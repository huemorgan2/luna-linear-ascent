import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from simulation.game_results import simulate

def diff(a,b,path=''):
 if type(a)!=type(b):return [(path,type(a).__name__,type(b).__name__)]
 if isinstance(a,dict):return sum([diff(a.get(k),b.get(k),path+'/'+k) for k in a.keys()|b.keys()],[])
 if isinstance(a,list):
  if len(a)!=len(b):return [(path+'/length',len(a),len(b))]
  return sum([diff(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))],[])
 return [] if a==b else [(path,a,b)]
if __name__=='__main__':
 cfg=dict(ruleset='collection-v1',players=2,days=1,max_floor=5,readiness_trials=2,minutes_per_day=2,policies=['planner','investor'],trace_players=2,readiness_policy='planner')
 a=simulate({**cfg,'workers':1});b=simulate({**cfg,'workers':0})
 out=dict(serial=a,parallel=b,differences=diff(a['players'],b['players']))
 Path(__file__).with_name('parity-diagnostic.json').write_text(json.dumps(out,separators=(',',':'))+'\n')
 print(json.dumps(out['differences'][:30],indent=2))
