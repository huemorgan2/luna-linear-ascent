"""Generate /mechanics page data from the real game numbers.

Reads plugin_linear_ascent.economy + the floor YAML (same import path
worldd itself uses) and writes static/site/mechanics-data.js — the
data file the unlinked /mechanics page renders. Run it whenever balance
changes:

    .venv/bin/python tools/gen_mechanics.py

The Kill Bar column is Monte-Carlo'd here, offline: for each monster
(common specimen, full-HP player) it is the lowest BAR — the design's
reference loadout of floor B: level min(B, 30), floor-B gear — whose
single-fight win chance is ~90% (accepted at >= 85%). Bars run 1–101;
past level cap 30 the ladder climbs by steel alone (043). Ground
monsters are fought as a warrior
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

def _player(bar: int) -> tuple[int, int, int]:
    """(ATK, DEF, HP) of the bar's reference player: level min(bar, 30)
    in floor-`bar` reference gear — _at_level_loadout caps the level
    itself, so past 30 the loadout keeps climbing by steel."""
    atk, dfs = eco._at_level_loadout(bar)
    return atk, dfs, eco.reference_player_hp(bar)


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


def _traced_fight(bar: int, floor: int, traits, dtype: str = "melee"):
    """One fight, attack every round. (won, rounds, player HP lost)."""
    p_atk, p_def, p_hp = _player(bar)
    hp0 = p_hp
    m_atk, m_def, m_hp, prof = _monster(floor, traits)
    mspd = prof["speed"]
    dodge = eco.dodge_pct(eco.PLAYER_BASE_SPEED, mspd)
    ranged = dtype == "ranged"                 # archer flow; magic fights
    #                                            like melee, typed magic
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


def win_rate(bar: int, floor: int, traits, sims: int,
             dtype: str = "melee") -> float:
    wins = sum(_traced_fight(bar, floor, traits, dtype)[0]
               for _ in range(sims))
    return wins / sims


def _kill_bar_typed(floor: int, traits,
                    dtype: str) -> tuple[int | None, float]:
    lo, hi = 1, eco.BAR_MAX
    if win_rate(hi, floor, traits, SCAN_SIMS, dtype) < WIN_ACCEPT:
        return None, win_rate(hi, floor, traits, CONFIRM_SIMS, dtype)
    while lo < hi:                             # win rate rises with the bar
        mid = (lo + hi) // 2
        if win_rate(mid, floor, traits, SCAN_SIMS, dtype) >= WIN_TARGET:
            hi = mid
        else:
            lo = mid + 1
    bar = lo
    rate = win_rate(bar, floor, traits, CONFIRM_SIMS, dtype)
    while bar > 1:                             # the ±5 tolerance walks down
        below = win_rate(bar - 1, floor, traits, CONFIRM_SIMS, dtype)
        if below < WIN_ACCEPT:
            break
        bar, rate = bar - 1, below
    while rate < WIN_ACCEPT and bar < eco.BAR_MAX:
        bar += 1
        rate = win_rate(bar, floor, traits, CONFIRM_SIMS, dtype)
    return bar, rate


def kill_bar(floor: int, traits) -> tuple[int | None, float, str]:
    """Lowest bar with ~90% (>= 85%) win chance, its rate, and the
    damage type that gets it — the class the creature does NOT counter:
    physical (bow for flyers, blade otherwise) unless armor halves
    physical harder than resist halves magic, then the staff. Magic is
    never the headline against an unarmored shape even though it would
    shave the DEF axis — the ladder is read through the fair class."""
    prof = eco.profile_from_traits(traits)
    physical = "ranged" if prof.get("flying") else "melee"
    phys_mult = eco.TIER_MULT.get(prof["armor"], 1.0)
    magic_mult = eco.TIER_MULT.get(prof["resist"], 1.0)
    dtypes = ((physical, "magic") if phys_mult >= magic_mult
              else ("magic", physical))
    best = (None, 0.0, dtypes[0])
    for dtype in dtypes:
        bar, rate = _kill_bar_typed(floor, traits, dtype)
        if bar is not None:
            return bar, rate, dtype            # the fair class first
        if rate > best[1]:
            best = (None, rate, dtype)
    return best


def fight_profile(bar: int, floor: int, traits, sims: int = 800,
                  dtype: str = "melee"):
    """(win rate, avg rounds, avg HP lost) at a given bar."""
    wins = rounds_sum = hp_sum = 0
    for _ in range(sims):
        w, r, lost = _traced_fight(bar, floor, traits, dtype)
        wins += w
        rounds_sum += r
        hp_sum += lost
    return wins / sims, rounds_sum / sims, hp_sum / sims


# ── rewards (averages, common specimen, no fade / luck / race) ──────────

def reward_avgs(floor: int, traits, prof) -> tuple[float, float]:
    """043: pay keys off the creature's bar — no threat multiplier."""
    bar = eco.creature_bar(floor, traits)
    xp = eco.xp_per_kill(bar)
    gold = eco.gold_per_kill(bar) * eco.profile_gold_mult(prof)
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
            kl, kl_rate, kl_type = kill_bar(n, e.traits)
            at = (fight_profile(kl, n, e.traits, dtype=kl_type)
                  if kl else (0.0, 0.0, 0.0))
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
                "targetBar": eco.creature_bar(n, e.traits),
                "killLevel": kl,
                "killType": kl_type,
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


def build_bars() -> list[dict]:
    """043: the 1–101 ladder the simulator climbs — per bar, the
    reference player (level min(bar, 30), floor-bar steel) and the
    starter-gear body at the same level."""
    out = []
    for b in range(1, eco.BAR_MAX + 1):
        atk, dfs = eco._at_level_loadout(b)
        lvl = eco.reference_level(b)
        out.append({
            "bar": b, "level": lvl,
            "refAtk": atk, "refDef": dfs,
            "refHp": eco.reference_player_hp(b),
            "baseAtk": eco.player_atk(lvl, eco.STARTER_WEAPON.bonus),
            "baseDef": eco.player_def(lvl, 0, 0),
            "baseHp": eco.player_max_hp(lvl),
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
        "barMax": eco.BAR_MAX,
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
        "bars": build_bars(),
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
