"""Versioned run artifacts and censoring-aware statistics."""
from __future__ import annotations

from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import platform
import statistics
import subprocess
import time
import uuid

from . import VERSION
from .bosses import evaluate_floor
from .model import Config, POLICIES, ROOT, Rules
from .swarm import simulate_player

_WORKER_RULES = None


def _init_worker(config):
    global _WORKER_RULES
    _WORKER_RULES = Rules(Config.from_dict(config))


def _run_worker(ident, policy):
    return simulate_player(_WORKER_RULES, ident, policy)


def _boss_worker(floor, members):
    return evaluate_floor(_WORKER_RULES, floor, members)


def available_cpus():
    if hasattr(os, "process_cpu_count"):
        return os.process_cpu_count() or 1
    if hasattr(os, "sched_getaffinity"):
        return len(os.sched_getaffinity(0)) or 1
    return os.cpu_count() or 1


class CpuPool:
    """One pool normally; Windows needs shards to exceed its 61-worker pool limit."""
    def __init__(self, workers, config):
        self.pools = []
        self.workers, self.cursor = workers, 0
        self.chunk = 61 if platform.system() == "Windows" else workers
        try:
            for start in range(0, workers, self.chunk):
                self.pools.append(ProcessPoolExecutor(max_workers=min(self.chunk, workers-start),
                    mp_context=multiprocessing.get_context("spawn"), initializer=_init_worker,
                    initargs=(config.to_dict(),)))
        except Exception:
            self.shutdown()
            raise

    def submit(self, fn, *args):
        pool = self.pools[(self.cursor % self.workers)//self.chunk]
        self.cursor += 1
        return pool.submit(fn, *args)

    def shutdown(self):
        for pool in self.pools:
            pool.shutdown(wait=True, cancel_futures=True)


def quantile(values, q):
    if not values:
        return None
    a = sorted(values)
    x = (len(a)-1)*q
    lo, hi = math.floor(x), math.ceil(x)
    return a[lo]+(a[hi]-a[lo])*(x-lo)


def cohort_stats(players, floor, horizon):
    members = [next((m for m in p["milestones"] if m["floor"] == floor), None) for p in players]
    reached = [m for m in members if m is not None]
    days = sorted(m["day"] for m in reached)
    n, k = len(players), len(days)
    # All non-completion observations are administrative right-censors at horizon.
    def population_percentile(q):
        index = max(0, math.ceil(n*q)-1)
        return days[index] if k > index else None
    return dict(players=n, reached=k, censored=n-k, reach_fraction=k/n if n else 0,
        mean_days=statistics.mean(days) if days else None,
        median_days=quantile(days, .5), p90_days=quantile(days, .9),
        population_median=population_percentile(.5) if n else None,
        population_p90=population_percentile(.9) if n else None,
        restricted_mean_days=(sum(days)+(n-k)*horizon)/n if n else None,
        mean_active_minutes=statistics.mean(m["active_minutes"] for m in reached) if reached else None,
        probe_win_rate=statistics.mean(m["assessment"]["win_rate"] for m in reached) if reached else None)


def aggregate(players, config):
    rows = []
    for f in range(1, config.max_floor+1):
        a = cohort_stats(players, f, config.days)
        totals = {k: sum(p["floors"].get(f, p["floors"].get(str(f), {})).get(k, 0) for p in players)
            for k in ("attempts", "wins", "kills", "deaths", "actions", "energy", "exhausted", "gold", "xp")}
        attempts = totals["attempts"]
        rows.append(dict(floor=f, **a, hunting=totals,
            hunt_win_rate=totals["wins"]/attempts if attempts else None,
            actions_per_hunt=totals["actions"]/attempts if attempts else None,
            policies={policy: cohort_stats([p for p in players if p["policy"] == policy], f, config.days) for policy in config.policies}))
    return rows


def code_hash():
    h = hashlib.sha256()
    for p in sorted(ROOT.glob("*.py")):
        h.update(p.name.encode()); h.update(p.read_bytes())
    return h.hexdigest()


def simulate(config, progress=None):
    config = Config.from_dict(config.to_dict() if isinstance(config, Config) else config)
    started = time.perf_counter()
    source_hash = code_hash()
    rules = Rules(config)
    players = [None]*config.players
    bosses = [None]*config.max_floor
    workers = min(config.workers or available_cpus(), max(config.players, config.max_floor))
    pool = None
    try:
        if workers > 1:
            # Spawn avoids inheriting web-server locks and works on Linux, macOS and Windows.
            pool = CpuPool(workers, config)
            futures = {pool.submit(_run_worker, i, config.policies[i % len(config.policies)]): i for i in range(config.players)}
            for n, future in enumerate(as_completed(futures), 1):
                players[futures[future]] = future.result()
                if progress:
                    progress(dict(stage="players", completed=n, total=config.players, fraction=.8*n/config.players))
        else:
            for i in range(config.players):
                policy = config.policies[i % len(config.policies)]
                players[i] = simulate_player(rules, i, policy)
                if progress:
                    progress(dict(stage="players", completed=i+1, total=config.players, fraction=.8*(i+1)/config.players))
        cohorts = [[] for _ in range(config.max_floor)]
        for player in players:
            for milestone in player["milestones"]:
                cohorts[milestone["floor"]-1].append(milestone)
        if pool:
            futures = {pool.submit(_boss_worker, f, cohorts[f-1]): f for f in range(1, config.max_floor+1)}
            for n, future in enumerate(as_completed(futures), 1):
                bosses[futures[future]-1] = future.result()
                if progress:
                    progress(dict(stage="wardens", completed=n, total=config.max_floor, fraction=.8+.2*n/config.max_floor))
        else:
            for f in range(1, config.max_floor+1):
                bosses[f-1] = evaluate_floor(rules, f, cohorts[f-1])
                if progress:
                    progress(dict(stage="wardens", completed=f, total=config.max_floor, fraction=.8+.2*f/config.max_floor))
    finally:
        if pool:
            pool.shutdown()
    floors = aggregate(players, config)
    if code_hash() != source_hash:
        raise RuntimeError("Simulator source changed during this run; restart with a stable checkout")
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.SubprocessError):
        commit = None
    # Execution-only settings must not change the seeded-result digest.
    payload = dict(config=config.to_dict(), players=players, floors=floors, wardens=bosses)
    semantic_payload = {**payload, "config": {k:v for k,v in config.to_dict().items() if k != "workers"}}
    deterministic_hash = hashlib.sha256(json.dumps(semantic_payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return dict(schema_version=1, simulator_version=VERSION,
        run_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex[:8],
        created_at=datetime.now(timezone.utc).isoformat(), duration_seconds=round(time.perf_counter()-started, 4),
        python_version=platform.python_version(), code_commit=commit, code_sha256=source_hash,
        execution=dict(workers=workers, available_cpus=available_cpus(), platform=platform.system(),
            architecture=platform.machine(), start_method="spawn" if workers > 1 else "serial"),
        input_sha256=rules.hash, source=rules.data["source"], deterministic_sha256=deterministic_hash,
        policy_definitions={k: POLICIES[k] for k in config.policies},
        assumptions={"ruleset":"deck/group proposal", "floor_access":"open tower; excludes shared-world gate waiting",
            "readiness":"full HP/energy, owned gear and ammo, fixed normal-group probes",
            "averages":"among reached players; censored players reported separately",
            "warden":"continuous healing; direct attacks only; finite HP/energy; no pledges",
            "details":"MODEL.md"}, **payload)


def validate_run(data):
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("Unsupported run format; expected schema_version 1")
    c = Config.from_dict(data.get("config", {}))
    if len(data.get("floors", [])) != c.max_floor or len(data.get("players", [])) != c.players:
        raise ValueError("Run counts do not match settings")
    if len(data.get("wardens", [])) != c.max_floor:
        raise ValueError("Missing warden results")
    return data


def save_run(data, directory=None):
    validate_run(data)
    directory = Path(directory or ROOT / "runs")
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (data["run_id"]+".json")
    # Unique filenames preserve earlier runs; atomic replace exposes only complete files.
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)+"\n")
    temporary.replace(target)
    return target
