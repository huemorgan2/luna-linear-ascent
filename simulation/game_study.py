#!/usr/bin/env python3
"""Repeat an actual-engine cohort on several seeds; every run is saved."""
from pathlib import Path
import argparse
import json
import statistics
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from simulation.game_agents import GameConfig
from simulation.game_results import simulate,save


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--players',type=int,default=12);parser.add_argument('--days',type=int,default=30)
    parser.add_argument('--seeds',default='1601,1602,1603');parser.add_argument('--workers',type=int,default=0)
    a=parser.parse_args()
    seeds=[int(s) for s in a.seeds.split(',')]
    if not 1<=len(seeds)<=12 or len(set(seeds))!=len(seeds):parser.error('Choose 1–12 distinct seeds')
    for seed in seeds:
        cfg=GameConfig.from_dict(dict(players=a.players,days=a.days,seed=seed,workers=a.workers))
        print(f'Actual engine / seed {seed}',flush=True)
        data=simulate(cfg,lambda e:print(f"  {e['completed']}/{e['total']} players",flush=True))
        path=save(data)
        print(json.dumps(dict(file=str(path),seed=seed,seconds=data['duration_seconds'],
            median_floor=statistics.median(p['ready_floor'] for p in data['players']),max_floor=max(p['ready_floor'] for p in data['players'])),indent=2),flush=True)


if __name__=='__main__':main()
