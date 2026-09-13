"""Real-engine complementary contexts omitted by the one-family matrix."""
import argparse,json
from collections import Counter
from pathlib import Path
from prepared import prepare,act,at_time,state
from simulation.game_adapter import engine_source
from simulation.game_collection import fight
from plugin_linear_ascent.engine import bestiary,groups,collection
from plugin_linear_ascent.content import schema


def trial(seed,profile,family,mode):
    families=(family,'hawkeye') if family=='ramguard' else (family,)
    s,fixture=prepare(seed,profile['floor'],families,honed=True);p=s.doc;iid=p['deck'][0]
    if family=='frostbind':
        p['gear']['shoes']=None
        fixture['gear']=dict(p['gear'])
    if family=='runestring':
        p['quiver'][fixture['grade']]['arcane']=40
    with at_time(s.seconds):
        members=[bestiary.rolled_member(p,profile['floor'],profile['id'],opening=True) for _ in range(2)]
        for m in members:m['gap']=0 if family in ('ramguard','skirmisher','breach') else 3
        groups.open_group(p,members=members)
    s.look();initial=p['hp'];actions=0;events=Counter();outcome='limit'
    if family=='runestring' and mode=='niche':act(s,'load_arrow:'+iid+':arcane')
    for _ in range(100):
        if not p.get('group'):
            outcome='win' if p['group_result']['won'] else 'loss';break
        opts={o.id for o in s.legal()};m=groups.current(p);skill='skill:'+iid;strike='strike:'+iid
        if family=='ramguard':
            if mode=='niche' and m['gap']==0 and skill in opts:oid=skill
            else:
                oid=fight(s,'tactician',probe=True)
                if mode=='plain' and oid==skill:oid=strike
        elif family=='frostbind' and mode=='niche' and skill in opts:oid=skill
        elif strike in opts:oid=strike
        elif 'approach' in opts and not m['air']:oid='approach'
        else:oid='flee'
        act(s,oid);actions+=1
        for e in (p.get('group') or p.get('group_result') or {}).get('events',[]):events[e['kind']]+=1
    return dict(seed=seed,family=family,mode=mode,creature=profile['id'],type=profile['type'],fixture=fixture,
        outcome=outcome,actions=actions,hp_lost=max(0,initial-p['hp']),events=dict(events),quiver=p['quiver'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=16);ap.add_argument('--out',required=True);args=ap.parse_args()
    source=engine_source();profiles=[bestiary.profile(f,e.id) for f in range(1,101) for e in schema.get_floor(f).encounters]
    cases={
        'ramguard':[p for p in profiles if not p['air'] and p['affinity']=='Magic' and 'steadfast' not in p['traits']],
        'frostbind':[p for p in profiles if p['air']],
        'runestring':[p for p in profiles if p['affinity']=='Power'],
    }
    rows=[];summary={}
    for family,available in cases.items():
        selected={}
        for anchor in (12,30,55,80):
            for air in (False,True):
                matching=[p for p in available if p['air']==air]
                if matching:
                    p=min(matching,key=lambda p:(abs(p['floor']-anchor),p['id']));selected[p['id']]=p
        sample=[trial(seed,p,family,mode) for p in selected.values() for seed in range(args.seeds) for mode in ('plain','niche')]
        rows+=sample;better=[];worse=[]
        for a,b in zip(sample[::2],sample[1::2]):
            if (b['outcome']=='win' and a['outcome']!='win') or (a['outcome']==b['outcome']=='win' and (b['hp_lost']<a['hp_lost'] or b['actions']<a['actions'])):better.append(b['creature'])
            if b['outcome']!='win' and a['outcome']=='win':worse.append(b['creature'])
        summary[family]=dict(trials=len(sample),improved=len(better),improved_creatures=dict(Counter(better)),lost_wins=len(worse),lost_creatures=dict(Counter(worse)),plain_wins=sum(r['outcome']=='win' for r in sample if r['mode']=='plain'),niche_wins=sum(r['outcome']=='win' for r in sample if r['mode']=='niche'))
    if engine_source()['sha256']!=source['sha256']:raise RuntimeError('Source changed')
    Path(args.out).write_text(json.dumps(dict(engine_source=source,summary=summary,trials=rows),separators=(',',':'))+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
