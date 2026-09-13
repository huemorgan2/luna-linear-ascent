"""Prepared choices from visible rules, prices and history; the core executes them.

No alternate attack is rolled and no hidden reward/RNG state enters a decision.
"""
from copy import deepcopy
import math
from .game_adapter import core,state,economy
from .game_collection import navigate
from plugin_linear_ascent.engine import collection,workshop,quiver,gathering,battle_rules,groups


def combat_choice(s,*,probe=False):
    p=s.doc;public=groups.public(p);m=public['members'][public['index']]
    opts={o.id for o in s.legal()};rules=collection.catalog()['effectRules']
    incoming=battle_rules.incoming(m['atk'],state.gear_bonus(p,'armor'),state.gear_bonus(p,'shield'))['hp']
    choices=[]
    def score(iid,skill,arrow):
        item=p['collection'][iid];family=collection.families()[item['family']];info=collection.stats(item)
        channel,factor=battle_rules.impact(family,m['gap'],arrow,skill=skill)
        amount=battle_rules.attack(p,item)*factor*(.5 if m.get('exhausted') else 1)
        mult=battle_rules.affinity(m,channel,focus=info['path']=='staff' and bool(p.get('mastery',{}).get('staff')))
        direct=battle_rules.hp_damage(amount,m['defense'],mult)
        value=min(m['hp'],direct)
        if direct>=m['hp']:return value+incoming # finishing prevents retaliation
        effects={family['technique'] if skill else '',arrow['status'] if arrow else ''}
        for kind in sorted(effects):
            rule=rules.get(kind)
            if not rule or rule.get('immunity') in m['traits']:continue
            if kind in ('poison','burn','bleed'):
                if any(e['kind']==kind and (kind=='bleed' or e['source']['id']==iid) for e in m['effects']):continue
                turns=min(rule['phases'],max(0,m['hp']/max(1,direct)-1))
                tick=battle_rules.hp_damage(amount*rule['rate'],0,battle_rules.affinity(m,rule['channel']),dot=True)
                value+=tick*turns*.7
            elif kind=='push' and m['gap']<3:value+=incoming*.9+direct*.25
            elif kind=='stun' and m['gap']<=1:value+=incoming*.6
            elif kind=='slow' and not m.get('slow_phases') and m['gap']>0 and m['speed']>=economy.player_speed(p):value+=incoming*.45
            elif kind=='expose':value+=m['defense']*.35*(1-rule['defense'])*1.5
        return value
    for oid in sorted(opts):
        if not oid.startswith(('strike:','skill:')):continue
        iid=oid.split(':')[1];item=p['collection'][iid]
        arrow=quiver.definitions()[quiver.chosen(p,item)] if collection.stats(item)['path']=='bow' else None
        choices.append((score(iid,oid.startswith('skill:'),arrow),oid))
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid]
        if collection.stats(item)['path']!='bow' or item['durability']<=0:continue
        for arrow in quiver.definitions().values():
            oid=f"load_arrow:{iid}:{arrow['id']}"
            if oid in opts and arrow['id']!=quiver.chosen(p,item):
                choices.append((score(iid,False,arrow)*.99,oid))
    if not choices:return 'approach' if not m['air'] and 'approach' in opts else 'flee'
    value,oid=max(choices)
    if not probe and p['hp']<incoming*1.25 and value<m['hp'] and m['gap']<=1:
        if 'drink_tonic' in opts:return 'drink_tonic'
        return 'flee'
    return oid


def travel(a,room,action,reason):
    a.last_decision_reason=reason
    return navigate(a,room) or action


def affordable(p,q,gold=None):
    return p['unlocked_floor']>=q['floor'] and (p['gold'] if gold is None else gold)>=q['gold'] and all(p['materials'].get(k,0)>=v for k,v in q['materials'].items())


def families(a):
    return a.cfg.collection_deck


def preferred(a,item):
    path=collection.stats(item)['path']
    return (1.8 if path==a.cfg.planner_path else .7)*(1.08 if item['family'] in families(a) else 1)


