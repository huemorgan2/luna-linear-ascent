#!/usr/bin/env python3
"""Vendor KayKit CC0 assets (characters, weapons, buildings) for the mock.

Fetches .gltf files plus whatever .bin/.png they reference, and the
self-contained character .glb files, into assets/.
"""

import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "assets"

ADV = ("https://raw.githubusercontent.com/KayKit-Game-Assets/"
       "KayKit-Character-Pack-Adventures-1.0/main/"
       "addons/kaykit_character_pack_adventures")
HEX = ("https://raw.githubusercontent.com/KayKit-Game-Assets/"
       "KayKit-Medieval-Hexagon-Pack-1.0/main/"
       "addons/kaykit_medieval_hexagon_pack")

CHARACTERS = ["Knight", "Barbarian", "Mage", "Rogue", "Rogue_Hooded"]
WEAPONS = ["sword_1handed", "axe_2handed", "axe_1handed", "staff",
           "crossbow_1handed", "dagger", "wand", "shield_round"]
BUILDINGS = ["building_tavern_blue", "building_castle_blue",
             "building_blacksmith_blue", "building_church_blue",
             "building_home_A_blue", "building_home_B_blue",
             "building_market_blue", "building_well_blue",
             "building_windmill_blue", "building_tower_A_blue"]


def get(url: str, dest: Path) -> bytes:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest.read_bytes()
    data = urllib.request.urlopen(url, timeout=60).read()
    dest.write_bytes(data)
    print(f"  {dest.relative_to(HERE)}  {len(data)//1024} KB")
    return data


def get_gltf(base_url: str, name: str, sub: Path) -> None:
    data = get(f"{base_url}/{name}.gltf", OUT / sub / f"{name}.gltf")
    doc = json.loads(data)
    uris = {b["uri"] for b in doc.get("buffers", []) if "uri" in b}
    uris |= {i["uri"] for i in doc.get("images", []) if "uri" in i}
    for u in uris:
        if u.startswith("data:"):
            continue
        get(f"{base_url}/{u}", OUT / sub / u)


print("characters (glb, self-contained):")
for c in CHARACTERS:
    get(f"{ADV}/Characters/gltf/{c}.glb", OUT / "characters" / f"{c}.glb")

print("weapons:")
for w in WEAPONS:
    get_gltf(f"{ADV}/Assets/gltf", w, Path("weapons"))

print("buildings:")
for b in BUILDINGS:
    get_gltf(f"{HEX}/Assets/gltf/buildings/blue", b, Path("buildings"))

print("done")
