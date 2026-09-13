"""Actual-engine matched prepared routes; never edits natural player state."""
import argparse,json
from collections import Counter
from pathlib import Path
from prepared import prepare,act,at_time,state,economy
from simulation.game_adapter import engine_source
from simulation.game_collection import fight
from plugin_linear_ascent.engine import gathering,collection


def trial(seed,key,mode,*,honed=False):
    site=gathering.SITES[key];floor=site['floor']
    gold=site['price']+round(100*economy.income_pillar(floor))
    s,fixture=prepare(seed,floor,gold=gold,honed=honed);p=s.doc;counts=Counter();actions=0;stopped=False
    def step(oid):
        nonlocal actions,stopped
        act(s,oid);actions+=1
        for e in s.events:
            counts[e['kind']]+=1
            if e['kind']=='gather' or (e['kind']=='enemy_start' and e['note'].endswith(':paid')):counts['energy_paid']+=1
            if e['kind']=='death':stopped=True
    for _ in range(500):
        if p.get('group'):step(fight(s,'tactician'));continue
        if p.get('group_result'):step('group_return');continue
        with at_time(s.seconds):energy=state.energy_now(p);low=p['hp']<state.max_hp(p)*.5
        if p.get('expedition'):
            step('gather_extract' if stopped or energy<3 or low or p['expedition']['attempts']>=6 else 'gather_step')
            continue
        if stopped or energy<3 or low or collection.claims(p):break
        if mode=='hunt':step('hunt');continue
        if p['location']=='gate_town':step('gather_site:'+key);continue
        if 'gather_tool' in {o.id for o in s.legal()}:step('gather_tool');continue
        step('gather_begin')
    else:raise RuntimeError(f'action bound: {key} {seed} {mode}')
    return dict(seed=seed,site=key,mode=mode,fixture=fixture,actions=actions,energy_paid=counts['energy_paid'],
        materials=dict(p['materials']),net_gold=p['gold']-gold,xp=state.xp_total(p),hp=p['hp'],counters=dict(counts),
        stop='death' if stopped else 'pending_claim' if collection.claims(p) else 'health' if low else 'energy')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seeds',type=int,default=32);ap.add_argument('--site',choices=list(gathering.SITES));ap.add_argument('--honed',action='store_true');ap.add_argument('--out',required=True);args=ap.parse_args()
    source=engine_source();rows=[];summary={}
    for key,site in gathering.SITES.items():
        if args.site and key!=args.site:continue
        sample=[trial(seed,key,mode,honed=args.honed) for seed in range(args.seeds) for mode in ('hunt','gather')];rows+=sample
        modes={}
        for mode in ('hunt','gather'):
            items=[r for r in sample if r['mode']==mode];energy=sum(r['energy_paid'] for r in items)
            target=sum(r['materials'].get(site['material'],0) for r in items)
            modes[mode]=dict(trials=len(items),energy_paid=energy,secured_target=target,units_per_energy=target/energy if energy else None,
                mean_net_gold=sum(r['net_gold'] for r in items)/len(items),deaths=sum(r['counters'].get('death',0) for r in items),
                mean_actions=sum(r['actions'] for r in items)/len(items),stops=dict(Counter(r['stop'] for r in items)))
        base=modes['hunt']['units_per_energy'];modes['ratio']=modes['gather']['units_per_energy']/base if base else None
        summary[key]=dict(floor=site['floor'],target=site['material'],**modes)
        print(key,json.dumps(summary[key]),flush=True)
    if engine_source()['sha256']!=source['sha256']:raise RuntimeError('Source changed during experiment')
    Path(args.out).write_text(json.dumps(dict(engine_source=source,seeds=args.seeds,defense_honed=args.honed,summary=summary,trials=rows),indent=2)+'\n')

if __name__=='__main__':main()
