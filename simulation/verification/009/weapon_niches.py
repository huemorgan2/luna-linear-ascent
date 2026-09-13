"""Compare actual techniques with strikes on prepared real creature groups."""
import argparse,json
from collections import Counter
from pathlib import Path
from prepared import prepare,act,at_time,state
from simulation.game_adapter import engine_source
from plugin_linear_ascent.engine import collection,bestiary,groups
from plugin_linear_ascent.content import schema


def trial(seed,profile,family,gap,techniques):
    floor=profile['floor'];s,fixture=prepare(seed,floor,(family,));p=s.doc;iid=p['deck'][0]
    with at_time(s.seconds):
        members=[bestiary.rolled_member(p,floor,profile['id'],opening=True) for _ in range(2)]
        for m in members:m['gap']=gap;m['arrival_gap']=gap
        groups.open_group(p,members=members)
    s.look();hp=p['hp'];actions=0;events=Counter();outcome='limit'
    for _ in range(100):
        if not p.get('group'):
            outcome='win' if p.get('group_result',{}).get('won') else 'loss';break
        opts={o.id for o in s.legal()};m=groups.current(p)
        skill='skill:'+iid;strike='strike:'+iid
        if techniques and skill in opts and not (family in ('ramguard','recoil','repulsor') and m['gap']==3):oid=skill
        elif strike in opts:oid=strike
        elif 'approach' in opts and not m['air']:oid='approach'
        else:oid='flee'
        act(s,oid);actions+=1
        for e in (p.get('group') or {}).get('events',[]):events[e['kind']]+=1
    return dict(seed=seed,creature=profile['id'],type=profile['type'],family=family,gap=gap,techniques=techniques,
        fixture=fixture,outcome=outcome,actions=actions,hp_lost=max(0,hp-p['hp']),events=dict(events),
        arrows_left=p['quiver'][fixture['grade']]['ordinary'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=8);ap.add_argument('--anchor',type=int,action='append');ap.add_argument('--family',choices=list(collection.families()));ap.add_argument('--out',required=True);args=ap.parse_args()
    source=engine_source();profiles=[bestiary.profile(f,e.id) for f in range(1,101) for e in schema.get_floor(f).encounters]
    cases={}
    for anchor in args.anchor or (3,30,55,80):
        for type_id in {p['type'] for p in profiles}:
            p=min((p for p in profiles if p['type']==type_id),key=lambda p:(abs(p['floor']-anchor),p['id']))
            cases[(p['floor'],p['id'])]=p
    rows=[];summary={}
    for family in collection.families():
        if args.family and family!=args.family:continue
        sample=[trial(seed,p,family,gap,skills) for p in cases.values() for gap in (0,3) for seed in range(args.seeds) for skills in (False,True)]
        rows+=sample;improved=[]
        for a,b in zip(sample[::2],sample[1::2]):
            if (b['outcome']=='win' and a['outcome']!='win') or (a['outcome']==b['outcome']=='win' and (b['hp_lost']<a['hp_lost'] or b['actions']<a['actions'])):
                improved.append(dict(creature=b['creature'],floor=b['fixture']['floor'],gap=b['gap'],seed=b['seed'],plain=dict(outcome=a['outcome'],hp_lost=a['hp_lost'],actions=a['actions']),technique=dict(outcome=b['outcome'],hp_lost=b['hp_lost'],actions=b['actions'])))
        summary[family]=dict(trials=len(sample),technique_improvements=len(improved),examples=improved[:8],
            plain_wins=sum(r['outcome']=='win' for r in sample if not r['techniques']),technique_wins=sum(r['outcome']=='win' for r in sample if r['techniques']))
        print(family,json.dumps({k:v for k,v in summary[family].items() if k!='examples'}),flush=True)
    if engine_source()['sha256']!=source['sha256']:raise RuntimeError('Source changed during experiment')
    Path(args.out).write_text(json.dumps(dict(engine_source=source,summary=summary,trials=rows),indent=2)+'\n')

if __name__=='__main__':main()
