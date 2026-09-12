"""Resource-aware, imperfect heuristics. No future rolls or readiness outcomes used."""
from copy import copy
import math
from .model import POLICIES, Weapon
from .combat import damage, make_group, shield_hit


def usable(w):
    return w.condition > 0 or w.source == "recovery-starter"


def reserve(rules,p):
    if p.policy == "rusher":
        return 0
    paid = [p.stored_deck.get(i,w) for i,w in enumerate(p.deck)]
    total = 0
    for w in paid:
        q=copy(w); q.condition=0
        total += rules.repair_quote(q)
    return total*rules.config.repair_reserve


def maintain(rules,p,floor):
    """Keep affordable combat tools before optional heals and arrows."""
    c=rules.config
    if p.policy == "rusher":
        return False  # keep the original spend/retreat mistakes as a contrasting policy
    # The same three paid slots may each retain one displaced paid weapon.
    for i,current in enumerate(p.deck):
        paid=p.stored_deck.get(i,current)
        if paid.condition >= .65 and paid.source != "recovery-starter":
            if i in p.stored_deck:
                p.deck[i]=p.stored_deck.pop(i)
            continue
        target=1.
        cost=rules.repair_quote(paid,target)
        if cost > p.wealth() and c.recovery_mode == "partial" and paid.source != "recovery-starter":
            # Fractional work has the same per-unit basis and a one-gold minimum.
            full=copy(paid);full.condition=0
            target=min(1,paid.condition+p.wealth()/max(1,rules.repair_quote(full))*.98)
            if target >= paid.condition+1/rules.endurance(paid):
                cost=rules.repair_quote(paid,target)
            else:
                target=paid.condition
        if target>paid.condition and cost<=p.wealth() and p.pay(cost,"repairs"):
            paid.condition=target
            p.count("partial_repairs" if target<1 else "full_repairs")
            if i in p.stored_deck:
                p.deck[i]=p.stored_deck.pop(i)
            continue
        # Buying a low-grade replacement can be cheaper than a high-grade repair.
        cheap=Weapon(paid.family,source="replacement")
        price=rules.price(cheap)
        if paid.condition<.2 and (current.source!="replacement" or current.condition<.2) and price<cost and p.wealth()>=price+reserve(rules,p):
            if p.pay(price,"equipment"):
                p.stored_deck[i]=paid; p.deck[i]=cheap
                p.count("cheap_replacements")
                continue
        if not usable(current) and c.recovery_mode == "starter":
            # Explicit candidate: retained starter takes a slot; no fourth attack or resale.
            p.stored_deck[i]=paid
            p.deck[i]=Weapon(paid.family,condition=0,source="recovery-starter")
            p.count("starter_recoveries")
    # Rest is free only when the scheduled outside-combat recovery arrives.
    # Buy treatment if some combat gear is usable and money remains above upkeep reserve.
    missing=1-p.hp/rules.hp_max(p)
    bill=math.ceil(rules.economy[floor-1]["heal_full"]*missing*c.heal_cost_scale)
    if missing>.35 and any(usable(w) for w in p.deck) and bill<=max(0,p.wealth()-reserve(rules,p)):
        if p.pay(bill,"healing"):
            p.hp=rules.hp_max(p)
    if p.shield_condition<.6:
        bill=max(1,round(rules.economy[floor-1]["gold"]*4*(1-p.shield_condition)))
        if bill<=max(0,p.wealth()-reserve(rules,p)) and p.pay(bill,"repairs"):
            p.shield_condition=1
    if any(rules.weapons[w.family]["path"]=="Bow" for w in p.deck):
        for arrow,target in (("ordinary",12),("arcane",6),("fire",3)):
            if arrow=="fire" and p.policy in ("learner","saver"):
                continue
            unit=max(.1,rules.economy[floor-1]["gold"]*.01)*rules.arrows[arrow]["units"]
            budget=max(0,p.wealth()-reserve(rules,p))
            amount=min(max(0,target-p.ammo[arrow]),int(budget/unit))
            if amount and p.pay(amount*unit,"ammo"):
                p.ammo[arrow]+=amount
    return True


