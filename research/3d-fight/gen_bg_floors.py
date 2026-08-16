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
    9: ("Setting: floor nine — The Signal Heath at night. Miles of dark "
        "heather under humming aether-pylons and cables, pylon lamps "
        "strobing, knife-edged shadows, one junction box, no moon. "),
    10: ("Setting: floor ten — The Muster Field. A great meadow of "
         "rotting army banners on poles, muster-tents, horse-lines, "
         "broken spears, standards hanging colourless in dead air. "),
    11: ("Setting: floor eleven — The Adit, a dwarf mine mouth in "
         "mountain-root. Timbered adit arch, dwarf lamps still burning, "
         "rust-red water, rails, tailings heaps, cold air. "),
    12: ("Setting: floor twelve — The Drowned Galleries. Dwarf mine "
         "galleries waist-deep in black water, half-running pumps, "
         "pipes, crate rafts, dead-flat black water, few lamps. "),
    13: ("Setting: floor thirteen — The Counting Halls. Halls of brass "
         "and slate, great scales, tally-engines, ledgers, drifts of "
         "coloured scrip paper, brass lamps. "),
    14: ("Setting: floor fourteen — The Gear Halls. Whole halls of "
         "gearing floor to unseen ceiling, huge cogs, belts, flywheels, "
         "half of it slowly turning, oil lamps. "),
    15: ("Setting: floor fifteen — The Core Vaults. Dwarven vaults with "
         "yard-thick doors, cracks of blinding core-glow through the "
         "seams, lead shielding, gauges, the only light from the doors. "),
    16: ("Setting: floor sixteen — The Forge Commons. A hundred family "
         "forges round one great anvil, plasma feeds glowing, smoke, "
         "racks of tools, orc-crude weapons stacked. "),
    17: ("Setting: floor seventeen — The Smelters. Great cold smelters, "
         "black glass slag channels still shimmering with heat, huge "
         "ladles hanging overhead like bells, iron walkways. "),
    18: ("Setting: floor eighteen — The Deep Drifts. The lowest dwarf "
         "drifts, winch-ropes hanging taut down shafts, scarce lamps, "
         "rough rock, deep settled dark. "),
    19: ("Setting: floor nineteen — The Breach. Yard-thick vault doors "
         "blown off their hinges lying where they fell, scorch-marks "
         "three storeys high, rubble, dead lamps. "),
    20: ("Setting: floor twenty — The Warcamp. The last dwarf hall made "
         "an orc warcamp: cookfires in ore carts, warframes racked like "
         "cordwood, a red banner hung from a crane, drums, the lift. "),
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
    # floor 9
    "beacon_moth": sc(9, 1.6, True, "Dark heather behind the fighting floor, a pylon lamp strobing bright with a glow ramp, cables overhead."),
    "moor_hare": sc(9, 1.8, False, "Open moor behind the fighting floor, pylons marching into the dark, knife-edged shadows across the heather."),
    "night_hawk": sc(9, 1.4, True, "A cable-run and junction box behind the fighting floor, one lamp glow, heather, deep dark beyond."),
    "shadow_wolf": sc(9, 1.5, False, "A pylon's hard shadow falling across the heather behind the fighting floor, lamps far off, black sky."),
    "pylon_adder": sc(9, 1.2, True, "A cable-run at ground level behind the fighting floor, blue spark glow ramp at a broken insulator, heather."),
    "flicker_wight": sc(9, 1.0, True, "A junction box on a post behind the fighting floor, its lamp glowing, pylons beyond in the dark."),
    "warden_009": sc(9, 1.6, True, GATE + "The gate stands under a pylon on the heath, its lamps strobing, cables running to it."),
    # floor 10
    "kings_guard": sc(10, 1.2, False, "A rank of rotting banners on poles behind the fighting floor, a muster-tent, broken spears in the ground."),
    "banner_wolf": sc(10, 1.5, False, "A tent-lane behind the fighting floor, sagging tents either side, banners hanging colourless."),
    "courier_hound": sc(10, 1.6, False, "Horse-lines and picket posts behind the fighting floor, banners beyond, churned field."),
    "parade_horse": sc(10, 1.0, False, "Muster-tents behind the fighting floor, a rotted saddle on a rail, standards on poles."),
    "bunting_kite": sc(10, 1.8, False, "Tall banner-poles behind the fighting floor, banners flapping ragged, open field."),
    "muster_wight": sc(10, 1.3, False, "A churned muster field behind the fighting floor, a rotted standard planted, mist low over the mire."),
    "warden_010": sc(10, 1.2, True, GATE + "Before the gate a throne of banner-poles and broken spears, banners either side, one brazier glow."),
    # floor 11
    "kobold_scavenger": sc(11, 0.6, True, "A side-shaft mouth behind the fighting floor, dwarf lamps burning with a glow ramp, coils of stripped copper."),
    "rust_hound": sc(11, 0.5, False, "Rust-red water running along a rail line behind the fighting floor, timber props, one dwarf lamp."),
    "orc_outrider": sc(11, 0.6, False, "A tailings heap behind the fighting floor, the adit arch beyond with lamps, cold mist."),
    "adit_bat": sc(11, 0.8, True, "The adit arch behind the fighting floor, dwarf lamps flickering with glow ramps, dark mine mouth."),
    "warden_011": sc(11, 0.5, False, GATE + "The gate is half buried in a rockfall inside the adit, red water pooling, lamps on the arch."),
    # floor 12
    "bilge_kobold": sc(12, 0.4, False, "A flooded gallery behind the fighting floor, black water, a raft of crate lids, pipes along the wall."),
    "drowned_hauler": sc(12, 0.4, False, "A drowned rail gallery behind the fighting floor, black water to the walls, silt-hung pipes, one lamp."),
    "orc_diver": sc(12, 0.4, False, "A sump pool behind the fighting floor, dwarf-steel salvage stacked, hoses, black water, one lamp."),
    "sump_eel": sc(12, 0.5, False, "Black water folding in a wide gallery behind the fighting floor, pump outflow, dead lamps."),
    "warden_012": sc(12, 0.5, False, GATE + "The gate stands drowned to the knee, pump-iron and weed knotted over it, black water."),
    # floor 13
    "coin_sifter": sc(13, 0.5, True, "Drifts of coloured scrip on a slate floor behind the fighting floor, brass lamps with glow ramps, a counting bench."),
    "tally_engine": sc(13, 0.4, True, "A row of tally-engines on benches behind the fighting floor, bead-frames, brass lamps."),
    "debt_collector": sc(13, 0.4, True, "A long aisle between counting benches behind the fighting floor, tally-marks chalked on the walls, lamps."),
    "ledger_wisp": sc(13, 0.6, True, "The grand ledger open on a lectern behind the fighting floor, dust in lamplight, brass and slate."),
    "scrip_rat": sc(13, 0.5, True, "A drift of scrip paper heaped against a wall behind the fighting floor, a lamp, brass scales."),
    "warden_013": sc(13, 0.5, True, GATE + "The gate stands behind the grand scales, huge weighing pans hanging, brass lamps."),
    # floor 14
    "gear_kobold": sc(14, 0.5, True, "Huge cogs rising into the dark behind the fighting floor, one slowly turning, an oil lamp glow."),
    "loose_flywheel": sc(14, 0.4, False, "A long gallery behind the fighting floor with a worn groove down the floor, gearing along the walls."),
    "pit_fighter": sc(14, 0.5, True, "Two meshing wheels behind the fighting floor, a chalk ring on the floor, a lamp on a post."),
    "belt_runner": sc(14, 0.6, False, "Moving belts and pulleys overhead behind the fighting floor, gearing beyond, one lamp."),
    "warden_014": sc(14, 0.5, True, GATE + "The gate is set into a wall of gearing, huge wheels turning behind it, oil lamps."),
    # floor 15
    "glow_sick_kobold": sc(15, 0.4, True, "A vault door behind the fighting floor, core-glow through its seams with a bright glow ramp, lead shielding."),
    "fuel_thief": sc(15, 0.4, True, "A vault corridor behind the fighting floor, glowing seams of light down the doors, gauges on the walls."),
    "forge_remnant": sc(15, 0.4, True, "A vault-tender's round behind the fighting floor, checklists on the wall, glowing door seams."),
    "rod_wisp": sc(15, 0.5, True, "Two vault doors behind the fighting floor, seam-light between them, the only light there is."),
    "warden_015": sc(15, 0.5, True, GATE + "The gate stands before the brightest vault door, core-glow ramps blazing through the seams."),
    # floor 16
    "orc_armorer": sc(16, 0.7, True, "A stolen forge behind the fighting floor, plasma feed glowing, an anvil, racks of pauldrons."),
    "hammer_kobold": sc(16, 0.6, True, "Family forges in a ring behind the fighting floor, hammers on racks, glow ramps from the feeds."),
    "half_forged": sc(16, 0.7, True, "The great communal anvil behind the fighting floor, glowing forges all round, smoke."),
    "bellows_hound": sc(16, 1.0, True, "Forge smoke rolling behind the fighting floor, glowing feeds through the smoke, bellows."),
    "warden_016": sc(16, 0.7, True, GATE + "The gate stands past the great anvil, forges glowing on either side, smoke."),
    # floor 17
    "slag_rat": sc(17, 0.6, True, "A cooled ladle on its side behind the fighting floor, black glass slag channels shimmering with heat glow."),
    "ladle_crew": sc(17, 0.6, True, "Ladles hanging overhead like bells behind the fighting floor, an iron walkway, glowing slag runs."),
    "smelter_boss": sc(17, 0.6, True, "A great cold smelter behind the fighting floor, tapping-hole glowing, slag channels."),
    "heat_haunt": sc(17, 0.8, True, "Heat shimmer over a slag channel behind the fighting floor, black glass, hanging ladles."),
    "warden_017": sc(17, 0.7, True, GATE + "The gate stands past the main slag channel, smoke and heat glow off the black glass."),
    # floor 18
    "blind_digger": sc(18, 0.3, False, "A rough drift behind the fighting floor, one scarce lamp far back, pick marks in the rock."),
    "winch_crawler": sc(18, 0.4, False, "Winch-ropes hanging taut down a shaft behind the fighting floor, a winch mount torn empty, dark."),
    "pit_hound": sc(18, 0.3, False, "A long dark drift behind the fighting floor, rope lines running along it, one lamp."),
    "drift_moth": sc(18, 0.5, True, "A guttering lamp on a drift wall behind the fighting floor, powder in the air, deep dark."),
    "warden_018": sc(18, 0.4, False, GATE + "The gate stands at the last shaft, every winch-rope running to one great drum beside it."),
    # floor 19
    "door_breaker": sc(19, 0.5, False, "Fallen vault doors lying behind the fighting floor, scorch marks climbing the walls, rubble."),
    "powder_kobold": sc(19, 0.5, True, "A stack of powder kegs behind the fighting floor, fuse-cord, a scorched wall, one lamp glow."),
    "doorward_remnant": sc(19, 0.4, False, "An empty doorway with no door behind the fighting floor, the door slab lying beyond, scorched stone."),
    "breach_crow": sc(19, 0.9, False, "A fallen door slab tilted behind the fighting floor, scorched dark above, rubble."),
    "scorch_rat": sc(19, 0.4, False, "The seam of a fallen door behind the fighting floor, old ration crates, scorched rubble."),
    "warden_019": sc(19, 0.5, False, GATE + "The gate stands amid the blown doors, hinge-plates and slabs heaped, scorch three storeys high."),
    # floor 20
    "honor_guard": sc(20, 0.7, True, "Racked warframes in rows behind the fighting floor, a red banner on a crane, cookfire glow ramps."),
    "warframe_champion": sc(20, 0.7, True, "A fighting ring in the warcamp behind the fighting floor, warframes racked, drums, cookfires."),
    "camp_hound": sc(20, 0.6, True, "Kennel chains and a cookfire in an ore cart behind the fighting floor, warframes racked beyond."),
    "drum_kobold": sc(20, 0.6, True, "War-drums on stands behind the fighting floor, a red banner, cookfire glow."),
    "camp_looter": sc(20, 0.6, True, "Rows of racked warframes behind the fighting floor, buckles and gear heaped, a cookfire."),
    "warden_020": sc(20, 0.8, True, GATE + "The gate is the lift itself, the red banner hung above from the dwarves' crane, cookfires either side."),
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
