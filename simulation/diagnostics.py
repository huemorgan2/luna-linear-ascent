"""Observed finances and labeled counterfactual probes, never extra player resources."""
from copy import copy
from dataclasses import asdict
from .model import Weapon


def financials(p):
    c=p.counters
    spending={k[6:]:v for k,v in c.items() if k.startswith("spent_")}
    incoming={k:c.get(k,0) for k in ("earned_gold","interest","salvage_gold")}
    accounted=50+sum(incoming.values())-sum(spending.values())-c.get("lost_gold",0)
    return dict(starting_gold=50,incoming=incoming,spending=spending,death_loss=c.get("lost_gold",0),
        forfeited_pending_gold=c.get("forfeited_gold",0),ending_wealth=p.wealth(),conservation_error=accounted-p.wealth())


def requirements(rules,p):
    access=min(rules.config.max_floor,p.ready_floor+1)
    offers=[]
    for i,current in enumerate(p.deck):
        w=p.stored_deck.get(i,current)
        if w.source=="recovery-starter":continue
        new=Weapon(w.family,w.grade,min(20,w.level+1)) if w.level<20 else Weapon(w.family,min(3,w.grade+1),0)
        if w.grade==3 and w.level==20:continue
        s=rules.state(new)
        need=[s["q"]*ratio for ratio in rules.weapons[w.family]["recipe"]]
        price=rules.price(new)
        offers.append(dict(slot=i,family=w.family,grade=new.grade,level=new.level,floor=s["floor"],gold=price,
            gold_missing=max(0,price-p.wealth()),materials=need,
            materials_missing=[max(0,n-have) for n,have in zip(need,p.materials[new.grade])],
            gate_blocked=s["floor"]>access or min(30,s["floor"])>p.level,
            broken=w.condition<=0,repair_quote=rules.repair_quote(w)))
    training=rules.characters[p.level-1]
    return dict(weapons=offers,training=dict(level=p.level+1 if p.level<30 else None,
        gold=training["gold"] if p.level<30 else 0,gold_missing=max(0,training["gold"]-p.wealth()) if p.level<30 else 0,
        xp_missing=max(0,training["xp"]-p.xp) if p.level<30 else 0))


def diagnose(rules,p,readiness):
    f=min(rules.config.max_floor,p.ready_floor+1)
    current=readiness(rules,p,f)
    repaired=copy(p);repaired.deck=[copy(p.stored_deck.get(i,w)) for i,w in enumerate(p.deck)]
    repaired.ammo=dict(p.ammo)
    for w in repaired.deck:w.condition=1
    repaired.shield_condition=1
    with_repairs=readiness(rules,repaired,f)
    supplied=copy(repaired);supplied.ammo={a:max(n,24) for a,n in p.ammo.items()}
    with_supplies=readiness(rules,supplied,f)
    req=requirements(rules,p)
    reasons=[]
    if any(w.condition<=0 for w in p.deck) or p.stored_deck:reasons.append("equipment_recovery")
    if with_repairs["win_rate"]>current["win_rate"]:reasons.append("condition_limits_combat")
    if with_supplies["win_rate"]>with_repairs["win_rate"]:reasons.append("ammunition_limits_combat")
    relevant=[x for x in req["weapons"] if not x["gate_blocked"]]
    if any(x["gold_missing"]>0 for x in relevant) or req["training"]["gold_missing"]>0:reasons.append("gold_shortfall")
    if any(any(x["materials_missing"]) for x in relevant):reasons.append("material_shortfall")
    if not relevant:reasons.append("equipment_or_training_gate")
    if with_supplies["win_rate"]<rules.config.readiness_threshold:
        reasons.append("combat_capability")
    if current["failures"].get("no_reachable_weapon_or_ammo",0):reasons.append("missing_reach_or_ammo")
    if current["failures"].get("survival",0):reasons.append("survival")
    if current["failures"].get("action_limit",0):reasons.append("damage_or_counter")
    if p.ready_floor==rules.config.max_floor:reasons=["study_complete"]
    return dict(next_floor=f,reasons=reasons,probe=current,repaired_probe=with_repairs,resupplied_probe=with_supplies,
        requirements=req,finances=financials(p),last_route=getattr(p,"last_route",None),
        counterfactual_note="Repair/supply probes use disposable copies; they grant nothing to the player. Reasons may overlap and are hypotheses, not unique causal percentages.")


def timeline_point(rules,p,day):
    return dict(day=day,ready_floor=p.ready_floor,level=p.level,wealth=p.wealth(),hp=p.hp,
        energy=p.energy,conditions=[round(w.condition,3) for w in p.deck],
        stored_broken=sum(w.condition<=0 for w in p.stored_deck.values()),
        counters=dict(p.counters),active_minutes=p.active_seconds/60)


def summarize(players):
    diagnosed=[p for p in players if "diagnosis" in p]
    if not diagnosed:return dict(available=False,note="This run predates detailed diagnostics.")
    reasons,spending={},{}
    episodes=[]
    for p in diagnosed:
        for r in p["diagnosis"]["reasons"]:reasons[r]=reasons.get(r,0)+1
        for k,v in p["diagnosis"]["finances"]["spending"].items():spending[k]=spending.get(k,0)+v
        episodes.extend(p.get("recovery_episodes",[]))
    return dict(available=True,players=len(diagnosed),reason_players=reasons,spending=spending,
        broke_all_paid_tools=sum(any(e["kind"]=="all_paid_broken" for e in p.get("recovery_episodes",[])) for p in diagnosed),
        recovery_episodes=len(episodes),recovered=sum(not e["censored"] for e in episodes),
        max_accounting_error=max(abs(p["diagnosis"]["finances"]["conservation_error"]) for p in diagnosed))
