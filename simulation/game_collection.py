"""Decisions for the candidate game; no damage, rewards or settlement here."""
from plugin_linear_ascent.engine import collection,groups,gathering,workshop,quiver,battle_rules
from .game_adapter import state,economy,core


def fight(session,policy,*,probe=False):
    p=session.doc;m=groups.current(p);g=p['group']
    opts={o.id:o for o in session.legal()}
    if not probe and policy not in ('rusher','learner') and p['hp']<state.max_hp(p)*.2:
        if 'drink_tonic' in opts:return 'drink_tonic'
        return 'flee'
    strikes=[oid for oid in opts if oid.startswith('strike:')]
    if policy in ('learner','rusher'):
        return strikes[0] if strikes else 'approach' if not m['air'] else 'flee'
    def score(oid,arrow=None):
        item=p['collection'][oid.split(':')[1]];info=collection.stats(item)
        channel,factor=battle_rules.impact(collection.families()[item['family']],m['gap'],arrow)
        mult=battle_rules.affinity(m,channel,focus=info['path']=='staff' and bool(p.get('mastery',{}).get('staff')))
        return battle_rules.attack(p,item)*factor*mult
    choices=[]
    for oid in strikes:
        item=p['collection'][oid.split(':')[1]]
        if collection.stats(item)['path']=='bow' and g.get('combat_revision',1)>=2:
            arrow=quiver.definitions()[quiver.chosen(p,item)]
            choices.append((score(oid,arrow),oid))
        else:choices.append((score(oid),oid))
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid]
        if collection.stats(item)['path']!='bow' or item['durability']<=0:continue
        for arrow in quiver.definitions().values():
            action=f"load_arrow:{iid}:{arrow['id']}"
            if action in opts and arrow['id']!=quiver.chosen(p,item):
                choices.append((score('strike:'+iid,arrow),action))
    if not choices:return 'approach' if not m['air'] else 'flee'
    _,strike=max(choices,key=lambda row:row[0])
    if strike.startswith('load_arrow:'):return strike
    iid=strike.partition(':')[2];item=p['collection'][iid];skill='skill:'+iid
    if skill in opts:
        family=item['family']
        if family in ('ramguard','recoil','repulsor') and m['gap']==3:return strike
        if family=='viper' and 'venomproof' in m['traits']:return strike
        if family=='briar' and 'bloodless' in m['traits']:return strike
        return skill
    return strike


def navigate(agent,room):
    p=agent.s.doc;opts={o.id for o in agent.s.legal()}
    if p.get('group_result'):return 'group_return'
    if p.get('collection_view'):return 'collection_back'
    if p.get('workshop_view'):return 'shop_back'
    if p.get('quiver_view'):return None if room=='quiver' else 'arrow_back'
    if p.get('location')=='gathering':return 'gather_extract' if p.get('expedition') else 'gather_back'
    if p.get('movie_floor'):return 'skip'
    if p['location']==room:return None
    if room in opts:return room
    if 'town' in opts:return 'town'
    if 'back' in opts:return 'back'
    return next(iter(opts),None)


