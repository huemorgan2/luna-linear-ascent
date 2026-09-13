"""Decision policies only. The imported core validates and executes every action."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, asdict
import math
import random
import re

from .game_adapter import GameSession, at_time, combat, core, economy, schema, state, digest

POLICIES = {
 'learner':dict(name='Learner',color='#9cacae',path='blade',retreat=.15,description='Uses the lead weapon, favors visible attack power and buys levels first.'),
 'tactician':dict(name='Tactician',color='#63d5c2',path='blade',retreat=.3,description='Reads the game’s damage hints, learns counters and protects repair funds.'),
 'saver':dict(name='Saver',color='#e0c17a',path='blade',retreat=.35,description='Hunts one floor below capability, maintains gear and banks between sessions.'),
 'rusher':dict(name='Rusher',color='#ef907f',path='blade',retreat=0,description='Pushes the next accessible floor and deep hunts; prioritizes attack purchases.'),
 'archer':dict(name='Archer',color='#a9c783',path='bow',retreat=.25,description='Buys and trains bows, favors the engine’s treeline shot when available.'),
 'mage':dict(name='Mage',color='#c9a6ec',path='staff',retreat=.25,description='Buys and trains staves, uses the engine’s magic attacks and repairs.'),
 'planner':dict(name='Planner',color='#e8af70',path='staff',retreat=.25,description='Uses counters, carried healing, spare sales and sleep between visits; strategy settings are recorded in the run.'),
}

@dataclass
class GameConfig:
    ruleset:str="legacy"
    players:int=24
    days:int=30
    seed:int=1601
    workers:int=0
    max_floor:int=100
    minutes_per_day:float=30
    sessions_per_day:int=3
    attendance:float=.9
    action_seconds:float=6
    readiness_trials:int=8
    readiness_threshold:float=.8
    probe_every_days:int=1
    max_combat_actions:int=100
    trace_players:int=6
    world_frontier:int=0  # 0 = an explicitly staged readiness fixture
    probe_mode:str='improvements'
    planner_path:str='staff'
    planner_growth:str='levels'
    planner_margin:int=2
    policies:tuple=('learner','tactician','saver','archer','mage','planner')

    def to_dict(self):
        d=asdict(self);d['policies']=list(self.policies);return d

    @classmethod
    def from_dict(cls,values):
        if not isinstance(values,dict):raise ValueError('Settings must be an object')
        unknown=set(values)-set(cls.__dataclass_fields__)
        if unknown:raise ValueError('Not an engine-run setting: '+', '.join(sorted(unknown)))
        c=cls(**values)
        if c.ruleset not in ('legacy','collection-v1'):raise ValueError('Unknown game ruleset')
        if c.probe_mode not in ('session','improvements'):raise ValueError('probe_mode must be session or improvements')
        if c.planner_path not in ('blade','bow','staff'):raise ValueError('planner_path must be blade, bow or staff')
        if c.planner_growth not in ('levels','training'):raise ValueError('planner_growth must be levels or training')
        ints=dict(players=(1,100000),days=(1,3650),seed=(0,2147483647),workers=(0,4096),max_floor=(1,100),
            sessions_per_day=(1,12),readiness_trials=(2,32),probe_every_days=(1,30),max_combat_actions=(10,500),trace_players=(0,100),world_frontier=(0,100),planner_margin=(0,2))
        for k,(lo,hi) in ints.items():
            x=getattr(c,k)
            if type(x) is not int or not lo<=x<=hi:raise ValueError(f'{k} must be an integer {lo}–{hi}')
        for k,lo,hi in [('minutes_per_day',1,240),('attendance',.1,1),('action_seconds',1,60),('readiness_threshold',.5,1)]:
            x=getattr(c,k)
            if isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) or not lo<=x<=hi:raise ValueError(f'{k} must be {lo}–{hi}')
        if not isinstance(c.policies,(list,tuple)) or not c.policies or any(not isinstance(k,str) or k not in POLICIES for k in c.policies) or len(set(c.policies))!=len(c.policies):raise ValueError('Select distinct known strategies')
        c.policies=tuple(c.policies);return c


def create_character(key,capture=True,ruleset="legacy"):
    s=GameSession(key,capture=capture,ruleset=ruleset)
    while s.doc['stage']=='intro':s.act(s.legal()[0].id)
    s.act('human');s.act('', 'Simclimber')
    return s


def in_battle(p):
    return p.get('group') or p.get('encounter')


def fight_choice(session, policy, *, probe=False):
    if session.doc.get('group'):
        from .game_collection import fight
        return fight(session,policy,probe=probe)
    opts={o.id:o for o in session.legal()};p=session.doc
    if not probe and p['hp']<state.max_hp(p)*POLICIES[policy]['retreat'] and 'run' in opts:return 'run'
    if policy=='archer' and 'treeline_shot' in opts:return 'treeline_shot'
    attacks=[o for k,o in opts.items() if k=='attack' or k.startswith('attack_')]
    if attacks:
        if policy in ('learner','rusher'):return attacks[0].id
        def predicted(o):
            found=re.search(r'~([\d,]+)',o.hint)
            return int(found.group(1).replace(',','')) if found else 0
        return max(attacks,key=predicted).id
    if 'close_in' in opts:return 'close_in'
    return 'run' if 'run' in opts else next(iter(opts))


def assess(document,seconds,floor,cfg):
    """Disposable test setup; hunts and every resulting transition use core."""
    wins=0;failures=Counter();samples=[]
    for trial in range(cfg.readiness_trials):
        p=deepcopy(document)
        p.update(luna_user=f'probe:{cfg.seed}:{floor}:{trial}',encounter=None,location='gate_town',floor=floor,
            unlocked_floor=max(floor,p['unlocked_floor']),rng_counter=0,pending_events=[])
        for k in ('movie_floor','movie_beat','sleeping','kill_receipt','profile_view','foe_sheet','group','group_result','expedition','collection_view','workshop_view','quiver_view','hunt_offers'):p.pop(k,None)
        with at_time(seconds):
            p['hp']=state.max_hp(p);p['energy_val']=float(state.energy_cap_of(p));p['energy_ts']=state.now().isoformat()
        s=GameSession(p['luna_user'],seconds=seconds,document=p,capture=False);s.act('hunt')
        if s.scene.refusal:raise RuntimeError('Probe hunt refused: '+s.scene.refusal)
        enemy=deepcopy(in_battle(s.doc));won=False;outcome='action_limit'
        for action in range(cfg.max_combat_actions):
            if s.doc.get('group'):
                option=fight_choice(s,'tactician',probe=True)
            elif cfg.probe_mode=='improvements':
                from .game_planner import fight
                option=fight(s)[0]
            else:option=fight_choice(s,'tactician',probe=True)
            s.act(option)
            if s.scene.refusal:raise RuntimeError('Probe action refused: '+option+': '+s.scene.refusal)
            success='group_clear' if p.get('ruleset')=='collection-v1' else 'kill'
            if any(e['kind']==success for e in s.events):won=True;outcome='win';break
            if not in_battle(s.doc):
                outcome='death_or_retreat';break
        wins+=won;failures[outcome]+=1
        samples.append(dict(monster=' / '.join(m['name'] for m in enemy['members']) if enemy.get('members') else enemy['name'],type='group' if enemy.get('members') else enemy.get('profile',{}).get('type'),outcome=outcome,actions=action+1))
    return dict(win_rate=wins/cfg.readiness_trials,wins=wins,trials=cfg.readiness_trials,failures=dict(failures),samples=samples)


class Agent:
    def __init__(self,cfg,ident,policy):
        self.cfg,self.id,self.policy=cfg,ident,policy
        self.rng=random.Random(f'agent:{cfg.seed}:{ident}')
        self.s=create_character(f'simulation:{cfg.seed}:{ident}',ident<cfg.trace_players,cfg.ruleset)
        self.ready=0;self.milestones=[];self.floors={};self.counters=Counter();self.ledger=Counter();self.blocked=Counter()
        self.timeline=[];self.active=0.;self.actions=0;self.goal=None;self.queue=[];self.target=1;self.end=0;self.last_probe=None
        self.recent=[];self.attempt=None;self.probe_key=None;self.last_win=None
        self.route_history={};self.planner_notes=Counter();self.last_decision_reason='';self.probe_checks=0
        self.sync_frontier(cfg.world_frontier or 1)

    def sync_frontier(self,floor):
        self.s.world_frontier(min(self.cfg.max_floor,floor))

    def act(self,option):
        before=self.s.doc;enc=deepcopy(in_battle(before))
        self.s.act(option,seconds=self.s.seconds+self.cfg.action_seconds)
        self.active+=self.cfg.action_seconds/60;self.actions+=1
        self.counters['actions']+=1
        if self.s.scene.refusal:
            self.blocked[self.s.scene.refusal]+=1;self.counters['refused_actions']+=1
        for event in self.s.events:
            kind=event['kind'];self.counters[kind]+=1
            self.ledger[kind]+=event.get('gold',0)
            if kind in ('kill','group_clear','gather_extract'):
                self.counters['earned_gold']+=max(0,event.get('gold',0));self.counters['earned_xp']+=max(0,event.get('xp',0))
        current=in_battle(self.s.doc)
        if not enc and current:
            f=current['floor'];self.attempt=f
            self.floors.setdefault(f,dict(attempts=0,wins=0,kills=0,deaths=0,actions=0,gold=0,xp=0))['attempts']+=1
        if enc:
            f=enc['floor'];row=self.floors[f];row['actions']+=1
            row['kills']+=sum(e['kind']=='kill' for e in self.s.events)
            for event in self.s.events:
                if event['kind'] in ('kill','group_clear'):
                    row['gold']+=event.get('gold',0)
                    row['xp']+=event.get('xp',0)
            success='group_clear' if enc.get('members') else 'kill'
            if any(e['kind']==success for e in self.s.events):
                row['wins']+=1;self.last_win=True
            elif not current:
                row['deaths']+=int(any(e['kind']=='death' for e in self.s.events));self.last_win=False
            if not current:
                history=self.route_history.setdefault(f,[]);history.append(self.last_win);del history[:-12]
        if any(e['kind'] in ('buy','train','levelup','hone','repair','upgrade','craft') for e in self.s.events):
            self.route_history={}
        if self.last_decision_reason:self.planner_notes[self.last_decision_reason]+=1
        self.recent.append(dict(at=self.s.seconds,action=option,headline=self.s.scene.headline,refusal=self.s.scene.refusal))
        self.recent=self.recent[-30:]

    def goto(self,room):
        if self.cfg.ruleset=="collection-v1":
            from .game_collection import navigate
            return navigate(self,room)
        s=self.s;p=s.doc;opts={o.id for o in s.legal()}
        if p.get('movie_floor'):return 'skip'
        if p['location']==room:return None
        if room in opts:return room
        if 'town' in opts:return 'town'
        if 'back' in opts:return 'back'
        return next(iter(opts),None)

    def resources(self):
        p=self.s.doc
        reserve=0 if self.policy in ('rusher','learner') else .1*p['gold']
        return p['gold']-reserve,p['xp']

    def plan_purchase(self):
        p=self.s.doc;gold,xp=self.resources();front=p['unlocked_floor'];policy=self.policy
        # These are decision estimates from actual library prices; core is
        # still the only authority that can grant items or spend currencies.
        if p['level']<economy.LEVEL_CAP and xp>=economy.xp_need(p['level']) and p['gold']>=economy.levelup_gold(p['level']):return ('guildhall','guild_train')
        for slot in economy.DURABILITY_SLOTS:
            g=economy.FORGE.get(p['gear'].get(slot) or '')
            left=p.get('durability',{}).get(slot)
            if g and economy.wears(g) and left is not None and left<economy.item_pool(g)*(.1 if policy=='rusher' else .4):
                if p['inventory'].get('repair_token',0):return ('forge','token_'+slot)
                if p['gold']>=economy.repair_price(g,1-left/economy.item_pool(g)) and xp>=economy.hone_xp(front):return ('forge','repair_'+slot)
                self.blocked['repair_resources']+=1
        main=POLICIES[policy]['path'];line={'blade':'warrior','bow':'archer','staff':'sorcerer'}[main]
        held=set(combat._held_slugs(p));owned=held|set(p['inventory'])
        main_slug={'blade':'rusted_sword','bow':'basic_bow','staff':'worn_staff'}[main]
        if main!='blade' and not any(economy.FORGE[x].line==line for x in held):
            if main_slug not in owned and gold>=economy.BASIC_WEAPON_PRICE:return ('forge','buy_'+main_slug)
            if main_slug in p['inventory']:return ('forge','wear_'+main_slug)
        rank=p['training'][main];target=4 if p['level']<3 else 6 if p['level']<8 else 8
        if rank<target and xp>=economy.train_xp_cost(rank+1,core._school_discounted(p,main)) and gold>=economy.train_gold(rank+1,front):return ('school','train_'+main)
        if policy=='tactician':
            if p['slots']==1 and gold>=economy.CARRY2_GOLD and xp>=economy.CARRY2_XP:return ('school','buy_carry2')
            if p['slots']==2 and p['level']>=economy.CARRY3_LEVEL and gold>=economy.carry3_gold(front) and xp>=economy.CARRY3_XP:return ('school','buy_carry3')
            for path,slug in [('bow','basic_bow'),('staff','worn_staff')]:
                if len(held)<p['slots'] and slug not in owned and gold>=economy.BASIC_WEAPON_PRICE:return ('forge','buy_'+slug)
                if len(held)<p['slots'] and slug in p['inventory']:return ('forge','wear_'+slug)
                if slug in held and p['training'][path]<4:
                    nr=p['training'][path]+1
                    if gold>=economy.train_gold(nr,front) and xp>=economy.train_xp_cost(nr,core._school_discounted(p,path)):return ('school','train_'+path)
        offers=[]
        shop_options={o.id for o in core._forge_scene(p).options if not o.locked}
        if core._door_open(p,economy.ARCANUM_LEVEL):shop_options|={o.id for o in core._arcanum_scene(p).options if not o.locked}
        for g in economy.FORGE.values():
            if 'buy_'+g.slug not in shop_options:continue
            if g.price<=0 or g.price>gold or g.slug in owned or g.slot not in ('weapon','armor','shield','shoes'):continue
            if economy.rung_player_level_req(g)>p['level'] or economy.rung_floor_req(g)>front:continue
            if g.slot=='weapon' and g.line!=line:continue
            old=economy.FORGE.get(p['gear'].get(g.slot) or '')
            benefit=(g.speed-(old.speed if old else 0)) if g.slot=='shoes' else g.bonus-(old.bonus if old else 0)
            if benefit<=0:continue
            if not core.pack_can_take(p,g.slug):continue
            weight=2 if g.slot=='weapon' else 1.4 if g.slot=='armor' else 1
            if policy=='rusher' and g.slot=='weapon':weight=5
            offers.append((benefit*weight/g.price,g))
        if offers:
            g=max(offers,key=lambda row:row[0])[1]
            return ('arcanum' if g.line=='sorcerer' else 'forge','buy_'+g.slug)
        if policy!='rusher':
            for slot in economy.HONE_SLOTS:
                slug=p['gear'].get(slot)
                cap=min(economy.max_hone(front),p['level']//4) if p['level']<economy.LEVEL_CAP else economy.max_hone(front)
                if slug and state.hone_level(p,slot)<cap and gold>=economy.hone_price(front) and xp>=economy.hone_xp(front):return ('forge','hone_'+slot)
        return None

    def step(self):
        # Read the engine's current state before deciding. A death/receipt
        # scene may describe a room the player has already returned to.
        if not in_battle(self.s.doc):self.s.look()
        if self.cfg.ruleset=='collection-v1':
            from .game_collection import decide
            return decide(self)
        if self.policy=='planner':
            from .game_planner import decide
            return decide(self)
        p=self.s.doc
        if p.get('encounter'):return fight_choice(self.s,self.policy)
        if p.get('movie_floor'):return 'skip'
        if p.get('sleeping'):return 'wake'
        if self.goal:
            room,action=self.goal
            nav=self.goto(room)
            if nav:return nav
            self.goal=None
            if action in {o.id for o in self.s.legal()}:return action
            self.blocked['planned_option_unavailable']+=1
        p=self.s.doc
        if self.policy=='saver' and p['bank']>0:
            self.goal=('vault','withdraw_all');return self.goto('vault') or 'withdraw_all'
        purchase=self.plan_purchase()
        if purchase:
            self.goal=purchase
            nav=self.goto(purchase[0])
            if nav:return nav
            self.goal=None;return purchase[1]
        if state.energy_now(p)<(economy.COST_WILDS_DEEP if self.policy=='rusher' and self.target>=economy.DEEP_HUNT_MIN_FLOOR else economy.COST_WILDS_FIGHT):
            self.blocked['energy_wait']+=1;return None
        if p['hp']<state.max_hp(p)*(.2 if self.policy=='rusher' else .55):
            missing=state.max_hp(p)-p['hp']
            quote=economy.healer_tent_price(max(1,p['floor']),p['hp'],state.max_hp(p))
            if self.policy not in ('learner','rusher') and p['gold']>=economy.STEW_PRICE and (
                    p['gold']<quote or economy.STEW_PRICE/min(missing,economy.STEW_HEAL_HP)<quote/missing):
                if 'stew' in {o.id for o in self.s.legal()}:return 'stew'
                self.goal=('lodge','stew');return self.goto('lodge') or 'stew'
            if p['location']=='gate_town':
                price=economy.healer_tent_price(p['floor'],p['hp'],state.max_hp(p))
                if p['gold']>=price:return 'heal'
            if self.policy!='rusher':self.blocked['health_wait']+=1;return None
        if p['location']=='gate_town' and p['floor']==self.target:
            return 'hunt_deep' if self.policy=='rusher' and self.target>=economy.DEEP_HUNT_MIN_FLOOR else 'hunt'
        if p['location']=='gate':return f'floor_{self.target}'
        return self.goto('gate')

    def probe(self):
        if self.ready>=self.cfg.max_floor or self.s.doc.get('expedition'):return
        if self.cfg.ruleset=='collection-v1':
            from plugin_linear_ascent.engine import collection
            if collection.claims(self.s.doc):return
        # Recheck only on changes relevant to combat; exact condition and
        # quiver retained. A new day also changes the game's RNG day seed.
        p=self.s.doc
        signature=digest({k:p.get(k) for k in ('level','gear','hone','training','slots','held','durability','durability_pack','quiver','arrow_choice','mastery','collection','deck')})
        key=(int(self.s.seconds//86400),signature,self.ready)
        if key==self.probe_key:return
        self.probe_key=key
        while self.ready<self.cfg.max_floor:
            f=self.ready+1
            assessment=assess(p,self.s.seconds,f,self.cfg);self.last_probe=assessment;self.probe_checks+=1
            if assessment['win_rate']<self.cfg.readiness_threshold:break
            self.ready=f
            self.milestones.append(dict(floor=f,day=self.s.seconds/86400,active_minutes=self.active,assessment=assessment))
            if not self.cfg.world_frontier:self.sync_frontier(f+1)
            if self.cfg.probe_mode=='session':break
        if self.cfg.probe_mode=='improvements':self.probe_key=(key[0],signature,self.ready)

    def improvement_probe(self,option):
        if self.cfg.probe_mode!='improvements' or in_battle(self.s.doc):return
        if any(e['kind'] in ('buy','train','levelup','hone','repair','upgrade','craft','arrows') for e in self.s.events) or option.startswith(('wear_','unequip_','nock_')):
            self.probe()

    def run(self):
        for day in range(self.cfg.days):
            if self.rng.random()>self.cfg.attendance:continue
            for visit in range(self.cfg.sessions_per_day):
                start=day*86400+visit*(16*3600/max(1,self.cfg.sessions_per_day-1))
                self.s.look(max(start,self.s.seconds))
                self.end=self.s.seconds+self.cfg.minutes_per_day*60/self.cfg.sessions_per_day
                if day%self.cfg.probe_every_days==0 and not in_battle(self.s.doc):
                    self.probe()
                self.target=min(self.s.doc['unlocked_floor'],max(1,self.ready+int(self.policy=='rusher')-int(self.policy=='saver')))
                if self.cfg.ruleset=='collection-v1' and self.policy not in ('rusher','learner'):
                    self.target=max(1,self.target-1)
                guard=0;repeat=None;repeated=0
                while self.s.seconds+self.cfg.action_seconds<=self.end:
                    # Reserve actual action time for the planner's between-visit
                    # rest. The game still charges every navigation/sleep action.
                    if self.policy=='planner' and not in_battle(self.s.doc) and self.end-self.s.seconds<=6*self.cfg.action_seconds:break
                    with at_time(self.s.seconds):option=self.step()
                    if option is None:break
                    before=(self.s.doc['location'],option)
                    repeated=repeated+1 if before==repeat else 0;repeat=before
                    if repeated>self.cfg.max_combat_actions and not in_battle(self.s.doc):
                        self.blocked['decision_loop']+=1;break
                    self.act(option);guard+=1
                    self.improvement_probe(option)
                    if self.s.scene.refusal:
                        self.goal=None
                        if repeated>2:self.blocked['refusal_loop']+=1;break
                # No fabricated end-of-session heal. Sleep and bank use
                # ordinary game choices within the remaining activity budget.
                if (visit==self.cfg.sessions_per_day-1 or self.policy=='planner') and not in_battle(self.s.doc):
                    self.s.look()
                    sequence=['vault','deposit_all'] if self.policy=='saver' else []
                    sequence+=['sleep_menu','sleep_fields']
                    for action in sequence:
                        for _ in range(4):
                            if self.s.seconds+self.cfg.action_seconds>self.end:break
                            opts={o.id for o in self.s.legal()}
                            if action in opts:self.act(action);break
                            nav=self.goto('town')
                            if nav:self.act(nav)
                            else:break
            self.timeline.append(dict(day=day+1,ready_floor=self.ready,level=self.s.doc['level'],gold=self.s.doc['gold'],bank=self.s.doc['bank'],active_minutes=self.active,actions=self.actions))
        self.s.look(max(self.s.seconds,self.cfg.days*86400))
        if not in_battle(self.s.doc):self.probe()
        p=self.s.doc
        # Ledger transfers are kept signed for inspection. Wealth is recorded
        # separately because depositing gold does not destroy it.
        return dict(id=self.id,policy=self.policy,ready_floor=self.ready,milestones=self.milestones,floors=self.floors,
            active_minutes=self.active,counters=dict(self.counters),gold_ledger=dict(self.ledger),bottlenecks=dict(self.blocked),timeline=self.timeline,
            last_probe=self.last_probe,recent_actions=self.recent,probe_checks=self.probe_checks,planner_decisions=dict(self.planner_notes),final=p,state_sha256=self.s.state_hash(),
            trace=self.s.trace if self.s.capture else None,key=self.s.key)


def simulate_player(cfg,ident,policy):
    return Agent(GameConfig.from_dict(cfg),ident,policy).run()
