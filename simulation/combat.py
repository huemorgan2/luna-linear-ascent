"""Action-based proposal combat. Each call mutates only its simulated player."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from .model import POLICIES, Weapon, interpolate


@dataclass
class Outcome:
    won: bool = False
    died: bool = False
    retreated: bool = False
    kills: int = 0
    actions: int = 0
    energy_spent: int = 0
    exhausted_enemies: int = 0
    gold: float = 0
    xp: float = 0
    incoming: float = 0
    materials: list = field(default_factory=lambda: [[0, 0] for _ in range(4)])
    drops: list = field(default_factory=list)
    trace: list = field(default_factory=list)


def make_group(rules, floor, rng, deep=False, carrier=None, ground_bias=False):
    f = rules.floors[floor-1]
    monsters = [m for m in f["monsters"] if not deep or m["deepEligible"]]
    if not monsters:
        monsters, deep = f["monsters"], False
    weights = [m["spawn"] * (3 if carrier and m["carrier"] == carrier else 1) *
        (3 if ground_bias and not rules.types[m["proposedType"]]["air"] else 1) for m in monsters]
    spec_names = list(f["specimens"])
    spec_weights = [f["deepSpecimenWeights"][s] if deep else f["specimens"][s]["weight"] for s in spec_names]
    out = []
    for i in range(rules.group_size(floor, rng)):
        m = dict(rng.choices(monsters, weights=weights)[0])
        s = rng.choices(spec_names, weights=spec_weights)[0]
        stats = m["specimenStats"][s]
        m.update(hp=stats["hp"]*rules.config.group_hp_scale,
                 atk=stats["deepAtk"] if deep else stats["atk"], specimen=s, deep=deep,
                 speed=rules.types[m["proposedType"]]["speed"] + (1 if s == "alpha" else 0) + (1 if deep else 0),
                 gap=1 if i == 0 else (0 if i % 3 == 1 else 1))
        out.append(m)
    return out


def start_enemy(p):
    """Last point funds the entire enemy. No negative energy or future debt."""
    funded = p.energy >= 1
    if funded:
        p.energy -= 1
    return funded


def shield_hit(raw, armor, shield):
    a = min(armor/2, raw*.5)
    s = min(shield/2, max(0, raw*.75-a))
    return max(1, raw-a-s), s


def damage(rules, p, item, enemy, gap, arrow="ordinary", exhausted=False, exposed=False):
    w, typ = rules.weapons[item.family], rules.types[enemy["proposedType"]]
    if (item.condition <= 0 and item.source != "recovery-starter") or (w["path"] == "Blade" and (typ["air"] or gap > 0)):
        return 0., "power"
    channel = "magic" if w["path"] == "Staff" else "power"
    factor = 1.
    if w["path"] == "Bow":
        a = rules.arrows[arrow]
        channel = a["channel"].lower()
        factor *= a["impact"]
        if gap == 0:
            factor *= .9 if item.family == "skirmisher" else .65
        if item.family == "runestring" and channel == "magic":
            factor *= 1.25
        if item.family == "hawkeye" and gap >= 2 and item.cooldown == 0:
            factor *= 1.2
    raw = rules.attack(p, item) * .75 * factor
    defense = enemy["defense"] * (.8 if exposed else 1)
    floor_damage = 1 if rules.config.model_revision == "proposal-v1" else .15*raw
    result = max(floor_damage, raw-defense/2) * typ[channel]
    if exhausted:
        result *= rules.config.exhaustion_damage
    return max(1., result), channel


def choose_attack(rules, p, enemy, gap, rng, exhausted, exposed):
    policy = POLICIES[p.policy]
    options = []
    for i, item in enumerate(p.deck):
        w = rules.weapons[item.family]
        arrows = [a for a, n in p.ammo.items() if n > 0] if w["path"] == "Bow" else ["ordinary"]
        for a in arrows:
            hit, channel = damage(rules, p, item, enemy, gap, a, exhausted, exposed)
            score = hit
            if policy["tactical"] and item.cooldown == 0 and hit:
                effect = w["effect"]
                if w["path"] == "Bow" and a not in ("ordinary", "arcane"):
                    effect = {"fire":"Burn", "poison":"Poison", "pinning":"Slow", "concussive":"Knockback"}[a]
                if effect in ("Stun", "Knockback"):
                    score += enemy["atk"]*.22
                if effect in ("Poison", "Burn", "Bleed") and enemy["hp"] > hit*1.5:
                    score += rules.attack(p, item)*.12
            if not policy["tactical"]:
                score = rules.attack(p, item) if hit else 0
            # Equivalent damage favors the cheaper payload.
            score -= rules.arrows[a]["units"]*.00001
            if hit:
                options.append((score, i, a, hit, channel))
    if not options:
        return None
    if rng.random() < policy["mistakes"]:
        return rng.choice(options)
    return max(options, key=lambda x: (x[0], -x[1]))


def roll_loot(rules, enemy, floor, rng):
    cfg = rules.loot
    mult = cfg["specimen"][enemy.get("specimen", "common")]
    for t in enemy.get("traits", []):
        mult *= cfg["body"].get(t, 1) * cfg["bite"].get(t, 1)
    materials = [[0, 0] for _ in range(4)]
    weapon_probs = []
    for gi, (mat, wp) in enumerate(zip(interpolate(cfg["materialKnots"], floor), interpolate(cfg["weaponKnots"], floor))):
        if gi == 3 and floor < cfg["legendaryDiscoveryFloor"]:
            mat = wp = 0
        deep = enemy.get("deep", False)
        mp = min(.95, mat/100 * mult * (cfg["deepMaterial"][gi] if deep else 1) * rules.config.material_scale)
        weapon_probs.append(wp/100 * mult * (cfg["deepWeapon"][gi] if deep else 1))
        if rng.random() < mp:
            y = min(5, 1+max(0, floor-(1+25*gi))//6)
            materials[gi] = [y*x for x in cfg["carrierRatios"][enemy["carrier"]]]
    total = sum(weapon_probs)
    if total > .5:
        weapon_probs = [p*.5/total for p in weapon_probs]
    roll, drop = rng.random(), None
    for gi, prob in enumerate(weapon_probs):
        roll -= prob
        if roll < 0:
            typ = enemy["proposedType"]
            favored = "Bow" if typ.startswith("air") else "Staff" if typ == "ground-magic" else "Blade" if typ == "ground-power" else ""
            choices = list(rules.weapons.values())
            w = rng.choices(choices, weights=[3 if w["path"] == favored else 1 for w in choices])[0]
            drop = Weapon(w["id"], gi, 0, [.4, .3, .2, .1][gi], source="drop")
            break
    return materials, drop


def fight_group(rules, p, floor, enemies, rng, *, probe=False, trace=False, retreat_after=None):
    """One continuous sequential group; XP per kill, loot only on full clear.

    Probe callers must pass a disposable player copy. They never roll rewards.
    """
    result = Outcome()
    pending_gold = 0
    policy = POLICIES[p.policy]
    max_hp = rules.hp_max(p)
    for index, original in enumerate(enemies):
        if retreat_after is not None and index >= retreat_after:
            result.retreated = True
            break
        if index and not probe and (p.hp < max_hp*policy["retreat"] or (p.energy < 1 and not policy["exhausted"])):
            result.retreated = True
            break
        enemy = dict(original)
        funded = start_enemy(p)
        result.energy_spent += int(funded)
        result.exhausted_enemies += int(not funded)
        if trace:
            result.trace.append(dict(enemy=index+1, event="begin", spent=int(funded), energy=p.energy, exhausted=not funded))
        gap = enemy.get("gap", 1)
        dot = {}  # effect -> (remaining phases, damage); only this enemy
        slow = stun_resist = exposed = 0
        alive = True
        for turn in range(rules.config.max_combat_actions):
            result.actions += 1
            speed = max(1, p.speed-(0 if funded else rules.config.exhaustion_speed))
            mspd = max(1, enemy["speed"]-(3 if slow else 0))
            stunned = pushed = False
            prior_cooldowns = [w.cooldown for w in p.deck]
            action = choose_attack(rules, p, enemy, gap, rng, not funded, exposed)
            new_dot = None
            if action is None:
                if not rules.types[enemy["proposedType"]]["air"] and gap:
                    gap -= 1
                else:
                    result.retreated = True
                    break
            elif not probe and p.hp < max_hp*policy["retreat"] and turn > 0:
                if rng.random() < min(.9, max(.15, .5+.05*(speed-mspd)+.1*gap)):
                    result.retreated = True
                    break
            else:
                _, wi, arrow, hit, channel = action
                item = p.deck[wi]
                weapon = rules.weapons[item.family]
                if weapon["path"] == "Bow":
                    p.ammo[arrow] -= 1
                item.condition = max(0, item.condition-1/rules.endurance(item))
                if rng.random() >= .08:
                    dealt = hit*rng.uniform(2/3, 4/3)
                    enemy["hp"] -= dealt
                    if trace:
                        result.trace.append(dict(enemy=index+1, turn=turn+1, event="hit", damage=dealt, weapon=item.family))
                    if exposed:
                        exposed -= 1
                    if item.cooldown == 0 and item.source != "recovery-starter":
                        effect = weapon["effect"]
                        if weapon["path"] == "Bow" and arrow not in ("ordinary", "arcane"):
                            effect = {"poison":"Poison", "fire":"Burn", "pinning":"Slow", "concussive":"Knockback"}[arrow]
                        item.cooldown = weapon["cooldown"] or (3 if arrow not in ("ordinary", "arcane") else 0)
                        traits = enemy.get("traits", [])
                        if effect in ("Poison", "Burn", "Bleed"):
                            immune = {"Poison":"venomproof", "Burn":"fireproof", "Bleed":"bloodless"}[effect]
                            # Wrongmade are bloodless; no invented susceptibility by animal name.
                            if immune not in traits and not (effect == "Bleed" and enemy.get("kind") == "wrongmade"):
                                rate, phases = {"Poison":(.08, 3), "Burn":(.12, 2), "Bleed":(.1, 2)}[effect]
                                dm = rules.attack(p, item)*rate*rules.types[enemy["proposedType"]]["magic" if effect == "Burn" else "power"]
                                if not funded:
                                    dm *= rules.config.exhaustion_damage
                                if effect == "Burn" and "flammable" in traits:
                                    dm *= 1.5
                                new_dot = (effect, phases, dm)
                        elif effect == "Stun" and not stun_resist:
                            stunned = True
                            stun_resist = 3
                        elif effect == "Knockback" and "steadfast" not in traits:
                            gap, pushed = min(3, gap+2), True
                        elif effect == "Slow":
                            slow = 3
                        elif effect == "Expose":
                            exposed = 2
            # Existing damage-over-time ticks on later actions, not on application.
            for effect, (left, dm) in list(dot.items()):
                enemy["hp"] -= dm
                if trace:
                    result.trace.append(dict(enemy=index+1, turn=turn+1, event="dot", effect=effect, damage=dm))
                if left <= 1:
                    del dot[effect]
                else:
                    dot[effect] = (left-1, dm)
            if new_dot:
                dot[new_dot[0]] = new_dot[1:]
            for item, old in zip(p.deck, prior_cooldowns):
                if old:
                    item.cooldown = max(0, item.cooldown-1)
            if enemy["hp"] <= 0:
                alive = False
                break
            if not stunned:
                if not pushed and gap:
                    gap = max(0, gap-(2 if rules.types[enemy["proposedType"]]["air"] else 1))
                if gap == 0:
                    dodge = min(.30, max(0, .1+.025*(speed-mspd)))
                    if rng.random() >= dodge:
                        raw = enemy["atk"]*rng.uniform(.5, 1)
                        hit, absorbed = shield_hit(raw, rules.armor(p)+rules.characters[p.level-1]["defense"], rules.shield(p))
                        p.hp -= hit
                        result.incoming += hit
                        p.shield_condition = max(0, p.shield_condition-absorbed/rules.shield_endurance(p))
            slow, stun_resist = max(0, slow-1), max(0, stun_resist-1)
            if p.hp <= 0:
                result.died = True
                break
        if alive:
            if not result.died:
                result.retreated = True
            break
        result.kills += 1
        if not probe:
            spec = rules.floors[floor-1]["specimens"][enemy.get("specimen", "common")]
            deep_mult = rules.floors[floor-1]["deep"]["reward"] if enemy.get("deep") else 1
            fade = rules.fade(p.ready_floor,floor)
            gold = max(1, round(enemy["gold"]*spec["gold"]*deep_mult*rng.uniform(.5, 1.5)*rules.config.gold_scale*fade))
            xp = min(max(1, round(enemy["xp"]*spec["hp"]*deep_mult*rng.uniform(.75, 1.25)*fade)), max(1, gold//2))
            p.xp += xp
            result.xp += xp
            pending_gold += gold
            mats, drop = roll_loot(rules, enemy, floor, rng)
            for gi in range(4):
                for j in range(2):
                    result.materials[gi][j] += mats[gi][j]
            if drop:
                result.drops.append(drop)
    result.won = result.kills == len(enemies) and p.hp > 0
    if not probe:
        if result.won:
            result.gold = pending_gold
            p.gold += pending_gold
            for gi in range(4):
                for j in range(2):
                    p.materials[gi][j] += result.materials[gi][j]
            if not p.tutorial:
                p.materials[0][0] += 2
                p.materials[0][1] += 6
                p.tutorial = True
        else:
            result.materials = [[0, 0] for _ in range(4)]
            result.drops = []
            p.count("forfeited_gold", pending_gold)
        if result.died:
            loss = p.gold*rules.config.death_gold_loss if p.level > 1 else 0
            p.gold -= loss
            p.count("lost_gold", loss)
            for item in p.deck:
                item.condition = max(0, item.condition-rules.config.death_condition_loss)
            p.hp = max_hp
        for key, val in (("groups", 1), ("wins", int(result.won)), ("deaths", int(result.died)),
            ("retreats", int(result.retreated)), ("kills", result.kills), ("energy_spent", result.energy_spent),
            ("exhausted_enemies", result.exhausted_enemies), ("earned_gold", result.gold), ("earned_xp", result.xp)):
            p.count(key, val)
    return result
