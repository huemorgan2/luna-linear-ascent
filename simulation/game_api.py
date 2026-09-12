"""Local-only HTTP support for real-engine runs and synthetic play sessions."""
from collections import OrderedDict
from copy import deepcopy
import json
import threading
import uuid

from .game_adapter import engine_source,replay
from .game_agents import GameConfig,POLICIES,create_character
from .game_results import RUNS,simulate,save,validate


class GameAPI:
    def __init__(self,directory=None):
        self.directory=directory or RUNS
        self.sessions=OrderedDict();self.lock=threading.Lock();self.cache={}

    def defaults(self):return dict(config=GameConfig().to_dict(),policies=POLICIES,source=engine_source())

    def manifest(self):
        self.directory.mkdir(parents=True,exist_ok=True);rows=[];errors=[]
        for p in sorted(self.directory.glob('*.json'),reverse=True):
            stamp=(p.stat().st_mtime_ns,p.stat().st_size)
            if self.cache.get(p.name,(None,))[0]!=stamp:
                try:
                    data=validate(json.loads(p.read_text()))
                    item={k:data[k] for k in ('run_id','created_at','config','duration_seconds','engine_source','deterministic_sha256')}
                    item['engine_source']={k:v for k,v in item['engine_source'].items() if k!='files'}
                    self.cache[p.name]=(stamp,item,None)
                except (ValueError,KeyError,OSError) as e:self.cache[p.name]=(stamp,None,str(e))
            _,item,error=self.cache[p.name]
            if error:errors.append(p.name+': '+error)
            else:rows.append(item)
        return dict(runs=rows,errors=errors)

    def inspect(self,settings):
        if not isinstance(settings,dict):raise ValueError('Inspector settings must be an object')
        with self.lock:
            ident=settings.get('session')
            if ident:
                if ident not in self.sessions:raise ValueError('Session expired; create a new synthetic player')
                s=self.sessions[ident]
                if len(s.trace)>2000:raise ValueError('Inspector action limit reached; create a new player')
                wait=settings.get('wait_seconds',0)
                if type(wait) not in (int,float) or not 0<=wait<=604800:raise ValueError('Wait must be 0–604800 seconds')
                if wait:s.look(s.seconds+wait)
                else:
                    opt=settings.get('action')
                    legal={o.id for o in s.legal()}
                    if opt not in legal:raise ValueError('Choose an available engine action')
                    before=deepcopy(s.doc);old_scene=s.scene;old_seconds=s.seconds;old_trace=len(s.trace)
                    try:s.act(opt,seconds=s.seconds+6)
                    except Exception:
                        s.doc=before;s.scene=old_scene;s.seconds=old_seconds;del s.trace[old_trace:]
                        raise
            else:
                seed=settings.get('seed',1601)
                GameConfig.from_dict(dict(seed=seed))
                ident=uuid.uuid4().hex;s=create_character(f'inspector:{seed}');self.sessions[ident]=s
                while len(self.sessions)>24:self.sessions.popitem(last=False)
            # The receipt is kept separately; current_scene exposes the next
            # actual state, preventing stale death-card navigation choices.
            receipt=s.scene.to_dict();events=list(s.events)
            if not s.doc.get('encounter'):s.look()
            return dict(session=ident,scene=s.scene.to_dict(),receipt=receipt,events=events,seconds=s.seconds,
                state_sha256=s.state_hash(),rng_counter=s.doc['rng_counter'],trace_length=len(s.trace),
                player={k:s.doc.get(k) for k in ('level','gold','bank','gear','held','slots','training','durability','xp','floor','location')})

    def verify(self,ident,player_id):
        path=self.directory/(ident+'.json')
        if not path.is_file():raise ValueError('Run not found')
        data=validate(json.loads(path.read_text()))
        player=next((p for p in data['players'] if p['id']==player_id),None)
        if player is None or player['trace'] is None:raise ValueError('No complete trace for this player')
        _,report=replay(player['key'],player['trace'],expected_source=data['engine_source']['sha256'],expected_state=player['state_sha256'])
        return report
