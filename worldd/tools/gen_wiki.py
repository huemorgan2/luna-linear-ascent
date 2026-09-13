#!/usr/bin/env python3
"""Bake the wiki from the exact collection engine deployed by worldd."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys

WORLD=Path(__file__).resolve().parents[1]
GAME=Path(os.environ.get('ASCENT_GAME_PATH',WORLD/'vendor'))
sys.path.insert(0,str(GAME))
from plugin_linear_ascent import economy,icons
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import collection,bestiary,gathering,workshop,quiver,battle_rules
from plugin_linear_ascent.version import VERSION
import plugin_linear_ascent
OUT=WORLD/'static/site/wiki'
ART=Path(plugin_linear_ascent.__file__).parent/'content/art'


def asset(relative):
    path=ART/relative
    if not path.is_file():raise ValueError('Missing game art: '+relative)
    return f'/static/laart/{relative}?v={VERSION}'


def item(family,grade,level,source='craft'):
    value=dict(id='wiki',family=family,grade=grade,level=level,source=source)
    value['maximum']=value['durability']=collection.stats(value)['maximum']
    return value


def sources(family,grade):
    f=collection.families()[family];cfg=f['acquisition'][grade]
    out=dict(cfg=deepcopy(cfg),findFloor=collection.catalog()['loot']['legendaryDiscoveryFloor'] if grade=='Legendary' else 1)
    for source in ('shop','craft','drop'):
        owned=item(family,grade,cfg[source+'Level'],source)
        stats=collection.stats(owned)
        quote=workshop.acquisition_quote(family,grade,source) if source!='drop' else dict(gold=0,materials={},floor=collection.floor_for(grade,0))
        out[source]=dict(level=owned['level'],floor=quote['floor'],atk=stats['attack'],gold=quote['gold'],materials=quote['materials'])
        out[source+'Max']=stats['maximum']
        out[source+'Now']=math.ceil(stats['maximum']*cfg[source+'DurabilityPct']/100)
        out[source+'Gold']=quote['gold']
    out['craftQ']=out['craft']['materials'][collection.MATERIALS[collection.GRADES.index(grade)][0]]/f['recipe'][0]
    return out


def make_data():
    model=deepcopy(collection.catalog())
    model['revision']='collection-2'
    model['grades']=list(collection.GRADES)
    model['materials']=[list(x) for x in collection.MATERIALS]
    floors=[];images=Counter();ids=set()
    for number in range(1,101):
        floor=schema.get_floor(number);monsters=[]
        weight=sum(e.weight for e in floor.encounters)
        for e in floor.encounters:
            if e.id in ids:raise ValueError('Duplicate creature '+e.id)
            ids.add(e.id)
            base=deepcopy(bestiary.profile(number,e.id))
            relative=base['image'];images[hashlib.sha256((ART/relative).read_bytes()).hexdigest()]+=1
            base.update(image=asset(relative),kind=e.kind or 'creature',currentType=base['type'],
                proposedType=base['type'],variantCount=1,spawn=round(e.weight/weight*100,2),bar=number,
                gold=economy.gold_per_kill(number),xp=economy.xp_per_kill(number),
                deepEligible=number>=economy.DEEP_HUNT_MIN_FLOOR and not {'frail','feeble'}.intersection(e.traits),
                carrier='A' if base['air'] else 'B' if base['affinity']=='Magic' else 'mixed',
                familyWeights=bestiary.family_weights(base),bundles=bestiary.material_bundles(number,base),
                specimenStats={},lootByMode={})
            for specimen in economy.SPECIMENS:
                normal=bestiary.specimen_profile(base,specimen)
                deep=bestiary.specimen_profile(base,specimen,deep=True)
                base['specimenStats'][specimen]=dict(hp=normal['hp'],atk=normal['atk'],deepAtk=deep['atk'],speed=normal['speed'],deepSpeed=deep['speed'])
            for mode in ('normal','deep'):
                rows={}
                for specimen in economy.SPECIMENS:
                    eligible=mode=='normal' or base['deepEligible'] and specimen!='runt'
                    rates=bestiary.drop_rates(number,base['traits'],specimen=specimen,deep=mode=='deep')
                    material=[rates['material'][g] if eligible else 0 for g in collection.GRADES]
                    weapon=[rates['weapon'][g] if eligible else 0 for g in collection.GRADES]
                    species=math.prod(model['loot']['body'].get(t,model['loot']['bite'].get(t,1)) for t in base['traits'])
                    rows[specimen]=dict(eligible=eligible,material=material,weapon=weapon,none=100-sum(weapon),species=species,factor=species*model['loot']['specimen'][specimen])
                base['lootByMode'][mode]=rows
            monsters.append(base)
        floors.append(dict(floor=number,zone=floor.zone,biome=floor.biome,town=floor.gate_town,description=floor.arrival,
            monsters=monsters,groups=list(bestiary.size_range(number)),sites=[dict(id=k,**s) for k,s in gathering.sites_at(number).items()],
            deep=dict(unlocked=number>=economy.DEEP_HUNT_MIN_FLOOR,energy=1,atk=1.2,speed=1,reward=1.4),
            specimens={k:{**v,'speed':int(k=='alpha')} for k,v in economy.specimen_table(number).items()},
            deepSpecimenWeights={k:v['weight'] for k,v in economy.DEEP_SPECIMENS.items()},
            warden=dict(name=floor.warden_name,hp=floor.warden_hp,atk=floor.warden_atk,defense=floor.warden_def,model='legacy-comparison')))
    for floor in floors:
        group=floor['monsters'][:floor['groups'][0]]
        floor['groupExample']=dict(names=[m['name'] for m in group],specimen='common',
            material=[100*(1-math.prod(1-m['lootByMode']['normal']['common']['material'][i]/100 for m in group)) for i in range(4)],
            weapon=[100*(1-math.prod(1-m['lootByMode']['normal']['common']['weapon'][i]/100 for m in group)) for i in range(4)])
    if max(images.values())>3:raise ValueError('More than three identities share creature art')
    if not bestiary.AIR_MAGIC.union(bestiary.AIR_POWER).issubset(ids):raise ValueError('Unknown flying identity')
    weapon_images=set()
    for w in model['weapons']:
        w['images']={};w['sources']={};w['states']={}
        for grade,art in w['artByGrade'].items():
            relative=art['file'] if art['source']=='collection' else f"weapons/large/{art['slug']}_100x160.png"
            path=ART/relative;digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in weapon_images:raise ValueError(f"Reused weapon drawing: {w['id']}/{grade}")
            weapon_images.add(digest);w['images'][grade]=dict(src=asset(relative),description=art['description'])
            w['sources'][grade]=sources(w['id'],grade)
            states=[]
            for level in range(21):
                owned=item(w['id'],grade,level);stats=collection.stats(owned)
                charge=workshop.acquisition_quote(w['id'],grade,'craft') if level==0 else collection.upgrade_quote(item(w['id'],grade,level-1))
                states.append(dict(level=level,floor=stats['floor'],atk=stats['attack'],dur=stats['maximum'],gold=charge['gold'],materials=charge['materials']))
            w['states'][grade]=states
        w['hitExamples']={t['id']:{a['id']:[battle_rules.example_hit(w,t,a,gap) for gap in range(4)] for a in model['arrows']} for t in model['types']}
    upgrades=[]
    # Neutral reference anchors are explanatory; actual family charges above
    # come directly from Forge quotes, never this informational reference.
    for gi,grade in enumerate(collection.GRADES):
        for level in range(21):
            floor=collection.floor_for(grade,level)
            upgrades.append(dict(grade=grade,gi=gi,level=level,floor=floor,
                atk=economy.honed_bonus(economy._reference_bonus(floor,'weapon'),economy.reference_hone(floor)),
                dur=round(1300*(1+.025*(floor-1)))))
    shields=[]
    for name,raw,armor,shield,guard in [('Light gear',100,10,8,False),('Armored',100,50,20,False),('Strong shield',100,40,80,False),('Guard stance',100,40,40,True),('Huge incoming hit',300,40,80,False),('Almost unharmed',1,200,300,True)]:
        shields.append(dict(name=name,raw=raw,armorDef=armor,shieldDef=shield,guard=guard,**battle_rules.incoming(raw,armor,shield,guard=guard)))
    keys=list(collection.MATERIAL_ICONS.values())+['weapon','sword','shield','armor','shoes','bow','staff','t_armor','t_resist','t_wing','t_speed','t_bulwark','t_wrench','heart','coin','aether','shard','pack','quiver','flask','back','run','arrow_up','arrow_down','note','bolt','lock','focus']
    return dict(revision=model['revision'],gameVersion=VERSION,ruleset=collection.RULESET,
        creatureCount=len(ids),uniqueImages=len(images),maxImageReuse=max(images.values()),
        floors=floors,upgrades=upgrades,icons={k:icons.icon_data_url(k) for k in keys},model=model,
        sites=[dict(id=k,**s,image=asset(f'banners/{schema.get_floor(s["floor"]).banner}_320x112.png')) for k,s in gathering.SITES.items()],
        materialIcons=collection.MATERIAL_ICONS,arrowQuotes={g:{a:quiver.quote(g,a) for a in quiver.definitions()} for g in collection.GRADES},shieldExamples=shields)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    target=OUT/'data.json';data=make_data();text=json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n'
    if args.check:
        if target.read_text()!=text:raise SystemExit('Wiki data is stale: run worldd/tools/gen_wiki.py')
        print('Wiki data matches the game engine')
    else:
        target.write_text(text)
        print(f"Wiki: {data['creatureCount']} creatures,64 weapon drawings,8 resource sites,1344 weapon states")
if __name__=='__main__':main()
