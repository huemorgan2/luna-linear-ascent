"""Generate /mechanics page data from the real game numbers.

Reads plugin_linear_ascent.economy + the floor YAML (same import path
worldd itself uses) and writes static/site/mechanics-data.js — the
data file the unlinked /mechanics page renders. Run it whenever balance
changes:

    .venv/bin/python tools/gen_mechanics.py

The Kill Level column is Monte-Carlo'd here, offline: for each monster
(common specimen, full-HP player in the design's at-level reference
gear) it is the lowest player level whose single-fight win chance is
~90% (accepted at >= 85%). Ground monsters are fought as a warrior
(melee — must eat the crossing blow and every counter); flying ones as
an archer (melee cannot touch them). The fight model mirrors
engine/combat.py: player strikes first, damage rolls uniform in
[stat/2, stat], chip floor ceil(raw/4), armor/resist tier multipliers,
dodge from speed advantage, the range ladder for bows.
"""

from __future__ import annotations

import json
import os
import random
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _HERE)
from app.gamepath import ensure_game_importable  # noqa: E402

ensure_game_importable()

from plugin_linear_ascent import economy as eco               # noqa: E402
from plugin_linear_ascent.content import schema               # noqa: E402

RNG = random.Random(0x5EED)
FIGHTS_PER_DAY = round(24 * 60 / eco.ENERGY_REGEN_MIN)        # sustained
WIN_TARGET = 0.90
WIN_ACCEPT = 0.85          # 90% ± 5 — the plan's tolerance
SCAN_SIMS = 500
CONFIRM_SIMS = 1500
MAX_ROUNDS = 400           # a fight longer than this counts as a loss


# ── the fight model (mirror of engine/combat.py, no consumables) ─────────

def _player(level: int) -> tuple[int, int, int]:
    """(ATK, DEF, HP) of the design's at-level reference player."""
    lvl = min(level, eco.LEVEL_CAP)
    atk, dfs = eco._at_level_loadout(lvl)
    return atk, dfs, eco.reference_player_hp(lvl)


def _monster(floor: int, traits) -> tuple[int, int, int, dict]:
    """Common-specimen stats + defense profile, bulwark included."""
    atk, dfs, hp = eco.creature_stats(floor, traits)
    prof = eco.profile_from_traits(traits)
    if prof.get("bulwark"):
        hp = round(hp * eco.BULWARK_HP_MULT)
    return atk, dfs, hp, prof


