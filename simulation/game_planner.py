"""Fallible planning from visible state and real engine actions. No future RNG."""
from copy import deepcopy
import math

from .game_adapter import GameSession,combat,core,economy,state


def legal_actions(session):
    """The game's pack popovers are legal actions too, beyond scene buttons."""
    opts={o.id:o for o in session.legal()}
    for slug in session.doc.get('inventory',{}):
        for o in core.pack_actions(session.doc,slug)[0]:
            if not o.locked:opts[o.id]=o
    return opts


def path_of(slug):
    g=economy.FORGE.get(slug)
    return economy.PATH_OF_LINE.get(g.line,'blade') if g else 'blade'


def weapon_damage(session,slug):
    """Expected-damage UI hint after a legal equipment preview, never attack."""
    p=deepcopy(session.doc)
    if slug in combat._held_slugs(p):combat._promote_held(p,slug)
    else:
        if 'wear_'+slug not in legal_actions(session):return -1
        preview=GameSession(session.key,seconds=session.seconds,document=p,capture=False)
        preview.act('wear_'+slug)
        if preview.scene.refusal:return -1
        p=preview.doc
    path=path_of(slug)
    return combat._pred_damage(p,path,p['training'].get(path,0))


def fight(session):
    p=session.doc;e=p['encounter'];opts=legal_actions(session)
    held=combat._held_slugs(p)
    # A held side-blade is locked at range while a ranged weapon leads.
    # Only the lead blade offers close_in; never invent that missing action.
    usable=[slug for slug in held if ('attack' if slug==p['gear']['weapon'] else 'attack_'+slug) in opts
            or (slug==p['gear']['weapon'] and 'close_in' in opts)]
    candidates=usable+[s for s in p['inventory'] if 'wear_'+s in opts and s in economy.FORGE and economy.FORGE[s].slot=='weapon']
    scores={s:weapon_damage(session,s) for s in candidates}
    best=max(candidates,key=lambda s:(scores[s],s in held,s==p['gear']['weapon']))
    if best not in held:return 'wear_'+best,'switch to the visible monster counter'
    damage=scores[best]
    if damage<=0:return 'run','escape an unreachable enemy'
    # A conservative decision estimate using displayed maximum enemy attack.
    # No attack is rolled on a copy and no future random value is inspected.
    if p['hp']<e['atk']*.75 and damage<e['hp'] and 'run' in opts:return 'run','retreat before another likely lethal round'
    if best==p['gear']['weapon'] and 'close_in' in opts:return 'close_in','close in with the stronger counter'
    if path_of(best)=='bow' and 'treeline_shot' in opts:return 'treeline_shot','use the trained opening shot'
    action='attack' if p['gear']['weapon']==best else 'attack_'+best
    if action in opts:return action,'attack with the best visible damage'
    return ('run' if 'run' in opts else next(iter(opts))),'leave an unsupported attack position'


def travel(a,room,action,reason):
    a.last_decision_reason=reason
    return a.goto(room) or action


def owned_by_path(p):
    groups={k:[] for k in ('blade','bow','staff')}
    for slug in sorted(set(combat._held_slugs(p))|set(p['inventory'])):
        g=economy.FORGE.get(slug)
        if g and g.slot=='weapon':groups[path_of(slug)].append(slug)
    return groups


def obsolete_sale(p):
    """Keep the best owned weapon of each path and all healing supplies."""
    groups=owned_by_path(p)
    protected={max(slugs,key=lambda s:(economy.FORGE[s].bonus,s in combat._held_slugs(p))) for slugs in groups.values() if slugs}
    candidates=[]
    for slug,count in p['inventory'].items():
        g=economy.FORGE.get(slug)
        if g and g.price>0 and slug not in economy.BASIC_WEAPONS:
            worn=economy.FORGE.get(p['gear'].get(g.slot))
            inferior=(g.slot=='weapon' and slug not in protected) or (g.slot!='weapon' and worn and g.bonus<=worn.bonus and g.speed<=worn.speed)
            if inferior:candidates.append((core._pawn_offer(p,g),slug))
        elif slug=='luck_charm' and p['level']<economy.CHARM_SLOT_LEVEL:
            candidates.append((core._pawn_sundry(p,slug)[1],slug))
    return max(candidates)[1] if candidates else None


