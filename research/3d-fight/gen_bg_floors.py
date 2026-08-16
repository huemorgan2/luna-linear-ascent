#!/usr/bin/env python3
"""Fight-scene backgrounds for floors 2–6 (+ the six wardens' stair-gates).

Same pipeline as demo2/gen_backgrounds.py (floor 1): Gemini paints a
designed 1-bit still at 21:9 → density master at 320x112 → perfect-loop
GIF (wind + glow), then make_bg_sheets.py bakes every GIF here into the
GL sprite sheet fight3d.js samples. One scene per creature id, prompted
from the floor's arrival text and the encounter's prose.

Usage:
  python3 gen_bg_floors.py stills [id ...]   # Gemini, skips existing jpgs
  python3 gen_bg_floors.py gifs   [id ...]   # local, rebuilds
"""
from __future__ import annotations

import asyncio
import importlib.util
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "demo2"))
_ROOT = os.path.join(_HERE, "..", "..")
_PROV = os.path.join(_ROOT, "..", "luna-plugins", "plugins",
                     "plugin-image-gen", "plugin_image_gen", "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _PROV)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

# demo2's module imports providers from an old path at load time — give
# it ours first, then borrow its style + post pipeline unchanged.
import gen_backgrounds as g1  # noqa: E402

OUT = os.path.join(_HERE, "backgrounds_floors")
g1.OUT = OUT
STYLE, STAGE = g1.STYLE, g1.STAGE

FLOOR = {
    2: ("Setting: floor two of the tower — The Rustwater Adit, a giants' "
        "mine. A flooded drift of orange rustwater, iron rails, timber "
        "props, ore carts, mine lamps on hooks, the roof lost in dark. "),
    3: ("Setting: floor three — The Drowned Pasture. Grey floodwater "
        "over meadowland, hay-ricks standing in the water, drowned "
        "fence lines, a mill and weir behind, mist over the water. "),
    4: ("Setting: floor four — The Lightless Glade, an elven wood gone "
        "black. Tall dark trunks, hanging branches, one cold pale glow "
        "somewhere in the trees, no sky, deep dark. "),
    5: ("Setting: floor five — The Flooded Mine, giants' galleries "
        "waist-deep in black water. Rusted hoists, pump pipes, dead "
        "lamps, iron walkways, water dead-flat and black. "),
    6: ("Setting: floor six — The Threshold Dark, a deep cave beyond "
        "the last lamps. Rough rock, hanging silk threads, guano "
        "mounds, a distant stair arch, one small lamp glow. "),
    7: ("Setting: floor seven — The Rotting Orchard. Mile on mile of "
        "planted apple rows gone to rot under tower floodlights, the "
        "ground deep in windfall, cider presses, wasps hanging in a "
        "sweet haze, bare pruned trunks in straight rows. "),
    8: ("Setting: floor eight — The Ash Dunes, the burned frontier. "
        "Grey ash dunes to the horizon, wind moving ash in slow sheets, "
        "glass-crusted flats, hard floodlight glare, no water. "),
}
GATE = ("The floor's stair-gate: a riveted iron gate and stair-lift "
        "machinery behind the fighting floor, stairs rising into "
        "darkness, two lamp cones from the gate towers pooling on the "
        "ground. ")

def sc(floor, wind, fire, prompt):
    return dict(floor=floor, wind=wind, fire=fire, prompt=prompt)

SCENES = {
    # floor 2
    "marsh_wolf": sc(2, 0.6, False, "Mine rails run along the drift behind the fighting floor, an ore cart tipped, a lamp on a timber prop pooling light."),
    "cave_cricket": sc(2, 0.4, False, "A low rock roof close overhead behind the fighting floor, timber props, a heap of stripped leather and rope, dust drifting in one lamp beam."),
    "shellback_tortoise": sc(2, 0.5, False, "Orange rustwater flooding the drift behind the fighting floor, rails vanishing under it, a lamp glow reflected in the water."),
    "kobold_digger": sc(2, 0.4, True, "A dig face at the end of a drift behind the fighting floor, mattocks and buckets, a small brazier burning with a glow ramp, chains on the wall."),
    "orc_overseer": sc(2, 0.5, True, "An overseer's post in the mine behind the fighting floor: a wooden platform, a hanging whip, a brazier, ore carts in a row."),
    "rust_seep": sc(2, 0.3, False, "A drift wall eaten smooth behind the fighting floor, orange stain climbing the rock, water running the wrong way, one lamp."),
    "warden_002": sc(2, 0.5, False, GATE + "The gate stands in the flooded main drift, rails leading into it, rustwater around its foot."),
    # floor 3
    "sluice_wolf": sc(3, 1.5, False, "Grey floodwater over pasture behind the fighting floor, two hay-ricks standing in the water, drowned fence posts, mist."),
    "reed_adder": sc(3, 1.8, False, "A bank of tall sedge and reeds behind the fighting floor, shallow water in slow curves, a distant weir."),
    "mire_boar": sc(3, 1.4, False, "A torn reed-bank and churned mud behind the fighting floor, floodwater beyond, a drowned gate."),
    "wire_eel": sc(3, 1.0, False, "Drowned fence lines with barbed wire trailing into flat grey water behind the fighting floor, a punt half-sunk, mist."),
    "windfall_haunt": sc(3, 1.2, True, "Flat black floodwater behind the fighting floor, a lone cold lantern glow hanging over it, drowned trees, thick mist."),
    "warden_003": sc(3, 1.3, False, GATE + "The gate stands beside a mill-pool and weir, water sheeting over the weir stones."),
    # floor 4
    "glade_stag": sc(4, 1.0, False, "Tall black tree trunks behind the fighting floor, bare ground, a single cold pale glow far back between the trees."),
    "dusk_hare": sc(4, 1.2, False, "A dark glade floor with low black brambles behind the fighting floor, trunks around, one faint glow low in the brush."),
    "glare_moth": sc(4, 0.8, True, "A lamp post with a guttering lamp behind the fighting floor, moths of light around it, black trunks beyond."),
    "wick_owl": sc(4, 1.1, False, "Huge branches arching low overhead behind the fighting floor, black trunks, a faint glow deep in the wood."),
    "lamp_eater": sc(4, 0.7, True, "A dying campfire behind the fighting floor, its glow ramp swallowed by black lichen crawling on the trunks around."),
    "lamptree_wight": sc(4, 1.6, True, "A treeline of snarled black branches behind the fighting floor, a cold false glow lit from inside the branches."),
    "warden_004": sc(4, 1.0, True, GATE + "The gate stands in the black glade under a welded lamp cage throwing hard blue-white glare."),
    # floor 5
    "blind_shoal": sc(5, 0.4, False, "A flooded gallery behind the fighting floor, black water dead-flat, iron pump pipes along the wall, one lamp."),
    "drift_eel": sc(5, 0.4, False, "A sump pool behind the fighting floor, black water, a rusted hoist cable dropping into it, dead lamps on hooks."),
    "downs_courser": sc(5, 0.5, False, "A long dry gallery behind the fighting floor, iron walkway, message-route markers painted on the wall, lamps in a row."),
    "coolant_crab": sc(5, 0.4, False, "A flooded drift behind the fighting floor, black water to the walls, a wrecked pump, pale light from one lamp."),
    "bailer_kobold": sc(5, 0.4, True, "A bilge pool behind the fighting floor, bailing buckets on ropes, a brazier on an iron stand with a glow ramp."),
    "miner_husk": sc(5, 0.5, False, "A flooded shift-gallery behind the fighting floor, a row of dead miner's lamps, water to the walls, hoist chains."),
    "warden_005": sc(5, 0.5, False, GATE + "The gate stands in a flooded gallery, a great pump valve beside it, water jetting from a pipe."),
    # floor 6
    "grave_moth": sc(6, 0.5, False, "A rough cave with a soft guano floor behind the fighting floor, silk threads hanging, one small lamp glow."),
    "guano_vole": sc(6, 0.4, False, "A low cave floor humped with soft mounds behind the fighting floor, rock roof, a faint lamp."),
    "silk_broodling": sc(6, 0.9, False, "Silk threads hanging from a cave roof behind the fighting floor, cocoons, dark rock, a faint lamp glow."),
    "vault_weaver": sc(6, 0.7, False, "A vaulted cave behind the fighting floor, thick webs across the roof, eight-fold pattern of threads, one lamp."),
    "lane_boar": sc(6, 0.3, False, "A narrow crawl passage behind the fighting floor, crusted rock walls, a lamp far back down the passage."),
    "wrapped_husk": sc(6, 0.8, False, "A silk-hung cave behind the fighting floor, cocoons shaped like men hanging, one lamp glow."),
    "warden_006": sc(6, 0.9, False, GATE + "The gate arch is webbed shut with steel silk, the roof above alive with threads."),
    # floor 7
    "orchard_wolfpack": sc(7, 1.4, False, "Straight rows of bare pruned apple trunks behind the fighting floor, windfall heaped between them, a floodlight cone through the haze."),
    "rabid_boar": sc(7, 1.2, False, "Broken orchard trees and a smashed cider press behind the fighting floor, windfall churned to pulp, floodlight glare in the haze."),
    "hornet_swarm": sc(7, 1.0, False, "A row of cider presses and barrels behind the fighting floor, windfall carpeting the ground, thin haze, one floodlight."),
    "windfall_crow": sc(7, 1.3, False, "High forked orchard branches arching over the fighting floor, rotting fruit hanging, windfall below, floodlight glow beyond."),
    "orchard_hare": sc(7, 1.5, False, "A long straight orchard row behind the fighting floor vanishing into haze, trunks either side, windfall on the ground."),
    "windfall_wight": sc(7, 1.1, True, "A cider-shed doorway behind the fighting floor, barrels and a hanging lamp with a warm glow ramp, orchard rows beyond in haze."),
    "warden_007": sc(7, 1.3, False, GATE + "The gate stands at the head of the orchard rows, windfall heaped against its foot, presses either side."),
    # floor 8
    "cinder_wolf": sc(8, 2.0, False, "Grey ash dunes rolling behind the fighting floor, wind lifting ash off the crests, hard floodlight glare from above."),
    "dune_hare": sc(8, 2.2, False, "A flat glass-crusted ash pan behind the fighting floor, low dunes beyond, dust sheeting across in the wind."),
    "cinder_salamander": sc(8, 1.2, True, "A warm ash hollow behind the fighting floor, ember glow ramps under the crust, thin smoke, dunes beyond."),
    "cinder_vulture": sc(8, 1.8, False, "A high dune ridge behind the fighting floor, a dead blackened tree with bones at its foot, glare sky."),
    "ash_adder": sc(8, 1.6, False, "Rippled ash dunes close behind the fighting floor, a track poured through the surface, glass shards catching floodlight."),
    "greywell_ogre": sc(8, 1.4, False, "A stone spring-mouth in an ash bowl behind the fighting floor, a dry well ring, dunes and glare beyond."),
    "warden_008": sc(8, 1.5, True, GATE + "The gate stands in an ash bowl before the lift, slag heaps either side, molten glow ramps in the ash."),
    # floor 1's warden — demo2 has a generic gate; give Brackjaw its meadow
    "warden_001": sc(1, 1.4, False, "Setting: floor one — The Fencerows, stolen meadowland under tower floodlights. " + GATE + "The gate stands at the edge of the stair-lift meadow, hedgerows behind."),
}
g1.SCENES = SCENES


async def gen_still(sid: str, key: str) -> str:
    cfg = SCENES[sid]
    floor = FLOOR.get(cfg["floor"], "")
    prompt = (STYLE + floor + STAGE + cfg["prompt"] +
              " Very wide cinematic side-on shot.")
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], prompt, aspect="21:9",
        api_key=key)
    if "error" in res:
        return f"FAIL {sid}: {res['error']} — {str(res.get('detail'))[:160]}"
    open(os.path.join(OUT, f"{sid}.jpg"), "wb").write(res["image_bytes"])
    return f"ok   {sid}"


async def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("stills", "gifs"):
        sys.exit(__doc__)
    mode, names = sys.argv[1], sys.argv[2:]
    os.makedirs(OUT, exist_ok=True)
    bad = [n for n in names if n not in SCENES]
    if bad:
        sys.exit(f"unknown ids: {bad}")
    if mode == "stills":
        key = g1.api_key()
        todo = names or [s for s in SCENES if not os.path.exists(
            os.path.join(OUT, f"{s}.jpg"))]
        print(f"{len(todo)} stills -> {OUT}")
        for i in range(0, len(todo), 4):
            for line in await asyncio.gather(
                    *(gen_still(n, key) for n in todo[i:i + 4])):
                print(line, flush=True)
    else:
        todo = names or [s for s in SCENES if os.path.exists(
            os.path.join(OUT, f"{s}.jpg"))]
        for n in todo:
            print(g1.build_gif(n), flush=True)
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