def prepare_owned(a):
    """Inspect/set/store actual instances; never replace the document directly."""
    p=a.s.doc
    desired=[]
    for family in families(a):
        path=collection.families()[family]['path'].lower()
        allowed=[i for i in p['collection'].values() if collection.stats(i)['path']==path and
            collection.floor_for(i['grade'],0)<=p['unlocked_floor'] and i['id'] not in desired]
        if not allowed:continue
        def value(i):
            full=collection.stats(i)['attack']
            # A dropped weapon is usable only after an affordable repair.
            power=full if workshop.repair_quote(i)<=p['gold'] else battle_rules.contribution(i)
            return power*(1.15 if i['family']==family else 1)
        item=max(allowed,key=lambda i:(value(i),i['id'] in p['deck']))
        desired.append(item['id'])
    for cell,iid in enumerate(desired):
        if p['deck'][cell]==iid:continue
        if iid in p['deck']:continue
        item=p['collection'][iid]
        if item.get('location','carried')!='carried':
            if not collection.at_storage(p):return travel(a,'town','collection','retrieve a useful owned counter')
            if core.pack_used(p)>=core.pack_cap(p):
                spare=next((i for i in p['collection'].values() if i['id'] not in p['deck'] and i.get('location')=='carried'),None)
                if spare:return 'inspect:'+spare['id'] if p.get('collection_selected')!=spare['id'] else 'store:'+spare['id']
            return 'inspect:'+iid if p.get('collection_selected')!=iid else 'take:'+iid
        a.last_decision_reason='select the stronger owned counter'
        return 'inspect:'+iid if p.get('collection_selected')!=iid else f'deck:{cell}:{iid}'
    spare=next((i for i in p['collection'].values() if i['id'] not in p['deck'] and i.get('location','carried')!='storage'),None)
    if spare and (collection.claims(p) or core.pack_used(p)>=core.pack_cap(p)-1):
        if not collection.at_storage(p):return travel(a,'town','collection','secure claims and make room')
        return 'inspect:'+spare['id'] if p.get('collection_selected')!=spare['id'] else 'store:'+spare['id']
    return None


