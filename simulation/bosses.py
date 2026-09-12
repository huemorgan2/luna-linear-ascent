"""Discrete timestamped attacks against shared HP, with finite player resources."""
from __future__ import annotations

import heapq
import math
import statistics

from .combat import shield_hit
from .model import stream
from .swarm import reference_player, readiness, snapshot


def direct_damage(rules, floor, member):
    defense = rules.economy[floor-1]["warden"]["defense"]
    amounts = []
    for w in member["deck"]:
        factor = .9 if w["family"] == "skirmisher" else .65 if w["path"] == "Bow" else 1
        cut = .75 if floor >= 21 else 1
        amounts.append(max(1, .75*w["attack"]*factor-defense/2)*cut)
    return max(amounts)


def parameters(rules, floor, reference):
    c = rules.config
    w = rules.economy[floor-1]["warden"]
    hp = w["legacy_shared_hp" if c.warden_pool == "legacy_shared" else "hp"]*c.warden_hp_scale
    heal = 0.
    if floor >= c.warden_heal_start:
        heal = direct_damage(rules, floor, reference)/c.warden_cadence_seconds*c.warden_heal_reference*c.warden_heal_growth**(floor-c.warden_heal_start)
    return dict(hp=hp, atk=w["atk"], defense=w["defense"], heal_per_second=heal)


def battle(rules, floor, members, count, params, trial=0, trace=False):
    c = rules.config
    if not members or count < 1:
        return dict(won=False, seconds=0, hp_left=params["hp"], reason="no qualified players", strikes=0)
    queue, state = [], []
    for i in range(count):
        m = members[i % len(members)]
        rng = stream(c.seed, floor, f"boss:{trial}:{i}")
        cadence = c.warden_cadence_seconds*rng.uniform(.9, 1.1)
        state.append(dict(hp=m["hp"], energy=m["energy"], damage=direct_damage(rules, floor, m),
            armor=m["armor"], shield=m["shield"], cadence=cadence, rng=rng))
        heapq.heappush(queue, (rng.uniform(0, c.warden_cadence_seconds), i))
    hp, now, hits = params["hp"], 0., 0
    events = []
    while queue:
        at, i = heapq.heappop(queue)
        s = state[i]
        hp = min(params["hp"], hp+params["heal_per_second"]*(at-now))
        now = at
        if s["hp"] <= 0 or s["energy"] < c.warden_energy_per_strike:
            continue
        s["energy"] -= c.warden_energy_per_strike
        dmg = s["damage"]*s["rng"].uniform(2/3, 4/3) if s["rng"].random() >= .08 else 0
        hp -= dmg
        hits += 1
        if trace:
            events.append(dict(second=round(at, 3), player=i, damage=dmg, hp=max(0, hp), energy=s["energy"]))
        if hp <= 0:
            return dict(won=True, seconds=now, hp_left=0, reason="defeated", strikes=hits, trace=events)
        incoming, _ = shield_hit(params["atk"]*s["rng"].uniform(.5, 1), s["armor"], s["shield"])
        s["hp"] -= incoming
        if s["hp"] > 0 and s["energy"] >= c.warden_energy_per_strike:
            heapq.heappush(queue, (at+s["cadence"], i))
    return dict(won=False, seconds=now, hp_left=hp, reason="energy or survival window exhausted", strikes=hits, trace=events)


def minimum_party(rules, floor, members, params):
    if not members:
        return dict(required=None, status="no qualified players", tested_max=0, success_rate=None)
    c = rules.config
    # Prefix rosters and random tapes are stable as n grows; no refills or tuning to N.
    required_wins = math.ceil(c.warden_success_threshold*c.warden_trials-1e-9)
    cache = {}
    def evaluate(n):
        if n not in cache:
            rows = [battle(rules, floor, members, n, params, t) for t in range(c.warden_trials)]
            cache[n] = rows
        rows = cache[n]
        return sum(r["won"] for r in rows) >= required_wins
    high = 1
    while not evaluate(high) and high < c.warden_max_party:
        high = min(c.warden_max_party, high*2)
    if not evaluate(high):
        return dict(required=None, status="above search limit", tested_max=high,
            success_rate=sum(r["won"] for r in cache[high])/c.warden_trials,
            best_remaining_hp_fraction=min(r["hp_left"] for r in cache[high])/params["hp"])
    low = 1
    while low < high:
        mid = (low+high)//2
        if evaluate(mid):
            high = mid
        else:
            low = mid+1
    wins = [r for r in cache[high] if r["won"]]
    return dict(required=high, status="extrapolated peers" if high > len(members) else "observed cohort sufficient",
        tested_max=c.warden_max_party, success_rate=len(wins)/c.warden_trials,
        seconds=statistics.mean(r["seconds"] for r in wins))


def evaluate_floor(rules, floor, observed):
    p = reference_player(rules, floor)
    assessment = readiness(rules, p, floor)
    ref = snapshot(rules, p, floor, 0, assessment)
    params = parameters(rules, floor, ref)
    reference = minimum_party(rules, floor, [ref], params)
    reference["status"] = "reference equipment benchmark" if reference["required"] else reference["status"]
    reference["hunting_win_rate"] = assessment["win_rate"]
    reference["qualified"] = assessment["win_rate"] >= rules.config.readiness_threshold
    # Deterministic order by player ID, not hand-picked strongest party.
    cohort = sorted(observed, key=lambda m: m["player"])
    return dict(floor=floor, name=rules.floors[floor-1]["warden"]["name"],
        **params, available_players=len(cohort), reference=reference,
        observed=minimum_party(rules, floor, cohort, params))