def _monster_blow(m_atk: int, p_def: int, halved: bool) -> int:
    raw = RNG.randint(m_atk // 2, m_atk)
    chip = max(1, -(-raw // eco.CHIP_DIVISOR))
    dmg = max(chip, raw - p_def // 2)
    return dmg // 2 if halved else dmg


def _traced_fight(level: int, floor: int, traits):
    """One fight, attack every round. (won, rounds, player HP lost)."""
    p_atk, p_def, p_hp = _player(level)
    hp0 = p_hp
    m_atk, m_def, m_hp, prof = _monster(floor, traits)
    mspd = prof["speed"]
    dodge = eco.dodge_pct(eco.PLAYER_BASE_SPEED, mspd)
    ranged = bool(prof.get("flying"))          # archer vs flyers
    dtype = "ranged" if ranged else "melee"
    gap, at_range, rounds = 1, True, 0
    while rounds < MAX_ROUNDS:
        rounds += 1
        if at_range and not ranged:
            # melee "attack" at range is the crossing: no damage dealt,
            # one halved blow taken (dodge still applies).
            at_range = False
            if not (dodge and RNG.random() < dodge / 100):
                p_hp -= _monster_blow(m_atk, p_def, halved=True)
            if p_hp <= 0:
                return 0, rounds, hp0
            continue
        mult = ((eco.bow_gap_mult(gap) if at_range else eco.BOW_CLOSE_MULT)
                if ranged else 1.0)
        raw = RNG.randint(p_atk // 2, p_atk)
        m_hp -= eco.typed_damage(dtype, round(raw * mult), m_def, prof)
        if m_hp <= 0:
            return 1, rounds, hp0 - p_hp       # no counter on the kill
        if at_range:                           # the gap is armor
            if RNG.random() < eco.p_close(mspd, eco.PLAYER_BASE_SPEED):
                gap -= 1
                if gap <= 0:
                    at_range = False
            continue
        if not (dodge and RNG.random() < dodge / 100):
            p_hp -= _monster_blow(m_atk, p_def, halved=False)
        if p_hp <= 0:
            return 0, rounds, hp0
    return 0, rounds, hp0 - max(p_hp, 0)


def win_rate(level: int, floor: int, traits, sims: int) -> float:
    wins = sum(_traced_fight(level, floor, traits)[0] for _ in range(sims))
    return wins / sims


def kill_level(floor: int, traits) -> tuple[int | None, float]:
    """Lowest level with ~90% (>= 85%) win chance, and its rate."""
    lo, hi = 1, eco.LEVEL_CAP
    if win_rate(hi, floor, traits, SCAN_SIMS) < WIN_ACCEPT:
        return None, win_rate(hi, floor, traits, CONFIRM_SIMS)
    while lo < hi:                             # win rate rises with level
        mid = (lo + hi) // 2
        if win_rate(mid, floor, traits, SCAN_SIMS) >= WIN_TARGET:
            hi = mid
        else:
            lo = mid + 1
    lvl = lo
    rate = win_rate(lvl, floor, traits, CONFIRM_SIMS)
    while lvl > 1:                             # the ±5 tolerance walks down
        below = win_rate(lvl - 1, floor, traits, CONFIRM_SIMS)
        if below < WIN_ACCEPT:
            break
        lvl, rate = lvl - 1, below
    while rate < WIN_ACCEPT and lvl < eco.LEVEL_CAP:
        lvl += 1
        rate = win_rate(lvl, floor, traits, CONFIRM_SIMS)
    return lvl, rate


def fight_profile(level: int, floor: int, traits, sims: int = 800):
    """(win rate, avg rounds, avg HP lost) at a given level."""
    wins = rounds_sum = hp_sum = 0
    for _ in range(sims):
        w, r, lost = _traced_fight(level, floor, traits)
        wins += w
        rounds_sum += r
        hp_sum += lost
    return wins / sims, rounds_sum / sims, hp_sum / sims


# ── rewards (averages, common specimen, no fade / luck / race) ──────────

def reward_avgs(floor: int, traits, prof) -> tuple[float, float]:
    threat = eco.kill_reward_mult(floor, traits)
    xp = eco.xp_per_kill(floor) * threat
    gold = (eco.gold_per_kill(floor) * threat
            * eco.profile_gold_mult(prof))
    return xp, gold


def spawn_weights(fl) -> dict[str, float]:
    """Effective pick weights: feeble prey fades past floor 3."""
    out: dict[str, float] = {}
    for e in fl.encounters:
        w = float(e.weight)
        _, bite = eco._archetype(e.traits)
        if bite == "feeble":
            w *= eco.prey_weight_mult(fl.floor)
        out[e.id] = w
    return out


# ── the two tabs ─────────────────────────────────────────────────────────

def build_floors() -> list[dict]:
    floors = []
    for n, fl in sorted(schema.load_floors().items()):
        weights = spawn_weights(fl)
        wsum = sum(weights.values()) or 1.0
        monsters = []
        for e in fl.encounters:
            atk, dfs, hp, prof = _monster(n, e.traits)
            xp, gold = reward_avgs(n, e.traits, prof)
            kl, kl_rate = kill_level(n, e.traits)
            at = fight_profile(kl, n, e.traits) if kl else (0.0, 0.0, 0.0)
            monsters.append({
                "id": e.id, "name": e.name, "kind": e.kind or "native",
                "traits": list(e.traits),
                "note": eco.archetype_note(e.traits),
                "spawnPct": round(100 * weights[e.id] / wsum, 1),
                "atk": atk, "def": dfs, "hp": hp,
                "armor": prof["armor"], "resist": prof["resist"],
                "flying": bool(prof.get("flying")),
                "bulwark": bool(prof.get("bulwark")),
                "speed": prof["speed"],
                "xpAvg": round(xp, 1), "goldAvg": round(gold, 1),
                "killLevel": kl,
                "killPct": round(100 * kl_rate, 1),
                "killRounds": round(at[1], 1),
                "killHpLost": round(at[2], 1),
            })
        wa, wd, wh = eco.warden_stats(n)
        floors.append({
            "floor": n, "tier": fl.tier, "biome": fl.biome,
            "zone": fl.zone, "gateTown": fl.gate_town,
            "monsters": monsters,
            "specimens": {k: {"weight": v["weight"], "hp": v["hp"],
                              "atk": v["atk"], "gold": v["gold"]}
                          for k, v in eco.specimen_table(n).items()},
            "warden": {"name": fl.warden_name, "atk": wa, "def": wd,
                       "hp": wh, "xp": eco.warden_xp(n),
                       "gold": eco.warden_gold(n)},
        })
        print(f"floor {n:3d} done", file=sys.stderr)
    return floors


def _xp_per_day(floor_row: dict) -> float:
    """Average XP per kill on a floor (spawn-weighted) × fights/day."""
    ms = floor_row["monsters"]
    if not ms:
        return 0.0
    avg = sum(m["xpAvg"] * m["spawnPct"] for m in ms) / 100.0
    return avg * FIGHTS_PER_DAY


def build_levels(floors: list[dict]) -> list[dict]:
    by_floor = {f["floor"]: f for f in floors}
    top = max(by_floor)
    out = []
    for lvl in range(1, eco.LEVEL_CAP + 1):
        grind = by_floor[min(lvl, top)]
        per_day = _xp_per_day(grind)
        need = eco.xp_need(lvl)
        atk, dfs = eco._at_level_loadout(lvl)
        out.append({
            "level": lvl,
            "xpNeed": need,
            "trainGold": eco.levelup_gold(lvl),
            "daysToFill": round(need / per_day, 2) if per_day else None,
            "grindFloor": grind["floor"],
            "baseAtk": eco.player_atk(lvl, eco.STARTER_WEAPON.bonus),
            "baseDef": eco.player_def(lvl, 0, 0),
            "baseHp": eco.player_max_hp(lvl),
            "refAtk": atk, "refDef": dfs,
            "refHp": eco.reference_player_hp(lvl),
        })
    return out


def build_gear() -> list[dict]:
    rows = []
    for g in eco.FORGE.values():
        rows.append({
            "slug": g.slug, "name": g.name, "slot": g.slot,
            "line": g.line, "tier": g.tier, "rung": g.rung,
            "bonus": g.bonus, "price": g.price, "speed": g.speed,
            "style": g.style,
            "levelReq": eco.rung_player_level_req(g),
            "floorReq": eco.rung_floor_req(g),
        })
    rows.sort(key=lambda r: (r["slot"], r["line"], r["tier"],
                             r["rung"], r["style"]))
    return rows


def build_shops() -> dict:
    return {
        "apothecary": [{"slug": i.slug, "name": i.name, "price": i.price,
                        "effect": i.effect, "note": i.note}
                       for i in eco.APOTHECARY.values()],
        "relics": [{"slug": r.slug, "name": r.name, "di": r.di}
                   for r in eco.RELICS.values()],
        "honePricePct": eco.HONE_PRICE_PCT,
        "repairPricePct": eco.REPAIR_PRICE_PCT,
        "offClassPriceMult": eco.OFF_CLASS_PRICE_MULT,
        "arrowPack": {"size": eco.ARROW_PACK_SIZE,
                      "price": eco.ARROW_PACK_PRICE},
    }


def build_constants() -> dict:
    return {
        "levelCap": eco.LEVEL_CAP,
        "playerSpeed": eco.PLAYER_BASE_SPEED,
        "chipDivisor": eco.CHIP_DIVISOR,
        "tierMult": eco.TIER_MULT,
        "bowGapMult": eco.BOW_GAP_MULT,
        "bowCloseMult": eco.BOW_CLOSE_MULT,
        "bulwarkHpMult": eco.BULWARK_HP_MULT,
        "fightsPerDay": FIGHTS_PER_DAY,
        "energyRegenMin": eco.ENERGY_REGEN_MIN,
        "costWildsFight": eco.COST_WILDS_FIGHT,
        "xpJitterPct": 25, "goldJitterPct": 50,
        "starterWeaponBonus": eco.STARTER_WEAPON.bonus,
        "winTargetPct": round(100 * WIN_TARGET),
        "winAcceptPct": round(100 * WIN_ACCEPT),
        "dailyIncome": {f: eco.daily_income(f) for f in range(1, 101)},
    }


def main() -> None:
    floors = build_floors()
    data = {
        "constants": build_constants(),
        "floors": floors,
        "levels": build_levels(floors),
        "gear": build_gear(),
        "shops": build_shops(),
    }
    out = os.path.join(_HERE, "static", "site", "mechanics-data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("// generated by tools/gen_mechanics.py — do not edit\n")
        f.write("window.MECH = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")
    kb = os.path.getsize(out) / 1024
    n_mon = sum(len(f["monsters"]) for f in floors)
    print(f"wrote {out} ({kb:.0f} KB, {len(floors)} floors, "
          f"{n_mon} monsters)")


if __name__ == "__main__":
    main()