def decide(a):
    s=a.s;p=s.doc;cfg=a.cfg;opts=legal_actions(s);a.last_decision_reason=''
    if p.get('encounter'):
        action,reason=fight(s);a.last_decision_reason=reason;return action
    if p.get('movie_floor'):return 'skip'
    if p.get('sleeping'):return 'wake'
    main=cfg.planner_path;groups=owned_by_path(p);gold=p['gold'];xp=p['xp'];front=p['unlocked_floor']
    # Use available road healing before buying recovery. Spending/grants are
    # resolved by core.apply_choice, including the item's real heal amount.
    missing=state.max_hp(p)-p['hp']
    for slug in ('trauma_kit','medgel'):
        amount=int(economy.APOTHECARY[slug].effect.rsplit('_',1)[1])
        if 'use_'+slug in opts and missing>=amount*.7:
            a.last_decision_reason='use carried healing';return 'use_'+slug
    sale=obsolete_sale(p)
    if sale:return travel(a,'pawn','sell_'+sale,'sell obsolete equipment or a currently unusable charm')
    # Free upgrades already earned through real drops.
    for slug in p['inventory']:
        g=economy.FORGE.get(slug)
        if not g or 'wear_'+slug not in opts:continue
        old=economy.FORGE.get(p['gear'].get(g.slot))
        if g.slot!='weapon' and (not old or (g.speed>old.speed if g.slot=='shoes' else g.bonus>old.bonus)):
            a.last_decision_reason='equip a better owned item';return 'wear_'+slug
    for slot in economy.DURABILITY_SLOTS:
        g=economy.FORGE.get(p['gear'].get(slot));left=p.get('durability',{}).get(slot)
        if g and economy.wears(g) and left is not None and left<economy.item_pool(g)*.12:
            if p['inventory'].get('repair_token'):return travel(a,'forge','token_'+slot,'use a repair token')
            if gold>=economy.repair_price(g,1-left/economy.item_pool(g)) and xp>=economy.hone_xp(front):
                return travel(a,'forge','repair_'+slot,'repair before breakage')
            a.blocked['repair_resources']+=1
    # Recover some banked money only through the actual vault action.
    if p['bank']>0 and gold<economy.levelup_gold(p['level']):
        if 'collect_interest' in opts:return 'collect_interest'
        return travel(a,'vault','withdraw_all','withdraw saved money for progression')
    level_action=p['level']<economy.LEVEL_CAP and xp>=economy.xp_need(p['level']) and gold>=economy.levelup_gold(p['level'])
    target_rank=min(10,p['level']+2);rank=p['training'][main]
    training=rank<target_rank and gold>=economy.train_gold(rank+1,front) and xp>=economy.train_xp_cost(rank+1,core._school_discounted(p,main))
    if cfg.planner_growth=='training' and training:return travel(a,'school','train_'+main,'prioritize weapon training')
    if level_action:return travel(a,'guildhall','guild_train','buy the next character level')
    if training:return travel(a,'school','train_'+main,'train the main weapon')
    # Full XP bar: preserve the level-up fee rather than spending it on an
    # affordable but minor upgrade and throwing away further kill XP.
    saving_level=p['level']<economy.LEVEL_CAP and xp>=economy.xp_need(p['level']) and gold<economy.levelup_gold(p['level'])
    basics={'blade':'rusted_sword','bow':'basic_bow','staff':'worn_staff'}
    if not groups[main] and gold>=economy.BASIC_WEAPON_PRICE and not saving_level:
        return travel(a,'forge','buy_'+basics[main],'buy the planned weapon path')
    if groups[main] and not any(path_of(x)==main for x in combat._held_slugs(p)):
        slug=max(groups[main],key=lambda x:economy.FORGE[x].bonus)
        if 'wear_'+slug in opts:return 'wear_'+slug
    if p['slots']==1 and xp>=economy.CARRY2_XP and gold>=economy.CARRY2_GOLD and not saving_level:
        return travel(a,'school','buy_carry2','unlock a counter-weapon slot')
    # A second damage path can also be carried in the pack and swapped in
    # the game's legal sizing-up window. Keep one counter for each type.
    for other in ('staff','bow','blade'):
        if other==main:continue
        if not groups[other] and gold>=economy.BASIC_WEAPON_PRICE and not saving_level:
            return travel(a,'forge','buy_'+basics[other],'buy a missing monster counter')
        rank2=p['training'][other]
        if groups[other] and rank2<min(4,p['level']) and xp>=economy.train_xp_cost(rank2+1,core._school_discounted(p,other)) and gold>=economy.train_gold(rank2+1,front) and not saving_level:
            return travel(a,'school','train_'+other,'train an owned counter-weapon')
    if not saving_level:
        shop={o.id for o in core._forge_scene(deepcopy(p)).options if not o.locked}
        if core._door_open(p,economy.ARCANUM_LEVEL):shop|={o.id for o in core._arcanum_scene(deepcopy(p)).options if not o.locked}
        offers=[]
        for g in economy.FORGE.values():
            if 'buy_'+g.slug not in shop or not 0<g.price<=gold or g.slug in p['inventory'] or g.slug in combat._held_slugs(p):continue
            if g.slot not in ('weapon','shield','armor','shoes'):continue
            if economy.rung_player_level_req(g)>p['level'] or economy.rung_floor_req(g)>front:continue
            if g.slot=='weapon':
                if path_of(g.slug)!=main:continue
                old=max((economy.FORGE[x] for x in groups[main]),key=lambda x:x.bonus,default=None)
            else:old=economy.FORGE.get(p['gear'].get(g.slot))
            gain=g.speed-(old.speed if old else 0) if g.slot=='shoes' else g.bonus-(old.bonus if old else 0)
            if gain<=0 or (old and not core.pack_can_take(p,old.slug)):continue
            # A scoring preference, not a replacement game stat formula.
            offers.append((gain*(2 if g.slot=='weapon' else 1)/g.price,g))
        if offers:
            g=max(offers,key=lambda x:x[0])[1]
            return travel(a,'arcanum' if g.line=='sorcerer' else 'forge','buy_'+g.slug,'buy a useful equipment improvement')
    # Floors are a farming decision, not simply the highest past probe win.
    target=max(1,min(front,max(1,a.ready),p['level']+1-cfg.planner_margin))
    while target>1:
        history=a.route_history.get(target,[])
        if len(history)<3 or sum(history)/len(history)>=.6:break
        target-=1
    a.target=target
    if state.energy_now(p)<economy.COST_WILDS_FIGHT:a.blocked['energy_wait']+=1;return None
    if p['hp']<state.max_hp(p)*.75:
        # Before the next scheduled visit, sleep supplies recovery. During
        # a visit buy affordable health through whichever real option is cheaper.
        quote=economy.healer_tent_price(max(1,p['floor']),p['hp'],state.max_hp(p))
        if gold>=quote and quote<=economy.STEW_PRICE*math.ceil(missing/economy.STEW_HEAL_HP) and 'heal' in opts:
            a.last_decision_reason='buy economical full recovery';return 'heal'
        if gold>=economy.STEW_PRICE:
            if 'stew' in opts:a.last_decision_reason='buy partial recovery';return 'stew'
            return travel(a,'lodge','stew','buy partial recovery')
        a.blocked['health_wait']+=1;return None
    if p['location']=='gate_town' and p['floor']==target:
        a.last_decision_reason='hunt a sustainable floor';return 'hunt'
    if p['location']=='gate':return 'floor_'+str(target)
    return a.goto('gate')
