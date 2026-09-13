"""Prepared floor3 material-return experiment through actual core actions.

Explicit fixtures, not natural progression. Same starter deck/training and
20 energy, one finite trip budget; no regen wait, free healing or upgrades.
Run: ASCENT_GAME_PATH=... python simulation/verification/007/gathering_probe.py
"""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.game_adapter import GameSession,at_time,engine_source
from simulation.game_agents import create_character
from simulation.game_collection import fight
from plugin_linear_ascent.engine import state


def trial(seed,mode):
    s=create_character('prepared-route-'+str(seed),capture=False,ruleset='collection-v1')
    p=s.doc
    p.update(level=3,hp=95,gold=300,floor=3,location='gate_town',unlocked_floor=3,
             training=dict(blade=3,bow=3,staff=3),energy_val=20)
    with at_time(s.seconds):p['hp']=state.max_hp(p)
    s.look();counts=Counter();start_gold=p['gold'];actions=0;stopped=False
    site={'wood':'drowned-copse','metal':'bog-iron-field'}.get(mode)
    def act(oid):
        nonlocal actions,stopped
        r=s.act(oid,seconds=s.seconds+6);actions+=1
        if r.refusal:raise RuntimeError((mode,seed,oid,r.refusal))
        for e in s.events:
            counts[e['kind']]+=1
            if e['kind']=='enemy_start' and e['note'].endswith(':paid'):counts['energy_paid']+=1
            if e['kind']=='gather':counts['energy_paid']+=1
            if e['kind']=='death':stopped=True
    for _ in range(500):
        if p.get('group'):
            act(fight(s,'tactician'));continue
        if p.get('group_result'):act('group_return');continue
        with at_time(s.seconds):en=state.energy_now(p);low=p['hp']<state.max_hp(p)*.5
        if p.get('expedition'):
            if stopped or en<3 or low or p['expedition']['attempts']>=6:act('gather_extract')
            else:act('gather_step')
            continue
        if stopped or en<3 or low:break
        if mode=='hunt':act('hunt');continue
        if p['location']=='gate_town':act('gather_site:'+site);continue
        if 'gather_tool' in {o.id for o in s.legal()}:act('gather_tool');continue
        act('gather_begin')
    else:raise RuntimeError(('action bound',mode,seed))
    return dict(seed=seed,mode=mode,actions=actions,active_minutes=actions/10,
        energy_paid=counts['energy_paid'],materials=dict(p['materials']),
        net_gold=p['gold']-start_gold,xp=state.xp_total(p),counters=dict(counts))


def main():
    rows=[trial(seed,mode) for seed in range(64) for mode in ('hunt','wood','metal')]
    summary={}
    for mode in ('hunt','wood','metal'):
        sample=[r for r in rows if r['mode']==mode];energy=sum(r['energy_paid'] for r in sample)
        totals={name:sum(r['materials'].get(name,0) for r in sample) for name in ('Wood','Raw Metal')}
        summary[mode]=dict(trials=len(sample),energy_paid=energy,secured_materials=totals,
            units_per_energy={k:v/energy for k,v in totals.items()},mean_net_gold=sum(r['net_gold'] for r in sample)/len(sample),
            mean_active_minutes=sum(r['active_minutes'] for r in sample)/len(sample),deaths=sum(r['counters'].get('death',0) for r in sample))
    for mode,target in [('wood','Wood'),('metal','Raw Metal')]:
        summary[mode]['target_return_vs_hunt']=summary[mode]['units_per_energy'][target]/summary['hunt']['units_per_energy'][target]
    result=dict(engine_source=engine_source(),fixture='Floor3, level3, authored three +0 starters, ranks3, fullHP,20energy,300gold; tools bought with fixturegold; no healing or upgrades',summary=summary,trials=rows)
    out=Path('/private/tmp/ascent-phase3-gathering-returns.json');out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(summary,indent=2));print(out)
if __name__=='__main__':main()
