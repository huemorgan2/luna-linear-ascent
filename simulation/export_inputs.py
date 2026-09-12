"""Freeze public design data + pure economy tables; never read player data.

python3 simulation/export_inputs.py --source /path/to/release-checkout
python3 simulation/export_inputs.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TARGET = HERE / "data" / "inputs.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(data):
    assert len(data["floors"]) == 100
    assert [f["floor"] for f in data["floors"]] == list(range(1, 101))
    assert len(data["upgrades"]) == 84
    assert len(data["model"]["weapons"]) == 16
    assert sum(len(f["monsters"]) for f in data["floors"]) == 425
    assert len({m["id"] for f in data["floors"] for m in f["monsters"]}) == 425
    assert all(0 <= s["level"] <= 20 for s in data["upgrades"])
    assert len(data["economy"]) == 100 and len(data["characters"]) == 30


def export(source):
    source = Path(source).resolve()
    wiki = source / "worldd/static/site/wiki/data.json"
    econ = source / "worldd/vendor/plugin_linear_ascent/economy.py"
    spec = importlib.util.spec_from_file_location("simulation_economy_export", econ)
    e = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = e
    spec.loader.exec_module(e)
    raw = json.loads(wiki.read_text())
    model = raw["model"]
    # Keep small, inspectable game data; art remains in the game asset tree.
    for w in model["weapons"]:
        w.pop("images", None)
    data = {k: raw[k] for k in ("floors", "upgrades", "model")}
    data["source"] = {
        "game_version": raw["gameVersion"], "wiki_revision": raw["revision"],
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip(),
        "files": {str(p.relative_to(source)): digest(p) for p in (wiki, econ)},
        "mode": "Pinned game tables + research proposal; not the production combat resolver",
    }
    data["constants"] = {
        "energy_regen_minutes": e.ENERGY_REGEN_MIN, "energy_base_cap": e.ENERGY_BASE_CAP,
        "level_cap": e.LEVEL_CAP, "pillar": e.PILLAR, "pace_discount": e.PACE_DISCOUNT,
        "warden_rise": e.WARDEN_RISE, "hp_per_armor": e.GEAR_HP_PER_ARMOR,
        "starting_gold": 50, "starting_armor": e.GATE_ARMOR.bonus,
        "starting_shield": e.GATE_SHIELD.bonus, "warden_strike_energy": e.COST_WARDEN_STRIKE,
    }
    data["characters"] = [dict(level=l, atk=e.player_atk(l, 0), defense=e.player_def(l, 0, 0),
        hp=e.player_max_hp(l, 0), xp=e.xp_need(l), gold=e.levelup_gold(l)) for l in range(1, 31)]
    data["economy"] = []
    for f in range(1, 101):
        a, d, h = e.warden_stats(f)
        data["economy"].append(dict(floor=f, armor=e.reference_armor_bonus(f),
            shield=e.honed_bonus(e._reference_bonus(f, "shield"), e.reference_hone(f)),
            defense_step_gold=max(1, round(e.hone_price(f) * 2 / 3)),
            reference_level=e.reference_level(f), heal_full=e.tent_full_price(f),
            gold=e.gold_per_kill(f), xp=e.xp_per_kill(f), energy_cap=e.energy_cap(e.gear_tier_for_floor(f)),
            warden=dict(hp=h, atk=a, defense=d, legacy_shared_hp=e.world_warden_hp(f),
                legacy_regen_hourly=e.world_warden_regen_hourly(f))))
    validate(data)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    return data


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    if args.check:
        data = json.loads(TARGET.read_text())
        validate(data)
        if args.source:
            for rel, expected in data["source"]["files"].items():
                assert digest(args.source / rel) == expected, rel
    elif args.source:
        data = export(args.source)
    else:
        p.error("Use --source RELEASE_CHECKOUT or --check")
    print(f"100 floors / 425 species / 16 families / 84 upgrades; SHA256 {digest(TARGET)}")


if __name__ == "__main__":
    main()
