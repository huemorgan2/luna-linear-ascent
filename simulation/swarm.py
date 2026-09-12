"""Persistent heuristic players and calendar-time progression."""
from __future__ import annotations

from copy import copy
from dataclasses import asdict
import math

from .combat import fight_group, make_group
from .model import POLICIES, Weapon, new_player, stream
from .policies import maintain, reserve, route, usable
from .diagnostics import diagnose, timeline_point


def restock(rules, p, floor):
    if rules.config.decision_model == "adaptive" and maintain(rules,p,floor):
        return
    row, cfg = rules.economy[floor-1], rules.config
    if p.hp < rules.hp_max(p)*.65:
        cost = math.ceil(row["heal_full"]*(1-p.hp/rules.hp_max(p))*cfg.heal_cost_scale)
        if p.pay(cost, "healing"):
            p.hp = rules.hp_max(p)
    for w in p.deck:
        if w.condition < .65:
            cost = rules.repair_quote(w)
            if p.pay(cost, "repairs"):
                w.condition = 1
    if p.shield_condition < .6:
        cost = max(1, round(row["gold"]*4*(1-p.shield_condition)))
        if p.pay(cost, "repairs"):
            p.shield_condition = 1
    if any(rules.weapons[w.family]["path"] == "Bow" for w in p.deck):
        targets = {"ordinary": 24, "arcane": 12}
        if p.policy in ("farmer", "tactician", "rusher"):
            targets["fire"] = 6
        for arrow, target in targets.items():
            need = max(0, target-p.ammo[arrow])
            # Per arrow: 1% of a same-floor normal kill × recipe-unit weight.
            cost = need*max(.1, row["gold"]*.01)*rules.arrows[arrow]["units"]
            if need and p.pay(cost, "ammo"):
                p.ammo[arrow] += need


def invest(rules, p, access):
    """Choose affordable marginal improvements; never grant missing resources."""
    cfg = rules.config
    changes = 0
    adaptive = cfg.decision_model == "adaptive" and p.policy != "rusher"
    for _ in range(0 if adaptive else 30):
        row = rules.characters[p.level-1]
        if p.level < 30 and p.xp >= row["xp"] and p.pay(row["gold"], "training"):
            before = rules.hp_max(p)
            p.xp -= row["xp"]
            p.level += 1
            p.hp += rules.hp_max(p)-before  # capacity gained outside a fight
            changes += 1
        else:
            break
    for _ in range(8):
        available = max(0,p.wealth()-(reserve(rules,p) if adaptive else 0))
        offers = []
        material_block = False
        gold_block = False
        for i, w in enumerate(p.deck):
            if w.source == "recovery-starter":
                # Repair the stored paid tool before buying a new higher-grade piece.
                continue
            candidates = []
            upgraded = rules.upgraded(w)
            if upgraded:
                candidates.append((upgraded, "upgrade"))
            if w.grade < 3:
                candidates += [(Weapon(w.family, w.grade+1, 0), "craft"),
                    (Weapon(w.family, w.grade+1, [0, 2, 4, 6][w.grade+1]), "shop")]
            for new, kind in candidates:
                state = rules.state(new)
                if state["floor"] > access or min(30, state["floor"]) > p.level:
                    continue
                price = rules.price(new, kind == "shop")
                recipe = [state["q"]*v for v in rules.weapons[new.family]["recipe"]] if kind != "shop" else [0, 0]
                if any(p.materials[new.grade][j] < recipe[j] for j in range(2)):
                    material_block = True
                    continue
                if price > available:
                    gold_block = True
                    continue
                gain = (rules.attack(p, new)-rules.attack(p, w))/max(1, rules.attack(p, w))
                weight = 2.5 if p.policy == "learner" and i == 0 else .5 if p.policy == "learner" else 1
                if p.policy == "saver" and rules.state(w)["floor"] >= max(1, p.ready_floor):
                    weight *= .25
                if gain > 0 or (new.level>w.level and new.grade==w.grade and rules.endurance(new)>rules.endurance(w)):
                    gain = max(gain, .01*(rules.endurance(new)/rules.endurance(w)-1))
                    offers.append((gain*weight/max(1, price), kind, i, new, price, recipe))
        for slot in ("armor", "shield"):
            current = getattr(p, slot+"_floor")
            for f in range(current+1, min(access, p.level if p.level < 30 else 100)+1):
                old = rules.economy[current-1][slot]
                bonus = rules.economy[f-1][slot]
                if bonus <= old:
                    continue
                price = rules.economy[f-1]["defense_step_gold"]*cfg.defense_cost_scale
                if price <= available:
                    weight = 1.4 if slot == "armor" else .65
                    offers.append(((bonus-old)/max(1, old)*weight/max(1, price), slot, 0, f, price, None))
                else:
                    gold_block = True
                break
        if adaptive and p.level<30:
            row=rules.characters[p.level-1]
            if p.xp>=row["xp"] and row["gold"]<=available:
                gain=(rules.characters[p.level]["atk"]-row["atk"])/max(1,rules.attack(p,max(p.deck,key=lambda w:rules.attack(p,w))))
                gain+=(rules.characters[p.level]["hp"]-row["hp"])/rules.hp_max(p)*.5
                offers.append((gain/max(1,row["gold"]),"training",0,p.level+1,row["gold"],None))
            elif p.xp>=row["xp"]:
                gold_block=True
        if not offers:
            reason = "materials" if material_block else "gold" if gold_block else "xp_or_gate"
            p.bottlenecks[reason] = p.bottlenecks.get(reason, 0)+1
            break
        _, kind, i, new, price, recipe = max(offers, key=lambda x: x[0])
        if not p.pay(price, "upgrades" if kind == "upgrade" else "training" if kind == "training" else "equipment"):
            raise AssertionError("Unaffordable offer selected")
        if kind == "training":
            before=rules.hp_max(p)
            p.xp-=rules.characters[p.level-1]["xp"]
            p.level=new
            p.hp+=rules.hp_max(p)-before
        elif kind in ("armor", "shield"):
            before = rules.hp_max(p)
            setattr(p, kind+"_floor", new)
            p.hp += rules.hp_max(p)-before
        else:
            if kind != "shop":
                for j in range(2):
                    p.materials[new.grade][j] -= recipe[j]
            new.source = kind
            p.deck[i] = new
        changes += 1
    return changes


