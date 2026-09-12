#!/usr/bin/env python3
"""Paired multi-seed studies. Every member run is independently saved."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import json
import statistics
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from simulation.model import Config, ROOT, Rules
from simulation.results import simulate, save_run, code_hash, cohort_stats

TARGETS = {10:[7,14],25:[30,60],50:[90,180],100:[270,365]}
VARIANTS = {
    "original": dict(name="Original simulator",parent=None,changes=dict(model_revision="proposal-v1",decision_model="original",recovery_mode="none",repair_fraction=.2)),
    "audited": dict(name="Audited rules / original decisions",parent="original",changes=dict(model_revision="audited-v2",decision_model="original",recovery_mode="none",repair_fraction=.13)),
    "decisions": dict(name="Resource-aware / paid repairs",parent="audited",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="none",repair_fraction=.13)),
    "starter": dict(name="Retained basic recovery",parent="decisions",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="starter",repair_fraction=.13)),
    "partial": dict(name="Partial paid repair",parent="decisions",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="partial",repair_fraction=.13)),
    "repair": dict(name="Half repair price",parent="starter",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="starter",repair_fraction=.065)),
    "durability": dict(name="Double weapon endurance",parent="starter",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="starter",repair_fraction=.13,durability_scale=2)),
    "group": dict(name="Enemy HP ×0.75",parent="starter",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="starter",repair_fraction=.13,group_hp_scale=.75)),
    "healing": dict(name="Half healing price",parent="starter",changes=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="starter",repair_fraction=.13,heal_cost_scale=.5)),
}


def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def plan(base,seeds,variants):
    base=Config.from_dict(base).to_dict()
    if not isinstance(seeds,list) or not 1<=len(seeds)<=12 or any(type(s) is not int for s in seeds) or len(set(seeds))!=len(seeds):raise ValueError('Choose 1–12 distinct integer seeds')
    if not isinstance(variants,list) or not variants or any(not isinstance(v,str) for v in variants) or len(set(variants))!=len(variants) or any(v not in VARIANTS for v in variants):raise ValueError('Unknown or duplicate study variants')
    jobs=[]
    # These controlled anchors prevent hidden previous UI tweaks leaking into the matrix.
    anchors=dict(model_revision="audited-v2",decision_model="adaptive",recovery_mode="starter",repair_fraction=.13,
        durability_scale=1,heal_cost_scale=1,group_hp_scale=1)
    for variant in variants:
        for seed in seeds:
            cfg=Config.from_dict({**base,**anchors,**VARIANTS[variant]['changes'],"seed":seed}).to_dict()
            jobs.append(dict(variant=variant,seed=seed,config=cfg))
    return jobs


def summarize_study(study,runs):
    summaries={}
    for key in study['variants']:
        rows=[r for r in runs if r['experiment']['variant']==key]
        players=[p for r in rows for p in r['players']]
        if not rows:continue
        horizon=rows[0]['config']['days']
        seed_medians=[statistics.median(p['ready_floor'] for p in r['players']) for r in rows]
        costs={k:sum(p['counters'].get('spent_'+k,0) for p in players) for k in ('healing','repairs','training','equipment','upgrades','ammo')}
        income=sum(p['counters'].get('earned_gold',0) for p in players)
        target_stats={str(f):cohort_stats(players,f,horizon) for f in TARGETS if f<=rows[0]['config']['max_floor']}
        summaries[key]=dict(name=VARIANTS[key]['name'],parent=VARIANTS[key]['parent'],runs=len(rows),players=len(players),
            median_floor=statistics.median(p['ready_floor'] for p in players),max_floor=max(p['ready_floor'] for p in players),
            seed_median_range=[min(seed_medians),max(seed_medians)],target_floors=target_stats,
            policy_medians={policy:statistics.median(p['ready_floor'] for p in players if p['policy']==policy)
                for policy in rows[0]['config']['policies'] if any(p['policy']==policy for p in players)},
            broken_final=sum(all(w['condition']<=0 and w.get('source')!='recovery-starter' for w in p['final']['deck']) for p in players),
            costs=costs,hunting_income=income,upkeep_income_share=(costs['healing']+costs['repairs'])/income if income else None,
            seconds=sum(r['duration_seconds'] for r in rows))
        parent=VARIANTS[key]['parent']
        parent_rows={r['config']['seed']:r for r in runs if r['experiment']['variant']==parent}
        paired=[];times={str(f):[] for f in TARGETS}
        for r in rows:
            old=parent_rows.get(r['config']['seed'])
            if not old:continue
            old_by_id={p['id']:p for p in old['players']}
            for p in r['players']:
                q=old_by_id[p['id']];paired.append(p['ready_floor']-q['ready_floor'])
                for f in TARGETS:
                    newer=next((m['day'] for m in p['milestones'] if m['floor']==f),horizon)
                    older=next((m['day'] for m in q['milestones'] if m['floor']==f),horizon)
                    times[str(f)].append(older-newer)
        summaries[key]['paired']=dict(players=len(paired),mean_floor_gain=statistics.mean(paired) if paired else None,
            restricted_days_saved={f:statistics.mean(v) if v else None for f,v in times.items()})
    return dict(variants=summaries,targets={str(f):dict(min_days=low,max_days=high,status="provisional planning range") for f,(low,high) in TARGETS.items()},
        caveat="Equal allocations to six heuristics are an experimental cohort, not measured player demographics. Seed ranges are not confidence intervals. Restricted days saved caps unfinished players at the horizon; it is not an eventual-completion forecast.")


def run_study(base=None,seeds=None,variants=None,*,resume=None,directory=None,run_directory=None,progress=None):
    directory=Path(directory or ROOT/'studies');run_directory=Path(run_directory or ROOT/'runs')
    source=code_hash()
    input_hash=Rules().hash
    if resume:
        path=Path(resume);study=json.loads(path.read_text())
        if study.get('code_sha256')!=source:raise ValueError('Resume requires the same simulator source; start a new study for changed code')
        if study.get('input_sha256')!=input_hash:raise ValueError('Resume requires identical input data')
    else:
        seeds=seeds or [1601,1602,1603];variants=variants or list(VARIANTS)
        jobs=plan(base or dict(players=12,days=120),seeds,variants)
        ident=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
        path=directory/(ident+'.json')
        study=dict(study_id=ident,created_at=datetime.now(timezone.utc).isoformat(),code_sha256=source,input_sha256=input_hash,
            variants=variants,seeds=seeds,jobs=jobs,status='running',completed=[],analysis=None)
        atomic_json(path,study)
    runs=[]
    completed={(row['variant'],row['seed']):row for row in study['completed']}
    for index,job in enumerate(study['jobs']):
        existing=completed.get((job['variant'],job['seed']))
        if existing:
            run=json.loads((run_directory/(existing['run_id']+'.json')).read_text())
            if run['config']!=job['config'] or run['code_sha256']!=source:raise ValueError('Saved study run does not match its frozen config/source')
        else:
            def member_progress(event):
                if progress:progress(dict(stage=VARIANTS[job['variant']]['name']+' / '+event['stage'],
                    fraction=(index+event['fraction'])/len(study['jobs']),completed=index,total=len(study['jobs'])))
            try:
                run=simulate(job['config'],member_progress)
                if run['input_sha256']!=input_hash:raise ValueError('Input data changed during the study')
            except (Exception,KeyboardInterrupt) as error:
                study['status']='interrupted';study['error']=str(error) or type(error).__name__
                atomic_json(path,study);raise
            run['experiment']=dict(study_id=study['study_id'],variant=job['variant'],name=VARIANTS[job['variant']]['name'])
            save_run(run,run_directory)
            study['completed'].append(dict(variant=job['variant'],seed=job['seed'],run_id=run['run_id']))
        runs.append(run)
        study['analysis']=summarize_study(study,runs)
        atomic_json(path,study)
        if progress:progress(dict(stage=VARIANTS[job['variant']]['name'],fraction=(index+1)/len(study['jobs']),completed=index+1,total=len(study['jobs'])))
    study['status']='complete';atomic_json(path,study)
    return study,path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--players',type=int,default=12);p.add_argument('--days',type=int,default=120)
    p.add_argument('--seeds',default='1601,1602,1603');p.add_argument('--variants',default=','.join(VARIANTS))
    p.add_argument('--workers',type=int,default=0);p.add_argument('--resume',type=Path)
    a=p.parse_args()
    def progress(e):
        if e['fraction']==1 or e['completed'] and e['fraction']==e['completed']/e['total']:
            print(f"{e['completed']}/{e['total']} · {e['stage']}",flush=True)
    try:
        study,path=run_study(dict(players=a.players,days=a.days,workers=a.workers),[int(s) for s in a.seeds.split(',')],a.variants.split(','),resume=a.resume,progress=progress)
    except (ValueError,OSError) as error:p.error(str(error))
    print(json.dumps(dict(study=str(path),status=study['status'],completed=len(study['completed'])),indent=2))


if __name__=='__main__':main()
