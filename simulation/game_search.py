#!/usr/bin/env python3
"""Search legal player strategies, then check finalists on untouched seeds."""
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
from pathlib import Path
import argparse
import json
import multiprocessing
import platform
import statistics
import sys
import time
import uuid
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from simulation.game_agents import GameConfig
from simulation.game_results import simulate, save, available_cpus, engine_source, host_hash, ROOT

SEARCHES=ROOT/'game-searches'


def candidates():
    return [dict(id=f'{path}-{growth}-margin{margin}',planner_path=path,planner_growth=growth,planner_margin=margin)
            for path,growth,margin in product(('blade','bow','staff'),('levels','training'),range(3))]


def measure(run):
    """All players count, including those who never qualify for later floors."""
    players=run['players'];days=run['config']['days']
    return dict(players=len(players),days=days,
        mean_floor=statistics.mean(p['ready_floor'] for p in players),
        median_floor=statistics.median(p['ready_floor'] for p in players),
        floor_days=statistics.mean(sum(max(0,days-m['day']) for m in p['milestones']) for p in players),
        deaths=sum(p['counters'].get('death',0) for p in players),
        refused_actions=sum(p['counters'].get('refused_actions',0) for p in players),
        decision_loops=sum(p['bottlenecks'].get('decision_loop',0)+p['bottlenecks'].get('refusal_loop',0) for p in players),
        floors={str(f['floor']):dict(reached=f['reached'],population_median=f['population_median'],
            fastest=min((m['day'] for p in players for m in p['milestones'] if m['floor']==f['floor']),default=None)) for f in run['floors']})


def run_trial(task):
    cfg=GameConfig.from_dict(task['config']);run=simulate(cfg);path=save(run)
    return dict(candidate=task['candidate'],stage=task['stage'],seed=cfg.seed,config=cfg.to_dict(),
        run_id=run['run_id'],file=path.name,metrics=measure(run),
        engine_sha256=run['engine_source']['sha256'],runner_sha256=run['runner_sha256'],
        deterministic_sha256=run['deterministic_sha256'],seconds=run['duration_seconds'])


def rank(trials):
    groups={}
    for trial in trials:groups.setdefault(trial['candidate'],[]).append(trial)
    rows=[]
    for name,group in groups.items():
        n=sum(t['metrics']['players'] for t in group)
        weighted=lambda key:sum(t['metrics'][key]*t['metrics']['players'] for t in group)/n
        rows.append(dict(candidate=name,mean_floor=weighted('mean_floor'),floor_days=weighted('floor_days'),
            seed_median_floors=[t['metrics']['median_floor'] for t in sorted(group,key=lambda t:t['seed'])]))
    return sorted(rows,key=lambda r:(-r['mean_floor'],-r['floor_days'],r['candidate']))


