"""Declared initial fixtures only; GameSession owns all subsequent transitions."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.game_agents import create_character
from simulation.game_adapter import at_time,core,economy,state
from plugin_linear_ascent.engine import collection


def prepare(seed,floor,families=('breach','hawkeye','ember'),gold=1000,*,honed=False):
    s=create_character(f'prepared-v2:{seed}:{floor}',capture=False,ruleset='collection-v1')
    p=s.doc
    p.update(level=max(3,min(30,floor-5)),floor=floor,unlocked_floor=floor,location='forge',
        gold=gold,energy_val=20,training=dict(blade=6,bow=6,staff=6),groups_cleared=1)
    grade=collection.GRADES[(floor-1)//25]
    level=max(n for n in range(21) if collection.floor_for(grade,n)<=floor)
    # A test setup, never an Agent action or natural progression result.
    for item in p['collection'].values():item['location']='storage'
    p['deck']=[None,None,None]
    for slot,family in enumerate(families):
        item=collection.mint(p,family,grade)
        item['level']=level;item['maximum']=collection.stats(item)['maximum'];item['durability']=item['maximum']
        collection.set_slot(p,slot,item['id'])
    offers={o.id for o in core._forge_scene(p).options if not o.locked}
    for slot in ('armor','shield','shoes'):
        allowed=[g for g in economy.FORGE.values() if g.slot==slot and 'buy_'+g.slug in offers]
        if allowed:
            gear=max(allowed,key=lambda g:g.speed if slot=='shoes' else g.bonus)
            p['gear'][slot]=gear.slug;p['durability'][slot]=economy.item_pool(gear)
    if honed:
        p['hone']['armor']=p['hone']['shield']=economy.reference_hone(floor)
    p['quiver']={grade:{'ordinary':100}}
    p['arrow_choice']={};p['location']='gate_town'
    with at_time(s.seconds):p['hp']=state.max_hp(p)
    s.look()
    return s,dict(floor=floor,level=p['level'],grade=grade,weapon_level=level,families=list(families),
        training=p['training'],gear=dict(p['gear']),hone=dict(p['hone']),hp=p['hp'],energy=20,gold=gold,ordinary_arrows=100)


def act(s,oid):
    scene=s.act(oid,seconds=s.seconds+6)
    if scene.refusal:raise RuntimeError(f'{oid}: {scene.refusal}')
    return scene