def claim_drops(rules, p, drops, access):
    for item in drops:
        p.count("weapon_drops")
        if rules.state(item)["floor"] <= access and min(30, rules.state(item)["floor"]) <= p.level:
            matching = [i for i, w in enumerate(p.deck) if rules.weapons[w.family]["path"] == rules.weapons[item.family]["path"]]
            if matching:
                i = min(matching, key=lambda j: rules.attack(p, p.deck[j]))
                if rules.attack(p, item) > rules.attack(p, p.deck[i])*1.1:
                    p.deck[i] = item
                    p.count("drops_equipped")
                    continue
        # No fictional player market. A small condition-scaled salvage return.
        value = rules.price(item, True)*.02*item.condition/1.04**(rules.state(item)["floor"]-1)
        p.gold += value
        p.count("salvage_gold", value)


def loadout_key(p):
    return (p.level, p.armor_floor, p.shield_floor, int(p.shield_condition*10),
        tuple((w.family, w.grade, w.level, int(w.condition*10)) for w in p.deck),
        tuple((a, min(24, n)//6) for a, n in p.ammo.items()))


def readiness(rules, p, floor):
    wins = actions = 0
    damage_fraction = 0
    failures, by_type = {}, {}
    for trial in range(rules.config.readiness_trials):
        # Probe copies never need accumulated histories, which grow with every floor.
        q = copy(p)
        q.deck = [copy(w) for w in p.deck]
        q.ammo = dict(p.ammo)
        q.hp, q.energy = rules.hp_max(q), rules.energy_cap(q)
        for w in q.deck:
            w.cooldown = 0
        # Same floors and random tapes for all players; independent of training RNG.
        rng = stream(rules.config.seed, floor, f"probe:{trial}")
        group = make_group(rules, floor, rng)
        result = fight_group(rules, q, floor, group, rng, probe=True)
        wins += int(result.won)
        actions += result.actions
        damage_fraction += result.incoming/rules.hp_max(q)
        if not result.won: failures[result.failure or "unfinished"] = failures.get(result.failure or "unfinished",0)+1
        for key,values in result.types.items():
            dest=by_type.setdefault(key,dict(started=0,kills=0,actions=0,incoming=0))
            for k,v in values.items():dest[k]+=v
    n = rules.config.readiness_trials
    return dict(win_rate=wins/n, actions=actions/n, damage_share=damage_fraction/n, trials=n,failures=failures,types=by_type)


def snapshot(rules, p, floor, time, assessment):
    return dict(floor=floor, day=time/86400, active_minutes=p.active_seconds/60,
        level=p.level, hp=rules.hp_max(p), armor=rules.armor(p), shield=rules.shield(p),
        energy=rules.energy_cap(p), speed=p.speed, wealth=p.wealth(),
        deck=[dict(**asdict(w), attack=rules.attack(p, w), path=rules.weapons[w.family]["path"]) for w in p.deck],
        assessment=assessment, player=p.id, policy=p.policy)


def choose_route(rules, p, rng):
    if rules.config.decision_model == "adaptive":
        selected=route(rules,p,rng)
        if selected is not None:return selected
    target = min(rules.config.max_floor, max(1, p.ready_floor))
    if p.policy == "rusher":
        target = min(rules.config.max_floor, max(1, p.ready_floor+1))
    elif getattr(p, "loss_streak", 0) >= 2 or p.hp < rules.hp_max(p)*.5:
        # A heuristic retreat to easier hunting, not a stat nerf to the monster.
        target = max(1, target-2)
    deep = POLICIES[p.policy]["deep"] and target >= 4 and (p.policy == "rusher" or (getattr(p, "loss_streak", 0) == 0 and rng.random() < .4))
    carrier = None
    if p.policy == "farmer":
        w = min(p.deck, key=lambda x: rules.state(x)["floor"])
        state = rules.upgrades[w.grade, min(20, w.level+1)]
        required = [state["q"]*v for v in rules.weapons[w.family]["recipe"]]
        j = max(range(2), key=lambda j: required[j]-p.materials[w.grade][j])
        carrier = "A" if j == 0 else "B"
    return target, make_group(rules, target, rng, deep, carrier, p.policy == "specialist")


def simulate_player(rules, ident, policy):
    if rules.config.model_revision == "proposal-v1":
        from .legacy_swarm import simulate_player as legacy_player
        return legacy_player(rules,ident,policy)
    c = rules.config
    p = new_player(rules, ident, policy)
    rng = stream(c.seed, ident, "training")
    schedule = stream(c.seed, ident, "schedule")
    activity = schedule.uniform(1-c.activity_spread, 1+c.activity_spread)
    previous_probe_key = None
    floor_stats = {}
    timeline, recovery_episodes, failed_probes = [], [], {}
    recovery_start = None
    def track_recovery(day):
        nonlocal recovery_start
        paid=[p.stored_deck.get(i,w) for i,w in enumerate(p.deck)]
        broken=all(w.condition<=0 for w in paid)
        if broken and recovery_start is None:recovery_start=day
        if not broken and recovery_start is not None:
            recovery_episodes.append(dict(kind="all_paid_broken",start_day=recovery_start,end_day=day,days=day-recovery_start,censored=False))
            recovery_start=None
    for day in range(c.days):
        # Bank only existing balance; interest is not an assumed daily wage.
        if day:
            interest = p.bank*c.bank_interest_daily
            p.bank += interest
            p.count("interest", interest)
        p.hp = rules.hp_max(p)  # outside-combat dawn recovery from current model
        if schedule.random() > c.attendance:
            if day%7==6 or day==c.days-1:timeline.append(timeline_point(rules,p,day+1))
            continue
        for session in range(c.sessions_per_day):
            now = max(p.last_time, (day+session/c.sessions_per_day)*86400)
            elapsed = max(0, now-p.last_time)
            # Average sleep bonus; energy capacity still clips unused regeneration.
            regen = elapsed/60/c.energy_regen_minutes*(1+c.sleep_hours/48)
            p.energy = min(rules.energy_cap(p), p.energy+regen)
            p.last_time = now
            track_recovery(now/86400)
            town_floor=getattr(p,"last_route",{}).get("floor",max(1,p.ready_floor)) if c.decision_model=="adaptive" else max(1,p.ready_floor)
            restock(rules, p, town_floor)
            track_recovery(now/86400)
            invest(rules, p, min(c.max_floor, p.ready_floor+1))
            key = loadout_key(p)
            if key != previous_probe_key:
                while p.ready_floor < c.max_floor:
                    f = p.ready_floor+1
                    score = readiness(rules, p, f)
                    if score["win_rate"]+1e-12 < c.readiness_threshold:
                        failed_probes[f]=dict(day=now/86400,**score)
                        break
                    p.ready_floor = f
                    p.ready[f] = snapshot(rules, p, f, now, score)
                previous_probe_key = key
            if p.ready_floor == c.max_floor:
                break
            budget = c.minutes_per_day*activity*60/c.sessions_per_day
            used = 0
            while used < budget:
                if not any(usable(w) for w in p.deck):
                    # No imaginary free weapon. Wait for affordable repair; expose the stall.
                    p.bottlenecks["broken_weapons"] = p.bottlenecks.get("broken_weapons", 0)+1
                    break
                if p.energy < 1 and not POLICIES[policy]["exhausted"]:
                    p.bottlenecks["energy"] = p.bottlenecks.get("energy", 0)+1
                    break
                floor, group = choose_route(rules, p, rng)
                if floor is None:
                    p.bottlenecks["rest_for_health"]=p.bottlenecks.get("rest_for_health",0)+1
                    break
                x = fight_group(rules, p, floor, group, rng)
                p.loss_streak = 0 if x.won else getattr(p, "loss_streak", 0)+1
                spent_time = max(1, x.actions)*c.action_seconds
                used += spent_time
                p.active_seconds += spent_time
                p.last_time += spent_time
                track_recovery(p.last_time/86400)
                p.energy = min(rules.energy_cap(p), p.energy+spent_time/60/c.energy_regen_minutes)
                if x.won:
                    claim_drops(rules, p, x.drops, min(c.max_floor, p.ready_floor+1))
                fs = floor_stats.setdefault(floor, dict(attempts=0, wins=0, kills=0, deaths=0, actions=0, energy=0, exhausted=0, gold=0, xp=0))
                for k, v in (("attempts", 1), ("wins", int(x.won)), ("kills", x.kills), ("deaths", int(x.died)),
                    ("actions", x.actions), ("energy", x.energy_spent), ("exhausted", x.exhausted_enemies), ("gold", x.gold), ("xp", x.xp)):
                    fs[k] += v
                memory=p.route_memory.setdefault(str(floor),dict(win=.5))
                memory["win"] = .8*memory["win"]+.2*int(x.won)
                failures=fs.setdefault("failures",{})
                if not x.won:failures[x.failure or "unfinished"]=failures.get(x.failure or "unfinished",0)+1
                fs.setdefault("types",{})
                for typ,values in x.types.items():
                    dest=fs["types"].setdefault(typ,dict(started=0,kills=0,actions=0,incoming=0))
                    for k,v in values.items():dest[k]+=v
                # Price town services at the route actually used, not an unrelated frontier.
                restock(rules, p, floor)
                track_recovery(p.last_time/86400)
                # Shop choices are made between hunts, not after every attack.
                invest(rules, p, min(c.max_floor, p.ready_floor+1))
            to_bank = p.gold*POLICIES[policy]["bank"]
            p.gold -= to_bank
            p.bank += to_bank
        if day%7==6 or day==c.days-1 or p.ready_floor==c.max_floor:
            timeline.append(timeline_point(rules,p,min(c.days,day+1)))
        if p.ready_floor == c.max_floor:
            break
    if recovery_start is not None:
        recovery_episodes.append(dict(kind="all_paid_broken",start_day=recovery_start,end_day=None,days=c.days-recovery_start,censored=True))
    return dict(id=ident, policy=policy, activity_factor=activity, ready_floor=p.ready_floor,
        milestones=list(p.ready.values()), active_minutes=p.active_seconds/60,
        diagnosis=diagnose(rules,p,readiness),timeline=timeline,recovery_episodes=recovery_episodes,failed_probes=failed_probes,
        counters=p.counters, bottlenecks=p.bottlenecks, floors=floor_stats,
        final=dict(level=p.level, gold=p.gold, bank=p.bank, xp=p.xp, energy=p.energy,hp=p.hp,ammo=p.ammo,shield_condition=p.shield_condition,
            stored_deck={i:asdict(w) for i,w in p.stored_deck.items()},
            materials=p.materials, armor_floor=p.armor_floor, shield_floor=p.shield_floor,
            deck=[asdict(w) for w in p.deck]))


def reference_player(rules, floor):
    p = new_player(rules, -1, "tactician")
    p.level = min(30, floor)
    p.armor_floor = p.shield_floor = floor
    state = max((s for s in rules.data["upgrades"] if s["floor"] <= floor), key=lambda s: s["floor"])
    p.deck = [Weapon(f, state["gi"], state["level"]) for f in ("breach", "ember", "skirmisher")]
    p.hp, p.energy = rules.hp_max(p), rules.energy_cap(p)
    p.ammo = {a: 100 for a in rules.arrows}
    return p