def write_report(report,directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    path=directory/(report['search_id']+'.json');tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');tmp.replace(path)
    return path


def batch(tasks,workers,on_result):
    """One process per trial, one player at a time inside it; no nested pools."""
    workers=min(workers or available_cpus(),len(tasks));pools=[]
    if workers==1:
        for task in tasks:on_result(run_trial(task))
        return
    chunk=61 if platform.system()=='Windows' else workers
    try:
        for n in range(0,workers,chunk):
            pools.append(ProcessPoolExecutor(max_workers=min(chunk,workers-n),mp_context=multiprocessing.get_context('spawn')))
        futures={pools[(i%workers)//chunk].submit(run_trial,t):t for i,t in enumerate(tasks)}
        for future in as_completed(futures):on_result(future.result())
    finally:
        for pool in pools:pool.shutdown(wait=True,cancel_futures=True)


def search(*,screen_players=3,screen_days=7,training_seeds=(1701,1702),validation_players=6,
           validation_days=30,validation_seeds=(1801,1802,1803),finalists=3,workers=0,directory=SEARCHES,grid=None,progress=print):
    if set(training_seeds)&set(validation_seeds):raise ValueError('Training and validation seeds must be disjoint')
    if not training_seeds or not validation_seeds or len(set(training_seeds))!=len(training_seeds) or len(set(validation_seeds))!=len(validation_seeds):raise ValueError('Each stage needs distinct seeds')
    if type(workers) is not int or not 0<=workers<=4096:raise ValueError('workers must be 0–4096')
    grid=candidates() if grid is None else grid
    if not 1<=finalists<=len(grid):raise ValueError('Invalid finalist count')
    for n,d in ((screen_players,screen_days),(validation_players,validation_days)):
        GameConfig.from_dict(dict(players=n,days=d))
    start=time.perf_counter()
    report=dict(schema_version=1,search_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8],
        created_at=datetime.now(timezone.utc).isoformat(),status='screening',engine_source=engine_source(),runner_sha256=host_hash(),
        settings=dict(screen_players=screen_players,screen_days=screen_days,training_seeds=list(training_seeds),
            validation_players=validation_players,validation_days=validation_days,validation_seeds=list(validation_seeds),
            finalists=finalists,workers=workers or available_cpus()),candidates=grid,trials=[],ranking=[],validation=[],winner=None,
        ranking_rule='Highest mean qualified floor across all training players; ties use total days spent qualified for floors. Unreached players count. Validation never changes the selected winner.',
        limits='Bounded search, not a proven optimum. Synthetic attendance and staged frontier; no multiplayer waiting or field-sleep ambushes. Earliest players mix strategy and luck.')
    path=write_report(report,directory)
    def receive(trial):
        report['trials'].append(trial);report['trials'].sort(key=lambda t:(t['stage'],t['candidate'],t['seed']))
        report['seconds']=round(time.perf_counter()-start,3);write_report(report,directory)
        if trial['metrics']['refused_actions'] or trial['metrics']['decision_loops']:
            raise RuntimeError('Invalid decisions in saved trial '+trial['run_id']+'; fix before ranking')
        if progress:progress(f"{trial['stage']} / {trial['candidate']} / seed {trial['seed']}: median floor {trial['metrics']['median_floor']}")
    def task(profile,stage,seed,n,days,policy='planner',mode='improvements'):
        cfg=GameConfig.from_dict(dict(players=n,days=days,seed=seed,policies=[policy],probe_mode=mode,workers=1,trace_players=1,
            **{k:v for k,v in profile.items() if k.startswith('planner_')}))
        return dict(candidate=profile['id'],stage=stage,config=cfg.to_dict())
    try:
        jobs=[task(p,'training',seed,screen_players,screen_days) for p in grid for seed in training_seeds]
        batch(jobs,workers,receive)
        report['ranking']=rank(report['trials']);report['winner']=report['ranking'][0]['candidate']
        selected=[next(p for p in grid if p['id']==r['candidate']) for r in report['ranking'][:finalists]]
        report['status']='validation';write_report(report,directory)
        jobs=[task(p,'validation',seed,validation_players,validation_days) for p in selected for seed in validation_seeds]
        # Mage was the fastest historical strategy before this search. These
        # matched audit arms distinguish host observation changes from planning.
        for name,policy,mode in [('historical-mage','mage','session'),('corrected-mage','mage','improvements'),('corrected-learner','learner','improvements')]:
            jobs.extend(task(dict(id=name),'validation',seed,validation_players,validation_days,policy,mode) for seed in validation_seeds)
        batch(jobs,workers,receive)
        report['validation']=rank([t for t in report['trials'] if t['stage']=='validation'])
        report['status']='complete';report['seconds']=round(time.perf_counter()-start,3)
    except BaseException as e:
        report['status']='failed';report['error']=f'{type(e).__name__}: {e}';write_report(report,directory);raise
    write_report(report,directory)
    return report,path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key,default in [('screen-players',3),('screen-days',7),('validation-players',6),('validation-days',30),('finalists',3),('workers',0)]:p.add_argument('--'+key,type=int,default=default)
    p.add_argument('--training-seeds',default='1701,1702');p.add_argument('--validation-seeds',default='1801,1802,1803')
    a=vars(p.parse_args())
    for k in ('training_seeds','validation_seeds'):a[k]=tuple(int(x) for x in a[k].split(','))
    report,path=search(**a,progress=lambda message:print(message,flush=True));print(json.dumps(dict(report=str(path),winner=report['winner'],seconds=report['seconds']),indent=2))


if __name__=='__main__':main()
