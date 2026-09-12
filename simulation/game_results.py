"""Parallel execution and measurements around the real game adapter."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import multiprocessing
from pathlib import Path
import platform
import subprocess
import time
import uuid

from .game_adapter import REPO, digest, engine_source, economy, schema
from .game_agents import GameConfig, POLICIES, simulate_player
from .results import available_cpus, cohort_stats

ROOT=REPO/'simulation'
RUNS=ROOT/'game-runs'
_WORKER_CONFIG=None


def host_hash():
    return digest({p.name:p.read_text() for p in sorted(ROOT.glob('game_*.py'))})


_IMPORTED_HOST=host_hash()


def initialize(config,expected_source):
    global _WORKER_CONFIG
    if engine_source()['sha256']!=expected_source:raise RuntimeError('Engine source differs in worker')
    # The game's loader normally tolerates broken content; a measurement
    # should fail visibly instead of silently omitting a floor.
    for f in range(1,config['max_floor']+1):schema.get_floor(f)
    _WORKER_CONFIG=config


def worker(ident,policy):
    return simulate_player(_WORKER_CONFIG,ident,policy)


def simulate(config,progress=None):
    cfg=GameConfig.from_dict(config.to_dict() if isinstance(config,GameConfig) else config)
    start=time.perf_counter();source=engine_source();host=host_hash();workers=min(cfg.workers or available_cpus(),cfg.players)
    if host!=_IMPORTED_HOST:raise RuntimeError('Runner files changed after import; restart the simulator')
    players=[None]*cfg.players;pools=[]
    try:
        if workers>1:
            chunk=61 if platform.system()=='Windows' else workers
            for n in range(0,workers,chunk):
                pools.append(ProcessPoolExecutor(max_workers=min(chunk,workers-n),mp_context=multiprocessing.get_context('spawn'),
                    initializer=initialize,initargs=(cfg.to_dict(),source['sha256'])))
            futures={pools[(i%workers)//chunk].submit(worker,i,cfg.policies[i%len(cfg.policies)]):i for i in range(cfg.players)}
            for n,future in enumerate(as_completed(futures),1):
                players[futures[future]]=future.result()
                if progress:progress(dict(stage='actual engine players',completed=n,total=cfg.players,fraction=n/cfg.players))
        else:
            initialize(cfg.to_dict(),source['sha256'])
            for i in range(cfg.players):
                players[i]=worker(i,cfg.policies[i%len(cfg.policies)])
                if progress:progress(dict(stage='actual engine players',completed=i+1,total=cfg.players,fraction=(i+1)/cfg.players))
    finally:
        for pool in pools:pool.shutdown(wait=True,cancel_futures=True)
    floors=[]
    for f in range(1,cfg.max_floor+1):
        totals={k:sum(p['floors'].get(f,{}).get(k,0) for p in players) for k in ('attempts','wins','kills','deaths','actions','gold','xp')}
        # These are the ACTUAL library's warden parameters, not an invented
        # headcount model. Shared service victory remains explicitly absent.
        warden=dict(name=schema.get_floor(f).warden_name,shared_hp=economy.world_warden_hp(f,cfg.players),
            quorum=economy.milestone_quorum(f,cfg.players) if economy.is_milestone(f) else None,
            regen_fraction_per_hour=economy.world_warden_regen_hourly(f),required_players=None,
            status='Not measured: shared-world PostgreSQL services are not executed')
        floors.append(dict(floor=f,**cohort_stats(players,f,cfg.days),hunting=totals,
            policies={k:cohort_stats([p for p in players if p['policy']==k],f,cfg.days) for k in cfg.policies},warden=warden))
    if engine_source()['sha256']!=source['sha256'] or host_hash()!=host:raise RuntimeError('Engine or runner source changed during run; no mixed-source result saved')
    semantic=dict(config={k:v for k,v in cfg.to_dict().items() if k!='workers'},players=players,floors=floors)
    try:commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
    except (OSError,subprocess.SubprocessError):commit=None
    return dict(schema_version=2,backend='actual-game-engine',run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8],
        created_at=datetime.now(timezone.utc).isoformat(),duration_seconds=round(time.perf_counter()-start,4),config=cfg.to_dict(),
        engine_source=source,runner_sha256=host,code_commit=commit,deterministic_sha256=digest(semantic),
        execution=dict(workers=workers,available_cpus=available_cpus(),python=platform.python_version(),platform=platform.system()),
        policy_definitions={k:POLICIES[k] for k in cfg.policies},players=players,floors=floors,
        boundaries=dict(resolver='Actual imported core; no duplicated game math',
            world_access='Fixed frontier '+str(cfg.world_frontier) if cfg.world_frontier else 'External readiness fixture: open the next floor after qualifying. Shared-world waiting excluded.',
            probes='Disposable copies; owned gear/condition/training, restored HP/energy, test-floor access. No player rewards.',
            multiplayer='Worldd database services, social interactions and shared warden victory are not run. Required-party counts remain null.',
            mechanics='The imported game revision decides mechanics. Proposed groups, fixed three slots and material grades are not injected.',
            activity='Heuristic choices and scheduled attendance are experimental inputs, not real player demographics.',
            trace='Complete action/time/world-fixture inputs saved for the first trace_players players. Other players retain final state, summary and recent actions.'))


def validate(data):
    if data.get('schema_version')!=2 or data.get('backend')!='actual-game-engine':raise ValueError('Expected an actual-engine run')
    cfg=GameConfig.from_dict(data['config'])
    if len(data['players'])!=cfg.players or len(data['floors'])!=cfg.max_floor:raise ValueError('Run counts do not match config')
    return data


def save(data,directory=None):
    validate(data);root=Path(directory or RUNS);root.mkdir(parents=True,exist_ok=True)
    path=root/(data['run_id']+'.json');tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,separators=(',',':'),allow_nan=False)+'\n');tmp.replace(path);return path
