#!/usr/bin/env python3
"""Bake the public wiki from the exact engine/content deployed by worldd.

Run from any directory: python worldd/tools/gen_wiki.py [--check].
Current species stats are never replaced with the research's toy profiles.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import sys

WORLD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORLD / 'vendor'))
from plugin_linear_ascent import economy, icons  # noqa: E402
from plugin_linear_ascent.content import schema  # noqa: E402
from plugin_linear_ascent.version import VERSION  # noqa: E402

OUT = WORLD / 'static/site/wiki'
ART = WORLD / 'vendor/plugin_linear_ascent/content/art'
# Authored draft exceptions, not random assignment or live type changes.
AIR_MAGIC = {'ledger_wisp', 'rod_wisp', 'cairn_wisp', 'bell_wisp', 'vigil_light',
             'charge_wisp', 'sac_light', 'mirage_wisp', 'pale_fire', 'chime_sprite',
             'charge_harpy', 'smoke_haunt', 'light_leak', 'pollen_shade',
             'banner_wraith', 'kings_shadow', 'arc_moth', 'mirror_moth'}
AIR_POWER = {'ash_wyrmling', 'road_wyrmling', 'nest_wyrmling', 'young_drake',
             'link_drake', 'column_drake', 'mast_drake', 'aerie_drake',
             'court_champion', 'wall_sentinel', 'rookery_warden_harpy'}
GRADES = [('Common',1,{12,13,22,23},1,'125'),
          ('Rare',26,{32,33,42,43},3,'47.5'),
          ('Epic',51,{52,53,62,63},8,'53.5'),
          ('Legendary',76,{82,83,92,93},20,'47.5')]

def asset(relative: str) -> str:
    path = ART / relative
    if not path.is_file():
        raise ValueError(f'Missing game art: {relative}')
    return f'/static/laart/{relative}?v={VERSION}'

def proposed_type(encounter) -> str:
    current = economy.type_of(encounter.traits)
    if current == 'fly':
        affinity = 'magic' if encounter.id in AIR_MAGIC else 'power' if encounter.id in AIR_POWER else 'common'
        return 'air-' + affinity
    return 'ground-' + {'armoured':'power','magic_resist':'magic','plain':'common'}[current]

def make_data() -> dict:
    floors, image_counts, ids = [], Counter(), set()
    for number in range(1, 101):
        floor = schema.get_floor(number)
        monsters = []
        weight = sum(e.weight for e in floor.encounters)
        for e in floor.encounters:
            if e.id in ids:
                raise ValueError(f'Duplicate creature identity: {e.id}')
            ids.add(e.id)
            relative = f'creatures/{e.id}_320x112.png'
            image_counts[hashlib.sha256((ART/relative).read_bytes()).hexdigest()] += 1
            atk, defense, hp = economy.creature_stats(number, e.traits)
            if 'bulwark' in e.traits:
                hp = round(hp * economy.BULWARK_HP_MULT)
            profile = economy.profile_from_traits(e.traits)
            bar = economy.creature_bar(number, e.traits)
            monsters.append(dict(id=e.id,name=e.name,kind=e.kind or 'creature',
                lore=e.lore or e.prose,traits=list(e.traits),image=asset(relative),
                currentType=profile['type'],speed=profile['speed'],hp=hp,atk=atk,
                defense=defense,bar=bar,spawn=round(e.weight/weight*100,2),
                gold=economy.gold_per_kill(bar),xp=economy.xp_per_kill(bar),
                proposedType=proposed_type(e),variantCount=1,
                deepEligible=number>=economy.DEEP_HUNT_MIN_FLOOR and not {'frail','feeble'}.intersection(e.traits),
                carrier='B' if profile['type']=='armoured' else 'A' if profile['type']=='fly' else 'mixed',
                specimenStats={k:dict(hp=round(hp*s['hp']),atk=round(atk*s['atk']),deepAtk=round(round(atk*s['atk'])*economy.DEEP_ATK_MULT)) for k,s in economy.SPECIMENS.items()}))
        floors.append(dict(floor=number,zone=floor.zone,biome=floor.biome,
            town=floor.gate_town,description=floor.arrival,monsters=monsters,
            deep=dict(unlocked=number>=economy.DEEP_HUNT_MIN_FLOOR,energy=economy.COST_WILDS_DEEP,atk=economy.DEEP_ATK_MULT,speed=economy.DEEP_SPEED_BONUS,reward=economy.deep_reward_mult(number)),
            specimens={k:{**v,'speed':economy.ALPHA_SPEED_BONUS if k=='alpha' else 0} for k,v in economy.specimen_table(number).items()},
            deepSpecimenWeights={k:v['weight'] for k,v in economy.DEEP_SPECIMENS.items()},
            warden=dict(name=floor.warden_name,hp=floor.warden_hp,
                        atk=floor.warden_atk,defense=floor.warden_def)))
    if max(image_counts.values()) > 3:
        raise ValueError('More than three creature identities share one image')
    if not AIR_MAGIC.union(AIR_POWER).issubset(ids):
        raise ValueError('Unknown draft flying species')
    upgrades=[]
    for gi,(name,start,skip,q0,coefficient) in enumerate(GRADES):
        q=0
        for level,gate in enumerate(f for f in range(start,start+25) if f not in skip):
            q=max(q+1,int((Decimal(q0)*Decimal('1.18')**level).__ceil__()))
            gold=200 if gi==0 and level==0 else int((Decimal(coefficient)*Decimal('1.3')**(gate-1)).__ceil__())
            upgrades.append(dict(grade=name,gi=gi,level=level,floor=gate,q=q,gold=gold,
                atk=economy.honed_bonus(economy._reference_bonus(gate,'weapon'),economy.reference_hone(gate)),
                dur=int((Decimal(1300)*(1+Decimal('.025')*(gate-1))).quantize(1,rounding=ROUND_HALF_UP))))
    model=json.loads((OUT/'model.json').read_text())
    for w in model['weapons']:
        w['image']=asset(f"weapons/large/{w['art']}_100x160.png") if (ART/f"weapons/large/{w['art']}_100x160.png").exists() else asset(f"weapons/icons/{w['art']}_30x48.png")
    keys=['weapon','sword','shield','armor','shoes','bow','staff','t_armor','t_resist',
          't_wing','t_speed','t_bulwark','t_wrench','heart','coin','aether','shard','pack','quiver',
          'flask','back','run','arrow_up','arrow_down','note','bolt','lock','focus']
    return dict(revision=model['revision'],gameVersion=VERSION,
        creatureCount=len(ids),uniqueImages=len(image_counts),maxImageReuse=max(image_counts.values()),
        floors=floors,upgrades=upgrades,icons={k:icons.icon_data_url(k) for k in keys},model=model)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    target=OUT/'data.json';text=json.dumps(make_data(),ensure_ascii=False,separators=(',',':'))+'\n'
    if args.check:
        if target.read_text()!=text:raise SystemExit('Wiki data is stale: run worldd/tools/gen_wiki.py')
        print('Wiki data is current')
    else:
        target.write_text(text);data=json.loads(text)
        print(f"Wiki: {data['creatureCount']} creatures, {data['uniqueImages']} unique images, 100 floors, 84 upgrade states")
if __name__=='__main__':main()
