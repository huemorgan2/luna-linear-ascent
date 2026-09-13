"""Matched real first actions expose passive force versus close-range niches."""
import json
from pathlib import Path
from prepared import prepare,act,at_time
from simulation.game_adapter import engine_source
from plugin_linear_ascent.engine import bestiary,groups
from plugin_linear_ascent.content import schema

def trial(seed,profile,family,gap):
 s,fixture=prepare(seed,profile['floor'],(family,),honed=True);p=s.doc;iid=p['deck'][0]
 with at_time(s.seconds):
  members=[bestiary.rolled_member(p,profile['floor'],profile['id'],opening=True) for _ in range(2)]
  for m in members:m['gap']=gap;m['arrival_gap']=gap
  groups.open_group(p,members=members)
 s.look();m=groups.current(p);before=m['hp'];hp=p['hp']
 act(s,'strike:'+iid)
 return dict(seed=seed,family=family,creature=profile['id'],type=profile['type'],gap=gap,fixture=fixture,
  damage=before-m['hp'],hp_lost=hp-p['hp'],events=p['group']['events'],durability=p['collection'][iid]['durability'])

source=engine_source();profiles=[bestiary.profile(f,e.id) for f in (12,30,55,80) for e in schema.get_floor(f).encounters]
rows=[]
for floor in (12,30,55,80):
 ground=[p for p in profiles if p['floor']==floor and not p['air']]
 if not ground:continue
 profile=min(ground,key=lambda p:p['id'])
 for seed in range(16):
  for family,gap in [('breach',0),('viper',0),('skirmisher',0),('hawkeye',0),('skirmisher',3),('hawkeye',3)]:
   rows.append(trial(seed,profile,family,gap))
summary={}
for name,a,b,gap in [('breach_contact','breach','viper',0),('skirmisher_contact','skirmisher','hawkeye',0),('hawkeye_cover','hawkeye','skirmisher',3)]:
 pairs=[(x,next(y for y in rows if y['seed']==x['seed'] and y['creature']==x['creature'] and y['gap']==gap and y['family']==b)) for x in rows if x['family']==a and x['gap']==gap]
 summary[name]=dict(pairs=len(pairs),stronger=sum(x['damage']>y['damage'] for x,y in pairs),equal=sum(x['damage']==y['damage'] for x,y in pairs),weaker=sum(x['damage']<y['damage'] for x,y in pairs),examples=[dict(creature=x['creature'],seed=x['seed'],first=x['damage'],second=y['damage']) for x,y in pairs if x['damage']>y['damage']][:4])
assert source['sha256']==engine_source()['sha256']
Path(__file__).with_name('passive-results.json').write_text(json.dumps(dict(engine_source=source,summary=summary,trials=rows),separators=(',',':'))+'\n')
print(json.dumps(summary,indent=2))
