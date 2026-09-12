#!/usr/bin/env python3
"""Run a heuristic swarm offline. Example: python3 simulation/run.py --players 120 --days 365"""
from pathlib import Path
import argparse
import json
import sys
import statistics

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from simulation.model import Config
from simulation.results import save_run, simulate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path)
    p.add_argument("--players", type=int)
    p.add_argument("--days", type=int)
    p.add_argument("--seed", type=int)
    p.add_argument("--workers", type=int, help="CPU processes: 0 = available CPUs, 1 = serial, or an explicit count")
    p.add_argument("--max-floor", type=int)
    p.add_argument("--output-dir", type=Path)
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args()
    try:
        values = json.loads(a.config.read_text()) if a.config else {}
    except (OSError, ValueError) as error:
        p.error(str(error))
    if not isinstance(values, dict):
        p.error("Config must be a JSON object")
    for key in ("players", "days", "seed", "max_floor", "workers"):
        if getattr(a, key) is not None:
            values[key] = getattr(a, key)
    try:
        config = Config.from_dict(values)
    except ValueError as error:
        p.error(str(error))
    def progress(event):
        if not a.quiet and (event["completed"] % 10 == 0 or event["completed"] == event["total"]):
            print(f"{event['stage']}: {event['completed']}/{event['total']}", flush=True)
    data = simulate(config, progress)
    path = save_run(data, a.output_dir)
    print(json.dumps(dict(file=str(path), seconds=data["duration_seconds"],
        deterministic_sha256=data["deterministic_sha256"], players=config.players,
        workers=data["execution"]["workers"],
        median_floor=statistics.median(p["ready_floor"] for p in data["players"])), indent=2))


if __name__ == "__main__":
    main()