def investments(a,gold=None):
    """Rank affordable marginal improvements; scores are policy preferences."""
    p=a.s.doc;cash=p['gold'] if gold is None else gold;xp=state.xp_total(p);front=p['unlocked_floor']
    options=[]
    def add(room,action,price,gain,reason):
        if price<=cash and gain>0:options.append((gain/max(1,price),room,action,price,reason))
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid];stats=collection.stats(item);weight=preferred(a,item)
        q=collection.upgrade_quote(item)
        if q and affordable(p,q,cash):
            new={**item,'level':q['level']}
            gain=(collection.stats(new)['attack']/max(1,stats['attack'])-1)*weight
            add('forge','upgrade:'+iid,q['gold'],gain,'upgrade a useful weapon with earned materials')
        price=workshop.repair_quote(item)
        if price and item['durability']<item['maximum']*.8:
            gain=(stats['attack']/max(1,battle_rules.contribution(item))-1)*weight
            add('forge','mend:'+iid,price,gain,'restore worn weapon contribution')
    main=a.cfg.planner_path
    for path in dict.fromkeys([main]+[collection.families()[f]['path'].lower() for f in families(a)]):
        rank=p['training'][path]
        target=min(10,max(3,p['level']+2)) if path==main else min(6,max(2,p['level']//2))
        if rank<target:
            costxp=economy.train_xp_cost(rank+1,core._school_discounted(p,path))
            if xp>=costxp:
                gain=(.12 if path==main else .04)*(1.7 if a.cfg.planner_growth=='training' else 1)
                add('school','train_'+path,economy.train_gold(rank+1,front),gain,'train accuracy and attack')
        if rank==10 and not p.get('mastery',{}).get(path) and xp>=economy.MASTERY_XP:
            add('school','mastery_'+path,0,.1,'study earned weapon mastery')
    if p['level']<economy.LEVEL_CAP and xp>=economy.xp_need(p['level']):
        add('guildhall','guild_train',economy.levelup_gold(p['level']),.22*(1.6 if a.cfg.planner_growth=='levels' else 1),'buy body growth and equipment access')
    rack={o.id for o in core._forge_scene(deepcopy(p)).options if not o.locked}
    for slot in ('armor','shield','shoes'):
        old=economy.FORGE.get(p['gear'].get(slot) or '')
        oldbonus=state.gear_bonus(p,slot)
        for gear in economy.FORGE.values():
            if gear.slot!=slot or 'buy_'+gear.slug not in rack or not 0<gear.price<=cash:continue
            if old and not core.pack_can_take(p,old.slug):continue
            if slot=='shoes':gain=(gear.speed-(old.speed if old else 0))*.14
            else:gain=(gear.bonus-oldbonus)/max(10,oldbonus)*(1.6 if slot=='armor' else .7)
            add('forge','buy_'+gear.slug,gear.price,gain,'buy protection or movement that improves survival')
        if not old:continue
        if slot in ('armor','shield') and 'hone_'+slot in rack and p['xp']>=economy.hone_xp(front):
            gain=(economy.honed_bonus(old.bonus,state.hone_level(p,slot)+1)-oldbonus)/max(10,oldbonus)
            add('forge','hone_'+slot,economy.hone_price(front),gain*(1.6 if slot=='armor' else .7),'hone protection using earned gold and XP')
        left=p.get('durability',{}).get(slot)
        if left is not None and economy.wears(old) and left<economy.item_pool(old)*.3:
            if 'token_'+slot in rack:add('forge','token_'+slot,0,.5,'spend an owned repair token')
            elif p['xp']>=economy.hone_xp(front):add('forge','repair_'+slot,economy.repair_price(old,1-left/economy.item_pool(old)),.4,'repair protection before breakage')
    if core.pack_used(p)<core.pack_cap(p):
        for family in families(a):
            path=collection.families()[family]['path'].lower()
            old=max((collection.stats(p['collection'][iid])['attack'] for iid in p['deck'] if iid and collection.stats(p['collection'][iid])['path']==path),default=1)
            for grade in collection.GRADES:
                for source in ('craft','shop'):
                    q=workshop.acquisition_quote(family,grade,source)
                    if not affordable(p,q,cash):continue
                    fake=dict(family=family,grade=grade,level=q['level'],source=source)
                    new=collection.stats(fake)['attack']
                    # Optional family preference only within the same power band.
                    has_family=any(i['family']==family and i['id'] in p['deck'] for i in p['collection'].values())
                    gain=(new/max(1,old)-1)* (1.8 if path==main else .7)
                    if not has_family and new>=old*.8:gain+=.25
                    add('weapon_shop',('forge_craft:' if source=='craft' else 'forge_buy:')+family+':'+grade,q['gold'],gain,'acquire a useful family or new grade')
    return sorted(options,reverse=True)


def supplies(a):
    p=a.s.doc
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid]
        if item['durability']<=0 and item['source']=='starter' and p['gold']<workshop.repair_quote(item):
            return travel(a,'forge','practice:'+iid,'recover a broken starter at the practice bench')
        if collection.stats(item)['path']!='bow':continue
        q=quiver.quote(item['grade'],'ordinary')
        if quiver.count(p,item['grade'],'ordinary')<20 and quiver.used(p)+q['count']<=collection.catalog()['quiver']['capacity']:
            if p['gold']>=q['gold']:action='arrow_buy:'+item['grade']+':ordinary'
            elif item['grade']=='Common':action='arrow_practice'
            else:continue
            if p.get('quiver_view'):return action
            return travel(a,'forge','quiver_shop','restock finite arrows before hunting')
        for kind in ('arcane','concussive'):
            q=quiver.quote(item['grade'],kind)
            if quiver.count(p,item['grade'],kind)<5 and p['gold']>=q['gold']*3 and quiver.used(p)+q['count']<=collection.catalog()['quiver']['capacity']:
                if p.get('quiver_view'):return 'arrow_buy:'+item['grade']+':'+kind
                return travel(a,'forge','quiver_shop','carry ammunition for a different threat')
    return None


def gather_target(a):
    if not a.cfg.collection_gather:return None
    p=a.s.doc;needs=[]
    for iid in p['deck']:
        if not iid:continue
        item=p['collection'][iid];q=collection.upgrade_quote(item)
        if q and q['floor']<=p['unlocked_floor'] and q['gold']<=p['gold']:
            needs.append((preferred(a,item),q))
    for family in families(a):
        for grade in collection.GRADES[1:]:
            q=workshop.acquisition_quote(family,grade,'craft')
            if q['floor']<=p['unlocked_floor'] and q['gold']<=p['gold']:
                path=collection.families()[family]['path'].lower()
                old=max((collection.stats(p['collection'][i])['floor'] for i in p['deck'] if i and collection.stats(p['collection'][i])['path']==path),default=0)
                if collection.floor_for(grade,0)>old:needs.append((2 if path==a.cfg.planner_path else .7,q))
    candidates=[]
    for weight,q in needs:
        for key,site in gathering.SITES.items():
            missing=q['materials'].get(site['material'],0)-p['materials'].get(site['material'],0)
            if missing<=0 or site['floor']>min(p['unlocked_floor'],max(3,a.ready)):continue
            if economy.floor_entry_player_level(site['floor'])>p['level']:continue
            tool=p.get('utility_tools',{}).get(site['tool'])
            if not tool and p['gold']<site['price']+q['gold']:continue
            candidates.append((weight*missing/(site['yield_pct']*site['yield_amount']),key))
    return max(candidates)[1] if candidates else None


def visit_site(a,key):
    p=a.s.doc;site=gathering.SITES[key]
    if p['location']=='gathering':
        if p.get('gathering_site')!=key:return 'gather_back'
        tool=p.get('utility_tools',{}).get(site['tool'])
        if not tool:return 'gather_tool'
        if tool['condition']==0:
            return 'gather_mend' if p['gold']>=gathering.tool_repair_price(site,tool) else 'gather_back'
        return 'gather_begin'
    if p['location']=='gate_town' and p['floor']==site['floor']:return 'gather_site:'+key
    return travel(a,'gate','floor_'+str(site['floor']),'collect the missing recipe material at its named place')


def decide(a):
    s=a.s;p=s.doc;opts={o.id for o in s.legal()};a.last_decision_reason=''
    if p.get('group'):
        if a.policy=='random':
            choices=[o for o in opts if o.startswith(('strike:','skill:'))]+[o for o in ('guard','withdraw','approach') if o in opts]
            return a.rng.choice(sorted(choices)) if choices else 'flee'
        return combat_choice(s)
    if p.get('group_result'):return 'group_return'
    if p.get('movie_floor'):return 'skip'
    if p.get('sleeping'):return 'wake'
    if p.get('expedition'):
        exp=p['expedition'];site=gathering.SITES[exp['site']]
        if exp['attempts']>=6 or state.energy_now(p)<3 or p['hp']<state.max_hp(p)*.5 or not p['utility_tools'][site['tool']]['condition']:return 'gather_extract'
        return 'gather_step'
    if p.get('pending_events') and 'town' in opts:return 'town'
    action=prepare_owned(a)
    if action:return action
    if p.get('collection_view'):return 'collection_back'
    if p.get('workshop_view'):return 'shop_back'
    if p.get('quiver_view'):
        action=supplies(a)
        return action if action and action.startswith(('arrow_buy:','arrow_practice')) else 'arrow_back'
    if state.energy_now(p)<2:a.blocked['energy_wait']+=1;return None
    # Paid protection displaced by a better piece remains owned in the pack.
    # Sell it through the broker before a full pack prevents the next purchase.
    for slug,count in p['inventory'].items():
        gear=economy.FORGE.get(slug)
        if not count or not gear or gear.slot not in ('armor','shield','shoes') or gear.price<=0:continue
        worn=economy.FORGE.get(p['gear'].get(gear.slot) or '')
        if worn and gear.bonus<=worn.bonus and gear.speed<=worn.speed:
            return travel(a,'pawn','sell_'+slug,'sell replaced protection and recover upgrade funds')
    # Existing legal road medicine first, without creating replacement supplies.
    from .game_planner import legal_actions
    if p['hp']<state.max_hp(p)*.7 and 'use_medgel' in legal_actions(s):return 'use_medgel'
    # Invested capital remains in the actual bank until a concrete use is affordable.
    investor=a.policy=='investor'
    if investor and p['bank']>0 and a.vault_visit!=int(s.seconds//86400):
        if p['location']!='vault':return travel(a,'vault','collect_interest','collect accrued investment returns')
        if 'collect_interest' in opts:return 'collect_interest'
        a.vault_visit=int(s.seconds//86400)
    if p['hp']<state.max_hp(p)*.65:
        quote=economy.healer_tent_price(max(1,p['floor']),p['hp'],state.max_hp(p))
        road=economy.healer_tent_price(1,p['hp'],state.max_hp(p))
        if 'heal' in opts and p['gold']>=quote and quote<=max(road*2,economy.STEW_PRICE):return 'heal'
        if p['gold']>=road:
            if p['location']=='gate_town' and p['floor']==1:return 'heal'
            return travel(a,'gate','floor_1','travel to affordable recovery before another group')
        if investor and p['bank']>=road:return travel(a,'vault','withdraw_all','use savings to recover')
        a.blocked['health_wait']+=1;return None
    action=supplies(a)
    if action:return action
    protected=(p['gold']+p['bank'])*a.cfg.collection_investment if investor else 0
    spendable=max(0,p['gold']-max(0,protected-p['bank']))
    choices=investments(a,spendable)
    if choices:
        score,room,action,price,reason=choices[0]
        if room=='weapon_shop':
            if p.get('workshop_view'):return action
            # The Forge accepts its explicit catalog actions; no guessed stock.
            return travel(a,'forge',action,reason)
        return travel(a,room,action,reason)
    if investor and p['bank']>0:
        funded=investments(a,p['gold']+p['bank']-protected)
        if funded and funded[0][3]>p['gold']:
            return travel(a,'vault','withdraw_all','release saved capital for an affordable improvement')
    key=gather_target(a)
    if key:return visit_site(a,key)
    if p['location']=='gathering':return 'gather_back'
    target=max(1,min(p['unlocked_floor'],a.ready-a.cfg.planner_margin))
    while target>1 and economy.floor_entry_player_level(target)>p['level']:target-=1
    while target>1:
        history=a.route_history.get(target,[])
        if len(history)<3 or sum(history)/len(history)>=.7:break
        target-=1
    a.target=target
    if p['location']=='gate_town' and p['floor']==target:return 'hunt'
    return travel(a,'gate','floor_'+str(target),'hunt a reachable floor that has paid reliably')
