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
past level cap 30 the ladder climbs by steel alone (043). 048: the
weapon decides — each monster is fought by the PATH its type does not
counter (bow vs fly, staff vs armoured, blade otherwise) with rank-6
reference hands (the migration default). The fight model mirrors
engine/combat.py: player strikes first, the trained hand sets the miss
chance and the floor of the roll band (TRAIN_MISS_PCT /
TRAIN_ROLL_FLOOR), chip floor ceil(raw/4), the TYPE_MULT triangle,
dodge from speed advantage, the range ladder for bows (the gap>1 draw
bonus only for rank-8 hands).
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
REF_RANK = 6               # the reference climber's trained rank (048
#                            phase 6: the migration default)
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


def _traced_fight(bar: int, floor: int, traits, path: str = "blade",
                  rank: int = REF_RANK):
    """One fight, attack every round. (won, rounds, player HP lost)."""
    p_atk, p_def, p_hp = _player(bar)
    hp0 = p_hp
    m_atk, m_def, m_hp, prof = _monster(floor, traits)
    mtype = prof["type"]
    if path == "blade" and mtype == "fly":
        return 0, 1, 0                         # steel can never reach it
    mspd = prof["speed"]
    dodge = eco.dodge_pct(eco.PLAYER_BASE_SPEED, mspd)
    ranged = path == "bow"                     # staff fights like melee,
    #                                            typed through the triangle
    miss = eco.TRAIN_MISS_PCT(rank) / 100
    roll_lo = round(eco.TRAIN_ROLL_FLOOR(rank) * p_atk)
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
        if miss and RNG.random() < miss:       # the untrained hand
            dmg = 0                            # swings wide; the round is
        else:                                  # spent, the counter lands
            mult = 1.0
            if ranged:
                mult = (eco.bow_gap_mult(gap) if at_range
                        else eco.BOW_CLOSE_MULT)
                if mult > 1 and rank < eco.GAP_DRAW_RANK:
                    mult = 1.0                 # the draw pays rank-8 hands
            raw = RNG.randint(roll_lo, p_atk)
            dmg = eco.typed_damage_048(path, round(raw * mult),
                                       m_def, mtype)
        m_hp -= dmg
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
             path: str = "blade") -> float:
    wins = sum(_traced_fight(bar, floor, traits, path)[0]
               for _ in range(sims))
    return wins / sims


def _kill_bar_typed(floor: int, traits,
                    path: str) -> tuple[int | None, float]:
    lo, hi = 1, eco.BAR_MAX
    if win_rate(hi, floor, traits, SCAN_SIMS, path) < WIN_ACCEPT:
        return None, win_rate(hi, floor, traits, CONFIRM_SIMS, path)
    while lo < hi:                             # win rate rises with the bar
        mid = (lo + hi) // 2
        if win_rate(mid, floor, traits, SCAN_SIMS, path) >= WIN_TARGET:
            hi = mid
        else:
            lo = mid + 1
    bar = lo
    rate = win_rate(bar, floor, traits, CONFIRM_SIMS, path)
    while bar > 1:                             # the ±5 tolerance walks down
        below = win_rate(bar - 1, floor, traits, CONFIRM_SIMS, path)
        if below < WIN_ACCEPT:
            break
        bar, rate = bar - 1, below
    while rate < WIN_ACCEPT and bar < eco.BAR_MAX:
        bar += 1
        rate = win_rate(bar, floor, traits, CONFIRM_SIMS, path)
    return bar, rate