def estimate_route(rules,p,floor,deep=False,carrier=None,ground=False):
    """Expected public roster cost, not a simulation of future random encounters."""
    fr=rules.floors[floor-1]
    monsters=[m for m in fr["monsters"] if not deep or m["deepEligible"]]
    if not monsters:
        return None
    hpmax=rules.hp_max(p)
    stats=[]
    for m in monsters:
        weight=m["spawn"]*(3 if carrier and m["carrier"]==carrier else 1)*(3 if ground and not rules.types[m["proposedType"]]["air"] else 1)
        options=[]
        for w in p.deck:
            if not usable(w):continue
            path=rules.weapons[w.family]["path"]
            arrows=[a for a,n in p.ammo.items() if n>0] if path=="Bow" else ["ordinary"]
            if w.source=="recovery-starter" and "ordinary" not in arrows:arrows.append("ordinary")
            for arrow in arrows:
                hit,_=damage(rules,p,w,m,0,arrow)
                if hit:
                    if p.policy=="learner":
                        score=rules.attack(p,w)
                    else:score=hit
                    options.append((score,hit,w,arrow))
        if not options:
            stats.append((weight,0,100,1e6,0));continue
        _,hit,w,arrow=max(options,key=lambda v:v[0])
        count=2 if floor<=3 else 2.5 if floor<=10 else 3 if floor<=25 else 3.5 if floor<=50 else 4 if floor<=75 else 4.5
        count=max(2,count*rules.config.group_size_scale)
        spec=fr["specimens"]
        spec_weight=fr["deepSpecimenWeights"] if deep else {s:v["weight"] for s,v in spec.items()}
        totalw=sum(spec_weight.values())
        enemy_hp=sum(m["specimenStats"][s]["hp"]*weight for s,weight in spec_weight.items())/totalw*rules.config.group_hp_scale
        atk=sum(m["specimenStats"][s]["deepAtk" if deep else "atk"]*weight for s,weight in spec_weight.items())/totalw
        turns=max(1,enemy_hp/max(.01,hit*.92))
        raw,_=shield_hit(atk*.75,rules.armor(p)+rules.characters[p.level-1]["defense"],rules.shield(p))
        control=.78 if rules.weapons[w.family]["effect"] in ("Stun","Knockback") and p.policy!="learner" else 1
        incoming=max(.1,turns-.6)*raw*.9*control
        # Predict completion loss smoothly; near-lethal groups rapidly become poor farms.
        risk=incoming*count/max(1,p.hp)
        chance=max(.01,min(.98,1.08-risk*.65))
        gold=m["gold"]*sum(spec[s]["gold"]*weight for s,weight in spec_weight.items())/totalw
        gold*=rules.fade(p.ready_floor,floor)*rules.config.gold_scale*(fr["deep"]["reward"] if deep else 1)
        q=copy(w);q.condition=0
        wear=rules.repair_quote(q)/rules.endurance(w)*turns
        ammo=max(.1,fr["monsters"][0]["gold"]*.01)*rules.arrows[arrow]["units"]*turns if rules.weapons[w.family]["path"]=="Bow" and w.source!="recovery-starter" else 0
        healing=rules.economy[floor-1]["heal_full"]*incoming/hpmax*rules.config.heal_cost_scale
        net=gold*chance**count-wear-ammo-healing
        stats.append((weight,net,turns,risk,chance))
    total=sum(x[0] for x in stats)
    net,turns,risk,chance=[sum(x[0]*x[i] for x in stats)/total for i in range(1,5)]
    # Energy efficiency and time efficiency both matter; vary their weight by policy.
    rate=net/max(1,turns)**(.6 if p.policy=="saver" else .35)
    if carrier:rate*=1.15
    if ground:rate*=1.08
    return dict(floor=floor,deep=deep,carrier=carrier,ground=ground,net_per_enemy=net,actions=turns,risk=risk,win=chance,score=rate)


def route(rules,p,rng):
    if p.policy=="rusher":return None
    target=min(rules.config.max_floor,max(1,p.ready_floor))
    key=(target,p.level,p.armor_floor,p.shield_floor,int(p.shield_condition*4),int(p.hp/rules.hp_max(p)*4),
        tuple((a//5,b//5) for a,b in p.materials) if p.policy=="farmer" else (),
        tuple((w.family,w.grade,w.level,int(w.condition*5),w.source) for w in p.deck),tuple(n>0 for n in p.ammo.values()))
    candidates=p.route_cache.get(key)
    if candidates is None:
        floors=sorted({1,max(1,target//2),*[max(1,target-d) for d in (0,1,2,3,5)]})
        candidates=[]
        for f in floors:
            variants=[(False,None,False)]
            if p.policy=="specialist":variants.append((False,None,True))
            if p.policy=="farmer":
                paid=min((p.stored_deck.get(i,w) for i,w in enumerate(p.deck)),key=lambda w:rules.state(w)["floor"])
                q=rules.upgrades[paid.grade,min(20,paid.level+1)]["q"]
                ratios=rules.weapons[paid.family]["recipe"]
                j=max(range(2),key=lambda j:q*ratios[j]-p.materials[paid.grade][j])
                variants.append((False,"A" if j==0 else "B",False))
            if POLICIES[p.policy]["deep"] and f>=4:variants.append((True,None,False))
            for deep,carrier,ground in variants:
                estimate=estimate_route(rules,p,f,deep,carrier,ground)
                if estimate:candidates.append(estimate)
        # Retain only a bounded recent cache; no persistent map of every condition state.
        if len(p.route_cache)>24:p.route_cache.clear()
        p.route_cache[key]=candidates
    def score(c):
        memory=p.route_memory.get(str(c["floor"]),{})
        penalty=.6+.4*memory.get("win",1)
        return c["score"]*penalty if c["score"]>=0 else c["score"]/penalty
    best=max(candidates,key=score)
    if best["risk"]>1.1 and p.hp<rules.hp_max(p)*.5:
        p.count("rested_sessions")
        return (None,None)
    p.last_route=dict(best)
    return best["floor"],make_group(rules,best["floor"],rng,best["deep"],best["carrier"],best["ground"])