def purchase(agent):
    p=agent.s.doc;gold=p['gold'];xp=state.xp_total(p);front=p['unlocked_floor']
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid]
        if item['durability']<item['maximum']*.1:
            if gold>=workshop.repair_quote(item):return ('forge','mend:'+iid)
            if item['source']=='starter' and state.energy_now(p)>0:return ('forge','practice:'+iid)
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid]
        if collection.stats(item)['path']=='bow' and quiver.count(p,item['grade'],'ordinary')<10:
            q=quiver.quote(item['grade'],'ordinary')
            if quiver.used(p)+q['count']<=collection.catalog()['quiver']['capacity']:
                if gold>=q['gold']:return ('quiver','arrow_buy:'+item['grade']+':ordinary')
                if item['grade']=='Common' and state.energy_now(p)>1:return ('quiver','arrow_practice')
    # Modest training improves accuracy; both counters and a missed hit matter.
    paths=['blade'] if agent.policy in ('learner','rusher') else ['bow','staff','blade']
    for path in paths:
        rank=p['training'][path]
        if rank<3 and xp>=economy.train_xp_cost(rank+1,core._school_discounted(p,path)) and gold>=economy.train_gold(rank+1,front):
            return ('school','train_'+path)
    if p['level']<economy.LEVEL_CAP and xp>=economy.xp_need(p['level']) and gold>=economy.levelup_gold(p['level']):
        return ('guildhall','guild_train')
    upgrade=[]
    for iid in p['deck']:
        if not iid:continue
        q=collection.upgrade_quote(p['collection'][iid])
        if q and q['floor']<=front and gold>=q['gold']:
            upgrade.append((q['gold'],iid,q))
    for _,iid,q in sorted(upgrade):
        if all(p['materials'].get(k,0)>=v for k,v in q['materials'].items()):
            return ('forge','upgrade:'+iid)
    # Buy useful defense from the same visible legacy armor/shield racks.
    best=[]
    offers={o.id for o in core._forge_scene(p).options if not o.locked}
    for gear in economy.FORGE.values():
        if gear.slot not in ('armor','shield','shoes') or 'buy_'+gear.slug not in offers or not 0<gear.price<=gold:continue
        old=economy.FORGE.get(p['gear'].get(gear.slot) or '')
        benefit=(gear.speed-(old.speed if old else 0)) if gear.slot=='shoes' else gear.bonus-(old.bonus if old else 0)
        if benefit>0 and core.pack_can_take(p,gear.slug):best.append((benefit/gear.price,gear.slug))
    if best:return ('forge','buy_'+max(best)[1])
    if agent.policy not in ('learner','rusher'):
        for _,iid,q in sorted(upgrade):
            for key,site in gathering.SITES.items():
                name=site['material']
                if site['floor']<=front and name in q['materials'] and p['materials'].get(name,0)<q['materials'][name]:
                    tool=p.get('utility_tools',{}).get(site['tool'])
                    if tool or gold>=site['price']+q['gold']:
                        return ('gather',key)
    return None


def decide(agent):
    s=agent.s;p=s.doc
    if p.get('group'):return fight(s,agent.policy)
    if p.get('group_result'):return 'group_return'
    if p.get('movie_floor'):return 'skip'
    if p.get('sleeping'):return 'wake'
    if p.get('expedition'):
        exp=p['expedition'];site=gathering.SITES[exp['site']]
        tool=p['utility_tools'][site['tool']]
        if exp['attempts']>=6 or state.energy_now(p)<3 or p['hp']<state.max_hp(p)*.5 or not tool['condition']:
            return 'gather_extract'
        return 'gather_step'
    if collection.claims(p):
        iid=collection.claims(p)[0]
        if not collection.at_storage(p):return navigate(agent,'town')
        if not p.get('collection_view') or p.get('collection_selected')!=iid:return 'inspect:'+iid
        return 'store:'+iid
    if p.get('collection_view'):return 'collection_back'
    if p.get('workshop_view'):return 'shop_back'
    if p.get('quiver_view') and (purchase(agent) or ('',''))[0]!='quiver':return 'arrow_back'
    minimum_energy=1 if agent.policy in ('learner','rusher') else 3
    if state.energy_now(p)<minimum_energy:
        agent.blocked['energy_wait']+=1;return None
    if p['hp']<state.max_hp(p)*.6:
        missing=state.max_hp(p)-p['hp']
        quote=economy.healer_tent_price(max(1,p['floor']),p['hp'],state.max_hp(p))
        if p['location']=='gate_town' and p['gold']>=quote:return 'heal'
        if p['gold']>=economy.STEW_PRICE:
            return 'stew' if 'stew' in {o.id for o in s.legal()} else navigate(agent,'lodge')
        agent.blocked['health_wait']+=1;return None
    plan=purchase(agent)
    if plan:
        room,oid=plan
        if room=='quiver':
            if p.get('quiver_view'):return oid
            if p['location']=='forge':return 'quiver_shop'
            return navigate(agent,'forge')
        if room=='gather':
            site=gathering.SITES[oid]
            if p['location']=='gathering':
                if p.get('gathering_site')!=oid:return 'gather_back'
                tool=p.get('utility_tools',{}).get(site['tool'])
                if not tool:return 'gather_tool'
                if tool['condition']==0:return 'gather_mend'
                return 'gather_begin'
            if p['location']=='gate_town' and p['floor']==site['floor']:return 'gather_site:'+oid
            if p['location']=='gate':return 'floor_'+str(site['floor'])
            return navigate(agent,'gate')
        if p['location']==room:return oid
        return navigate(agent,room)
    if p['location']=='gathering':return 'gather_back'
    if p['location']=='gate_town' and p['floor']==agent.target:return 'hunt'
    if p['location']=='gate':return 'floor_'+str(agent.target)
    return navigate(agent,'gate')