def avg_hits(hp: int, m_def: int, prof: dict, bar: int) -> dict:
    """Attacks to kill for the bar's reference player on each path, at
    REF_RANK hands' mean swing (mirrors combat's _pred_damage; misses
    not counted). The bow is read at gap 1 — the kiting shot, ×1.0.
    None = the path cannot land at all (blade vs a flyer)."""
    p_atk, _ = eco._at_level_loadout(bar)
    raw = round((round(eco.TRAIN_ROLL_FLOOR(REF_RANK) * p_atk)
                 + p_atk) / 2)
    out = {}
    for path in ("blade", "bow", "staff"):
        if path == "blade" and prof["type"] == "fly":
            out["hits_" + path] = None
            continue
        dmg = eco.typed_damage_048(path, raw, m_def, prof["type"])
        out["hits_" + path] = None if dmg <= 0 else -(-hp // dmg)
    return out


# 048: the fair path per type — the full answer first, then the best
# half. Blade is the headline against plain (the melee default).
FAIR_PATHS = {
    "fly": ("bow", "staff"),
    "armoured": ("staff", "blade"),
    "magic_resist": ("blade", "bow"),
    "plain": ("blade",),
}


def kill_bar(floor: int, traits) -> tuple[int | None, float, str]:
    """Lowest bar with ~90% (>= 85%) win chance, its rate, and the
    weapon path that gets it — the path the creature's type does NOT
    counter (the ×1.0 cell of the triangle), falling back to the best
    half-answer if even the fair path cannot get there."""
    prof = eco.profile_from_traits(traits)
    paths = FAIR_PATHS[prof["type"]]
    best = (None, 0.0, paths[0])
    for path in paths:
        bar, rate = _kill_bar_typed(floor, traits, path)
        if bar is not None:
            return bar, rate, path             # the fair path first
        if rate > best[1]:
            best = (None, rate, path)
    return best


def fight_profile(bar: int, floor: int, traits, sims: int = 800,
                  path: str = "blade"):
    """(win rate, avg rounds, avg HP lost) at a given bar."""
    wins = rounds_sum = hp_sum = 0
    for _ in range(sims):
        w, r, lost = _traced_fight(bar, floor, traits, path)
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
            hits = avg_hits(hp, dfs, prof, eco.creature_bar(n, e.traits))
            kl, kl_rate, kl_type = kill_bar(n, e.traits)
            at = (fight_profile(kl, n, e.traits, path=kl_type)
                  if kl else (0.0, 0.0, 0.0))
            monsters.append({
                "id": e.id, "name": e.name, "kind": e.kind or "native",
                "traits": list(e.traits),
                "note": eco.archetype_note(e.traits),
                "spawnPct": round(100 * weights[e.id] / wsum, 1),
                "atk": atk, "def": dfs, "hp": hp,
                "type": prof["type"],
                "flying": bool(prof.get("flying")),
                "bulwark": bool(prof.get("bulwark")),
                "speed": prof["speed"],
                "xpAvg": round(xp, 1), "goldAvg": round(gold, 1),
                "hitsBlade": hits["hits_blade"],
                "hitsBow": hits["hits_bow"],
                "hitsStaff": hits["hits_staff"],
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
            "baseDef": eco.player_def(lvl, eco.GATE_SHIELD.bonus,
                                      eco.GATE_ARMOR.bonus),
            "baseHp": eco.player_max_hp(lvl, eco.GATE_ARMOR.bonus),
            "refAtk": atk, "refDef": dfs,
            "refHp": eco.reference_player_hp(lvl),
        })
    return out


def build_bars() -> list[dict]:
    """043: the 1–101 ladder the simulator climbs — per bar, the
    reference player (level min(bar, 30), floor-bar steel) and the
    gate-issue body at the same level (starter weapon + the free
    buckler/jerkin every character carries from creation)."""
    out = []
    for b in range(1, eco.BAR_MAX + 1):
        atk, dfs = eco._at_level_loadout(b)
        lvl = eco.reference_level(b)
        out.append({
            "bar": b, "level": lvl,
            "refAtk": atk, "refDef": dfs,
            "refHp": eco.reference_player_hp(b),
            "baseAtk": eco.player_atk(lvl, eco.STARTER_WEAPON.bonus),
            "baseDef": eco.player_def(lvl, eco.GATE_SHIELD.bonus,
                                      eco.GATE_ARMOR.bonus),
            "baseHp": eco.player_max_hp(lvl, eco.GATE_ARMOR.bonus),
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
        # 048: the off-class weapon tax died with the classes — the
        # trained rank is the only tax on a weapon.
        "arrowPack": {"size": eco.ARROW_PACK_SIZE,
                      "price": eco.ARROW_PACK_PRICE},
    }


def _fit_level(xp: int) -> int:
    """The lowest body level whose bar holds `xp` — the fits-the-bar
    law: an XP price is honest only if one level's hard bar can pay it
    (048 phase 6)."""
    lvl = 1
    while eco.xp_need(lvl) < xp and lvl < eco.LEVEL_CAP:
        lvl += 1
    return lvl


def build_training() -> dict:
    """The School's ledger — rank costs, the hand's curves, the gate
    table, and the merchandise (048)."""
    ranks = []
    cum = 0
    for r in range(1, 11):
        xp = eco.train_xp(r)
        cum += xp
        ranks.append({
            "rank": r, "xp": xp, "cumXp": cum,
            "gold10": eco.train_gold(r, 10),
            "gold30": eco.train_gold(r, 30),
            "missPct": eco.TRAIN_MISS_PCT(r),
            "rollFloorPct": round(100 * eco.TRAIN_ROLL_FLOOR(r)),
            "fitLevel": _fit_level(xp),
            "fitXpNeed": eco.xp_need(_fit_level(xp)),
        })
    return {
        "ranks": ranks,
        "missPct0": eco.TRAIN_MISS_PCT(0),
        "rollFloorPct0": round(100 * eco.TRAIN_ROLL_FLOOR(0)),
        "gates": [
            {"path": "blade", "name": "shield wall",
             "rank": eco.WALL_RANK},
            {"path": "bow", "name": "shot from cover",
             "rank": eco.TREELINE_RANK},
            {"path": "bow", "name": "give ground",
             "rank": eco.GAP_OPEN_RANK},
            {"path": "bow", "name": "the open-gap draw pays",
             "rank": eco.GAP_DRAW_RANK},
            {"path": "staff", "name": "the lullaby",
             "rank": eco.SLEEP_RANK},
        ],
        "merch": [
            {"name": "2nd weapon slot (CARRY)", "xp": eco.CARRY2_XP,
             "gold": eco.CARRY2_GOLD, "level": 1,
             "fitLevel": _fit_level(eco.CARRY2_XP)},
            # 049.1: the level gate is gone — the 500-XP price is the
            # gate (the bar itself can't hold it before ~level 8).
            {"name": "3rd weapon slot (CARRY)", "xp": eco.CARRY3_XP,
             "gold": None, "goldAnchor": eco.CARRY3_GOLD_ANCHOR,
             "level": 1,
             "fitLevel": _fit_level(eco.CARRY3_XP)},
            {"name": "mastery study (at rank 10)", "xp": eco.MASTERY_XP,
             "gold": None, "level": None,
             "fitLevel": _fit_level(eco.MASTERY_XP)},
        ],
        "masteryDiscount": eco.MASTERY_DISCOUNT,
        "masteryDiscountMaxRank": eco.MASTERY_DISCOUNT_MAX_RANK,
        "masteryTeeth": {
            "riposteReturn": eco.RIPOSTE_RETURN,
            "longDrawCritMult": eco.LONG_DRAW_CRIT_MULT,
            "longDrawTop": eco.LONG_DRAW_TOP,
            "focusMult": eco.FOCUS_MULT,
        },
    }


def build_constants() -> dict:
    return {
        "levelCap": eco.LEVEL_CAP,
        "barMax": eco.BAR_MAX,
        "playerSpeed": eco.PLAYER_BASE_SPEED,
        "chipDivisor": eco.CHIP_DIVISOR,
        "typeMult": eco.TYPE_MULT,
        "typeSpeed": eco.TYPE_SPEED,
        "refRank": REF_RANK,
        "gapDrawRank": eco.GAP_DRAW_RANK,
        "trainMissPct": [eco.TRAIN_MISS_PCT(r) for r in range(11)],
        "trainRollFloor": [eco.TRAIN_ROLL_FLOOR(r) for r in range(11)],
        "earlyCoinFloors": eco.EARLY_COIN_FLOORS,
        "earlyCoinMult": {f: eco.early_coin_mult(f)
                          for f in range(1, eco.EARLY_COIN_FLOORS + 1)},
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
        "training": build_training(),
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
