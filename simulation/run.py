#!/usr/bin/env python3
"""Run bots through the actual game engine without its UI."""
from pathlib import Path
import argparse
import json
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path)
    for name in ('players','days','seed','workers','max-floor','trace-players','world-frontier'):p.add_argument('--'+name,type=int)
    p.add_argument('--output-dir',type=Path);p.add_argument('--quiet',action='store_true')
    p.add_argument('--replay',type=Path,help='Verify a recorded actual-engine run player against current engine source')
    p.add_argument('--player',type=int,default=0)
    a=p.parse_args()
    from simulation.game_agents import GameConfig
    from simulation.game_results import simulate,save
    try:
        if a.replay:
            from simulation.game_adapter import replay
            data=json.loads(a.replay.read_text());row=next(x for x in data['players'] if x['id']==a.player)
            if row['trace'] is None:raise ValueError('This player has no full trace; choose a recorded player')
            _,report=replay(row['key'],row['trace'],expected_source=data['engine_source']['sha256'],expected_state=row['state_sha256'])
            print(json.dumps(report,indent=2));sys.exit(0 if report['match'] else 1)
        values=json.loads(a.config.read_text()) if a.config else {}
        if not isinstance(values,dict):raise ValueError('Config must be an object')
        for key in ('players','days','seed','workers','max_floor','trace_players','world_frontier'):
            if getattr(a,key) is not None:values[key]=getattr(a,key)
        cfg=GameConfig.from_dict(values)
        def progress(event):
            if not a.quiet:print(f"{event['stage']}: {event['completed']}/{event['total']}",flush=True)
        data=simulate(cfg,progress);path=save(data,a.output_dir)
        print(json.dumps(dict(file=str(path),seconds=data['duration_seconds'],workers=data['execution']['workers'],
            engine=data['engine_source']['version'],engine_sha256=data['engine_source']['sha256'],
            deterministic_sha256=data['deterministic_sha256'],median_floor=statistics.median(x['ready_floor'] for x in data['players'])),indent=2))
    except (ValueError,OSError,KeyError,StopIteration) as error:p.error(str(error))


if __name__=='__main__':main()
