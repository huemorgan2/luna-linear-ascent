"""Floors 2–20 monsters + the wardens (floors 1–20): the whole Tripo
pipeline per creature — text-to-model → texture → rig → walk clip —
resumable, parallel.

Same recipe as gen_monsters.py / gen_monster_clips.py (floor 1); the
prompts here are written from the floor YAML prose and the shipped
encounter banners so the model matches the card. Body plans pick the
Tripo rigger and the walk preset:

  quadruped  v2.5 rig, preset:quadruped:walk
  biped      v1.0 humanoid rig, preset:walk
  hexapod / octopod / serpentine / aquatic — v2.5 rig with the
             matching preset (Tripo's non-humanoid family; no avian preset)
  none       unrigged: the kill scene slides it (a seep, a lantern)

Outputs land in models/monsters/{id}/ (manifest.json, 00_base.glb,
10_textured.glb, 20_rigged.glb, 50_walk.glb) — the same layout floor 1
uses, so ship_monsters.py picks the finished clip up unchanged.

Usage:
  python3 gen_floors.py                 # every creature below, 4 workers
  python3 gen_floors.py -j 6 id id …    # subset, N workers
  python3 gen_floors.py status
"""
import json
import sys
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from gen_monsters import OUT, STYLE, api, download, wait, FACE_LIMIT, \
    GEN_MODEL, TEXTURE_MODEL

RIG_MODEL_OF = {"biped": "v1.0-20240301"}          # else v2.5-20260210
RIG_V25 = "v2.5-20260210"
WALK_OF = {
    "quadruped": "preset:quadruped:walk", "biped": "preset:walk",
    "hexapod": "preset:hexapod:walk", "octopod": "preset:octopod:walk",
    "serpentine": "preset:serpentine:march",
    "aquatic": "preset:aquatic:march",
}

Q = ("Fantasy game monster, single creature, full body, standing on all "
     "fours in a neutral stance, all four legs straight and clearly "
     "separated, head level, side readable silhouette.")
B = ("Fantasy game monster, single character, full body, standing "
     "upright in a clean A-pose, arms straight and held slightly away "
     "from the body, legs apart, nothing held in the hands.")
S = ("Fantasy game monster, single creature, full body, long body "
     "stretched out straight and level, side readable silhouette.")
X = ("Fantasy game monster, single creature, full body, standing with "
     "every leg planted and clearly separated, body level, side "
     "readable silhouette.")

# id: (plan, prompt, texture)
M = {}

def m(cid, plan, prompt, tex):
    M[cid] = {"plan": plan, "prompt": prompt, "texture": tex + " " + STYLE}

# ── floor 2 · The Rustwater Adit (Giants) ─────────────────────────────
m("marsh_wolf", "quadruped",
  "A lean mine hound coated in rust-scale, a wolf-like body plated in "
  "flaking rust, jaws locked half open showing long teeth, thin ribs, "
  "a rail-worker's iron collar. " + Q,
  "Light rust-orange scale plates over pale grey hide, near-white teeth "
  "and eyes, mid-grey iron collar.")
m("cave_cricket", "hexapod",
  "A giant cave cricket the size of a dog, six spined legs with huge "
  "folded back jumping legs, long antennae, a segmented pale carapace, "
  "large compound eyes, chewing mouthparts. " + X,
  "Pale ivory carapace with light-grey segment lines, near-white eyes, "
  "mid-grey leg spines.")
m("shellback_tortoise", "quadruped",
  "A massive tortoise as wide as a cart door, its shell crusted over "
  "with rusted iron plates and rivets, a beaked head on a thick neck, "
  "four heavy clawed legs, dripping wet. " + Q,
  "Light rust-brown riveted plates on the shell, pale grey wrinkled "
  "skin, near-white beak and claws.")
m("kobold_digger", "biped",
  "A small kobold miner in a heavy iron collar, half blind with milky "
  "eyes, dog-like snout, a leather apron and rag wrappings, a mattock "
  "slung on the back, hunched shoulders. " + B,
  "Light sandy-grey scaly skin, mid-grey iron collar and mattock head, "
  "pale leather apron, near-white milky eyes.")
m("orc_overseer", "biped",
  "A scarred red orc outrider, tall and lean, tusked underbite, cropped "
  "ears, a studded leather drover's harness, a coiled whip hung at the "
  "hip, bandaged forearms, hateful stare. " + B,
  "Light brick-red skin, near-white tusks, mid-grey studded leather "
  "harness, pale bandages.")
m("rust_seep", "none",
  "A crawling stain of living rust: a low spreading mound of orange "
  "corrosion with many finger-like tendrils reaching forward along the "
  "ground, bubbling crust, eaten-smooth rock underneath, no face. "
  "Fantasy game monster, single creature, low wide creeping shape, "
  "side readable silhouette.",
  "Light rust-orange crust, near-white bubbling foam edges, mid-grey "
  "smooth stone underneath.")
m("warden_002", "quadruped",
  "A huge pit hound welded into a war engine: a muscular hound body "
  "under riveted iron plate, an ore-crusher's toothed steel jaw grafted "
  "over its head, hydraulic pistons along the legs, chains and rail "
  "spikes dragging from its haunches. " + Q,
  "Light steel plate with mid-grey rivets and rust streaks, near-white "
  "crusher teeth, pale grey hide, light rust chains.")

# ── floor 3 · The Drowned Pasture (Men) ───────────────────────────────
m("sluice_wolf", "quadruped",
  "A marsh wolf, low and web-footed, sodden fur slicked flat, only eyes "
  "and shoulders high, a broad muzzle, waterweed tangled in the coat. "
  + Q,
  "Pale grey slick fur, near-white eyes and teeth, light-green weed "
  "strands, mid-grey wet paws.")
m("reed_adder", "serpentine",
  "A thick marsh adder, a long serpent with a broad flat head, "
  "zigzag pattern along the back, tongue out, body in a slow S curve "
  "lying flat on the ground. " + S,
  "Pale olive scales with a light-grey zigzag pattern, near-white "
  "belly, near-white eyes.")
m("mire_boar", "quadruped",
  "A huge boar armoured in caked mud to the eyes, cracked mud plates "
  "over the shoulders, tusks curling up, bristled ridge, thick legs. "
  + Q,
  "Light dried-mud plates over mid-grey bristled hide, near-white "
  "tusks and eyes.")
m("wire_eel", "serpentine",
  "A long white pike-like fish grown through rusted barbed fence wire, "
  "steel barbs jutting from its flanks, a long toothed jaw, wire "
  "trailing from the tail, body straight and level. " + S,
  "Near-white fish body, light-grey barbed wire and barbs, mid-grey "
  "rust spots, pale eyes.")
m("windfall_haunt", "none",
  "A drowned lantern floating in the air: an old iron storm lantern "
  "with a cracked glass, a cold flame inside, hung from a hovering "
  "knot of pale mist and drifting weed, no hand carrying it. Fantasy "
  "game monster, single object, floating, side readable silhouette.",
  "Light iron lantern frame, near-white glowing glass and flame, pale "
  "grey mist and weed.")
m("warden_003", "quadruped",
  "A giant mire boar under a weir-iron carapace of green bronze, "
  "riveted plates shedding water, iron-capped tusks, a spiked bronze "
  "collar, thick armoured legs. " + Q,
  "Light verdigris-green bronze plates with mid-grey rivets, pale grey "
  "hide, near-white iron-capped tusks.")

# ── floor 4 · The Lightless Glade (Elves) ─────────────────────────────
m("glade_stag", "quadruped",
  "A pale blind stag, bone-white antlers wide and swept back, milky "
  "eyes, lean flanks, long legs, head cocked as if listening. " + Q,
  "Near-white coat, light-grey antlers, pale milky eyes, mid-grey "
  "hooves.")
m("dusk_hare", "quadruped",
  "A large hare, fever-lean and wild-eyed, tall ears back, powerful "
  "hind legs, standing on all fours ready to spring. " + Q,
  "Pale grey fur, near-white belly and eyes, mid-grey ear tips.")
m("glare_moth", "quadruped",
  "A broad wet lamp newt, a salamander two hands wide, flat head, "
  "wide mouth, glistening skin, four splayed legs, a thick tail. " + Q,
  "Pale glossy grey skin with near-white spots, light-grey belly, "
  "near-white eyes.")
m("wick_owl", "biped",   # no avian preset exists; the upright bird takes the humanoid rig
  "A huge owl broad as a door, feathers fluffed, wings folded, big "
  "round facial disc, hooked beak, standing on thick taloned legs. "
  "Fantasy game monster, single creature, full body, standing upright "
  "on both feet, wings folded at the sides, side readable silhouette.",
  "Pale mottled grey feathers, near-white facial disc and eyes, "
  "mid-grey beak and talons.")
m("lamp_eater", "none",
  "A crawling shape of black lichen and lightless moss dragging itself "
  "forward, a low ragged mound with a hollow where a face would be, "
  "lichen fronds reaching ahead. Fantasy game monster, single creature, "
  "low creeping shape, side readable silhouette.",
  "Mid-grey lichen with light-grey frond tips, near-white pale spores, "
  "no dark areas.")
m("lamptree_wight", "biped",
  "A tall wight of snarled black branches shaped like a man, tall as "
  "two men, twig fingers, a cold false glow in the hollow chest, "
  "branch antlers on the head. " + B,
  "Light-grey bark and branches, near-white glowing chest and eyes, "
  "pale grey twigs.")
m("warden_004", "quadruped",
  "A pale stag crowned with a welded iron lamp cage of blue glass "
  "lanterns between its antlers, iron plates riveted along its neck "
  "and back, long legs, milky eyes. " + Q,
  "Near-white coat, light steel lamp cage with near-white glowing "
  "glass, mid-grey rivets, pale antlers.")

# ── floor 5 · The Flooded Mine (Giants) ───────────────────────────────
m("blind_shoal", "serpentine",
  "A pallid eyeless cave fish, fat and blunt, needle teeth in a wide "
  "mouth, translucent fins, body straight and level. " + S,
  "Near-white translucent skin, light pink gills, pale fins, no eyes.")
m("drift_eel", "serpentine",
  "A blind sump lamprey long as a rope, a round sucker mouth ringed "
  "with teeth, a smooth eyeless head, a long tapering finned body lying "
  "straight and level. " + S,
  "Pale grey slick skin, near-white sucker mouth and teeth, light-grey "
  "fin.")
m("downs_courser", "quadruped",
  "A lean mine hound running its message route, long legs, a leather "
  "message satchel strapped to its back, a hanging tongue, ribs "
  "showing, clawed feet. " + Q,
  "Pale grey short fur, mid-grey leather satchel and straps, near-white "
  "teeth and eyes.")
m("coolant_crab", "quadruped",
  "A pale salamander the size of a cart wheel, broad flat head, wide "
  "gaping mouth, thick short legs, a wide tail, wet mottled skin. " + Q,
  "Pale pinkish-grey skin with light mottling, near-white belly, "
  "near-white eyes.")
m("bailer_kobold", "biped",
  "A wet collared kobold, dog-snouted, wearing a sodden rag tunic and a "
  "heavy iron collar, a bailing hook hung at the belt, hunched, wet "
  "to the bone. " + B,
  "Light sandy-grey scaly skin, mid-grey iron collar and hook, pale "
  "wet rag tunic, near-white eyes.")
m("miner_husk", "biped",
  "A drowned miner's husk: a bulky man-shape of dripping water and old "
  "mining gear, a rotten leather helmet, harness straps, an empty hood "
  "where the face was, thick arms. " + B,
  "Light-grey watery body, mid-grey leather helmet and harness, "
  "near-white glowing hood, pale straps.")
m("warden_005", "serpentine",
  "A giant sump eel welded through with iron, a huge pump-valve maw of "
  "riveted steel for a mouth, pipes along its back, a long muscular "
  "finned body lying straight and level. " + S,
  "Light steel valve maw with mid-grey rivets, pale grey slick body, "
  "near-white eyes, light rust pipes.")

# ── floor 6 · The Threshold Dark (Deep) ───────────────────────────────
m("grave_moth", "quadruped",
  "A palm-broad grave rat, hairless and pale, big clinging claws, a "
  "long naked tail, wide blind eyes, dust caked in the skin folds. " + Q,
  "Pale grey hairless skin, near-white eyes and teeth, light dust "
  "patches.")
m("guano_vole", "quadruped",
  "A bloated blind vole, round body, tiny eyes, big yellow incisors, "
  "short legs, coarse patchy fur. " + Q,
  "Pale brown-grey fur, near-white incisors, light-grey belly.")
m("silk_broodling", "octopod",
  "A dog-sized cave spider broodling, eight long spindly legs, a small "
  "pale body, big forelegs raised, glinting eyes, silk trailing. " + X,
  "Pale grey body, near-white legs, light-grey joints, near-white "
  "eyes.")
m("vault_weaver", "octopod",
  "A huge sentinel spider, an armoured ambush weaver, eight thick "
  "plated legs, a broad abdomen, eight bright eyes, heavy fangs. " + X,
  "Light-grey armour plates, mid-grey leg joints, near-white eyes and "
  "fangs.")
m("lane_boar", "quadruped",
  "A blind boar grown into a wall of crusted bristle, a massive front-"
  "heavy body, small blind eyes, thick tusks, short legs. " + Q,
  "Light-grey crusted bristles, pale hide, near-white tusks.")
m("wrapped_husk", "biped",
  "A man-shaped cocoon of silk walking upright, empty inside, silk "
  "wrapping every limb, a hollow where the face would be. " + B,
  "Near-white silk wrapping, light-grey shadowed folds, pale hollow "
  "face.")
m("warden_006", "octopod",
  "A sentinel spider welded huge, iron plates over the abdomen, steel "
  "spinnerets, eight thick armoured legs, heavy fangs, eight glowing "
  "eyes. " + X,
  "Light steel plates with mid-grey rivets, pale grey body, near-white "
  "eyes and fangs.")

# ── floor 1 · the warden ──────────────────────────────────────────────
m("warden_001", "quadruped",
  "A big beast of wolf and welded plate: a dire wolf body under riveted "
  "steel plate, a plated head with a hinged steel jaw, servo pistons "
  "at the shoulders and hips, thick legs. " + Q,
  "Light steel plate with mid-grey rivets, pale grey fur, near-white "
  "teeth and eyes.")

# ── floor 7 · The Rotting Orchard (Men) ───────────────────────────────
m("orchard_wolfpack", "quadruped",
  "A lean grey orchard wolf, coat matted with rotting fruit pulp and "
  "wasps, lips peeled back in a drunk snarl, ears flat, ribs showing, "
  "tail low. " + Q,
  "Pale grey fur with light-brown fruit-pulp stains, near-white teeth "
  "and eyes, mid-grey nose.")
m("rabid_boar", "quadruped",
  "A huge boar the size of a hay-wain, soaked and dripping with black "
  "rot-cider, foam at the jaws, tusks long and curled, broken branches "
  "and leaves stuck in its bristles, small furious eyes. " + Q,
  "Mid-grey bristled hide with darker dripping cider streaks, "
  "near-white tusks, foam and eyes, light-brown leaves.")
m("hornet_swarm", "none",
  "A boiling carpet of hundreds of mice moving as one mound: a low "
  "wide heap of tightly packed small mice, tails and pink noses "
  "everywhere, the front edge rearing up like a wave, no single face. "
  "Fantasy game monster, single creature, low wide creeping shape, "
  "side readable silhouette.",
  "Light grey-brown fur, near-white bellies and eyes, pale pink noses "
  "and tails.")
m("windfall_crow", "quadruped",
  "A bloated giant dormouse, fat and round with rot-swollen belly, "
  "sticky fur, big black eyes, long whiskers, small paws, thick furry "
  "tail, mouth open showing front teeth. " + Q,
  "Light sandy-brown fur, near-white belly and teeth, mid-grey eyes "
  "and nose.")
m("orchard_hare", "quadruped",
  "A big fever-thin hare running flat out, ears pinned back, long "
  "hind legs stretched, wild rolling eyes, foam at the mouth, coat "
  "ragged. " + Q,
  "Pale grey-brown fur, near-white belly, tail and eyes, mid-grey "
  "ear tips.")
m("windfall_wight", "biped",
  "A reeling drowned-looking man-figure dripping black cider, sodden "
  "orchard-worker's coat and hat, face hollow and slack, one hand "
  "cupped open as if offering a drink, the other hand hidden behind "
  "the back holding a pruning hook. Fantasy game monster, single "
  "character, full body, standing upright, legs apart.",
  "Mid-grey sodden coat and hat streaked with dark cider, pale "
  "grey skin, near-white eyes, light-grey cup.")
m("warden_007", "quadruped",
  "A monstrous cider-mad boar armoured in cider-press iron: barrel "
  "hoops banded round its body, press-plates riveted over the shoulders "
  "and skull, iron screw-spike on the brow, black cider dripping from "
  "every seam, huge tusks. " + Q,
  "Light rust-brown iron hoops and plates with mid-grey rivets, dark "
  "grey bristled hide, near-white tusks and eyes.")

# ── floor 8 · The Ash Dunes (Ogres) ───────────────────────────────────
m("cinder_wolf", "quadruped",
  "A lean ash-line jackal, long-legged and big-eared, coat caked in "
  "grey ash, ribs sharp, sly narrow muzzle, brush tail. " + Q,
  "Pale ash-grey coat, near-white eyes and teeth, mid-grey ear tips "
  "and muzzle.")
m("dune_hare", "quadruped",
  "A pale desert hare with long ears, running flat out over glass "
  "dust, its coat spiked with fine shards of glass, hind legs "
  "stretched, eyes wide. " + Q,
  "Near-white fur with light-grey glass shards, pale eyes, mid-grey "
  "ear tips.")
m("cinder_salamander", "quadruped",
  "A big ash salamander, low and long, blunt head, ember-veined skin "
  "with glowing cracks, four splayed legs, a thick tail dragging "
  "smoke, one orange eye open. " + Q,
  "Mid-grey ash skin with near-white glowing crack veins, pale "
  "belly, near-white eye.")
m("cinder_vulture", "biped",
  "A huge ash-caked vulture standing on the ground, bald wrinkled "
  "head and neck, hooked beak, wings folded tight at the sides, ruff "
  "of ragged feathers, thick scaly legs, hunched. Fantasy game "
  "monster, single creature, full body, standing upright, side "
  "readable silhouette.",
  "Mid-grey ash-caked feathers, pale bald head and neck, near-white "
  "beak and eyes, light-grey legs.")
m("ash_adder", "serpentine",
  "A thick sand adder, a long serpent with a broad flat head, "
  "horn-scales above the eyes, keeled ash-grey scales with a pale "
  "diamond pattern, tongue out, body straight and level. " + S,
  "Pale ash-grey scales with near-white diamond pattern, light "
  "belly, near-white eyes.")
m("greywell_ogre", "biped",
  "A huge sun-mad dune ogre, heavy hunched shoulders, tiny eyes, "
  "underbite, a riveted iron slave collar, rag loincloth, cracked "
  "ash-grey skin, a large rough glass boulder resting on one "
  "shoulder held by one hand, other arm hanging. Fantasy game "
  "monster, single character, full body, standing upright, legs "
  "apart.",
  "Light ash-grey cracked skin, mid-grey iron collar, pale rag "
  "loincloth, near-white glass boulder, near-white eyes and teeth.")
m("warden_008", "biped",
  "A colossal dune ogre welded into slag-plate armour and ash-glass "
  "shards, an iron collar fused into its skull, plates riveted over "
  "chest and shoulders, one arm hydraulic, a glowing molten boulder "
  "held in one hand at the side, hunched and massive. Fantasy game "
  "monster, single character, full body, standing upright, legs "
  "apart.",
  "Light slag-grey plates with mid-grey rivets, pale ash skin, "
  "near-white glass shards, near-white glowing boulder, eyes.")


# ── floor 9 · The Signal Heath (Men) ──────────────────────────────────
m("beacon_moth", "quadruped",
  "A vole as broad as a plate, blinding-pale, fat round body, tiny ears, "
  "short legs, whiskers, small black eyes, blunt muzzle. " + Q,
  "Near-white fur, light-grey paws and nose, mid-grey eyes.")
m("moor_hare", "quadruped",
  "A wild-eyed moorland hare mid-bolt, tall ears back, tufts of bog "
  "cotton caught in the fur, ragged coat, long hind legs. " + Q,
  "Pale grey-brown fur with near-white cotton tufts, near-white belly "
  "and eyes.")
m("night_hawk", "quadruped",
  "A shrew grown huge and wrong, long pointed twitching snout, tiny "
  "eyes, mouth open showing needle teeth, velvet coat, short legs, "
  "thin tail. " + Q,
  "Mid-grey velvet fur, pale belly, near-white teeth, pale pink snout.")
m("shadow_wolf", "quadruped",
  "A lean black wolf built for cover, low head, narrow muzzle, pale "
  "eyes, coat blending to smoke at the edges, ears flat. " + Q,
  "Dark grey to near-black fur, near-white eyes and teeth, mid-grey "
  "smoke edges.")
m("pylon_adder", "serpentine",
  "A charged adder, a long serpent with a flat head, scales edged with "
  "blue-white sparks, small arcs of lightning along the back, tongue "
  "out, body straight and level. " + S,
  "Mid-grey scales with near-white spark edges, near-white belly and "
  "eyes.")
m("flicker_wight", "biped",
  "A man-shape of dark and static: a lineman's figure in a long coat "
  "and hood, face a blank of grey noise, hands empty and open, "
  "outline flickering. Fantasy game monster, single character, full "
  "body, standing upright, legs apart, arms slightly away from body.",
  "Dark grey coat and hood, near-white static face, pale grey hands.")
m("warden_009", "quadruped",
  "A huge shadow-line wolf maned in pylon lamps: a black wolf body with "
  "a mane of glass lamp bulbs and wire down the neck and shoulders, "
  "cable trailing from the haunches, blazing white eyes. " + Q,
  "Near-black fur, near-white glowing lamp bulbs and eyes, mid-grey "
  "wire and cable.")

# ── floor 10 · The Muster Field (Men) ─────────────────────────────────
m("kings_guard", "biped",
  "A goblin of the honor-watch in overlapped tower plate armour, iron "
  "collar, closed visor helm with a plume, snapped arrows stuck in "
  "the plate, sword sheathed at the hip, empty hands. " + B,
  "Light steel plate with mid-grey rivets, pale green skin, near-white "
  "plume, mid-grey collar.")
m("banner_wolf", "quadruped",
  "A half-starved wolf dragging six feet of rotted banner tangled at "
  "its neck, ribs showing, matted coat, torn cloth trailing behind "
  "along the ground. " + Q,
  "Mid-grey ragged fur, pale tattered banner cloth, near-white teeth "
  "and eyes.")
m("courier_hound", "quadruped",
  "A lean long-legged courier hound at a dead run, deep chest, rotted "
  "leather harness straps hanging from its shoulders, ears back, "
  "mouth open. " + Q,
  "Pale tan short coat, mid-grey harness straps, near-white teeth and "
  "eyes.")
m("parade_horse", "quadruped",
  "A tall gaunt war-horse, riderless, tack rotted to hanging straps, "
  "eyes white and blind, ribs showing, mane ragged, head low. " + Q,
  "Pale grey coat, near-white eyes and mane, mid-grey rotted straps.")
m("bunting_kite", "biped",
  "A king-sized kite bird standing on the ground, hooked beak, forked "
  "tail, wings folded, ragged banner scraps tangled in its feathers, "
  "sharp eyes. Fantasy game monster, single creature, full body, "
  "standing upright, side readable silhouette.",
  "Light brown feathers, pale grey banner scraps, near-white beak and "
  "eyes.")
m("muster_wight", "biped",
  "A half-there soldier of mist and mire in a rusted breastplate and "
  "kettle helm, face hollow, holding a rotted standard pole upright "
  "against its shoulder, other hand empty. Fantasy game monster, "
  "single character, full body, standing upright, legs apart.",
  "Pale grey mist body, light rust breastplate and helm, mid-grey "
  "pole, near-white hollow eyes.")
m("warden_010", "biped",
  "Gnarl the Goblin King: a fat scarred goblin in a crooked tin crown "
  "and a moth-eaten fur robe over dented plate, a notched sword too "
  "big for him sheathed on his back, empty hands, sneering. " + B,
  "Light green skin, mid-grey dented plate, pale fur robe, near-white "
  "crown, teeth and eyes.")

# ── floor 11 · The Adit (Dwarves) ─────────────────────────────────────
m("kobold_scavenger", "biped",
  "A wiry kobold scavenger, dog-like snout, big ears, a sack of "
  "stripped copper wire slung over one shoulder, a pry-bar hung on "
  "the belt, rag tunic, empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey pry-bar, pale rag tunic, "
  "light copper wire in the sack.")
m("rust_hound", "quadruped",
  "A hound of wire and hide, ribs of iron wire showing through torn "
  "hide, joints weeping orange rust, nose down, iron collar, teeth "
  "bared. " + Q,
  "Mid-grey hide, light-grey wire, light rust-orange joints, near-white "
  "teeth and eyes.")
m("orc_outrider", "biped",
  "A red orc outrider in half a warframe: one arm bare and muscled, "
  "the other a heavy hydraulic steel arm, chest plate on one side, "
  "tusked underbite, cropped ears, empty hands. " + B,
  "Light brick-red skin, light steel warframe arm and plate with "
  "mid-grey pistons, near-white tusks.")
m("adit_bat", "none",
  "A giant bat as broad as a cloak in flight, wings fully spread wide "
  "and level, ears large, mouth open with small fangs, body small "
  "between the wings, seen side-on. Fantasy game monster, single "
  "creature, wings spread flat, side readable silhouette.",
  "Mid-grey wing membrane, dark grey fur body, near-white fangs and "
  "eyes.")
m("warden_011", "none",
  "A tunneling engine grown teeth: a long riveted iron drill-machine "
  "on tracks, its bore-head become a set of ore-crusher jaws lined "
  "with steel teeth, red water dripping, pipes and rivets along the "
  "body. Fantasy game monster, single machine, low long shape, side "
  "readable silhouette.",
  "Light steel plates with mid-grey rivets and rust streaks, near-white "
  "teeth, light rust-red drips.")

# ── floor 12 · The Drowned Galleries (Dwarves) ────────────────────────
m("bilge_kobold", "biped",
  "A kobold fisher in a wet oilskin coat and hood, dog-like snout, a "
  "barbed fishing spear strapped across the back, coils of line at "
  "the belt, empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey oilskin, pale spear shaft, "
  "near-white eyes.")
m("drowned_hauler", "hexapod",
  "An ore-hauler machine wading on six rusted iron legs, a flatbed "
  "body of riveted plate, unlit lamps on the front, silt and river-moss "
  "hanging from it, water dripping. " + X,
  "Light steel plates with mid-grey rivets and rust, pale grey silt, "
  "near-white lamp glass.")
m("orc_diver", "biped",
  "A red orc in a sealed diving warframe, round brass helmet with a "
  "porthole, riveted plate suit, hoses on the back, water sheeting "
  "off, empty gauntlets. " + B,
  "Light brass helmet, mid-grey plate suit with light rivets, pale "
  "hoses, near-white porthole glass.")
m("sump_eel", "serpentine",
  "A pale-bellied eel thick as a hawser, long body straight and "
  "level, broad toothed mouth open, small eyes, dorsal fin along the "
  "back. " + S,
  "Dark grey back, near-white belly, near-white teeth and eyes.")
m("warden_012", "biped",
  "Sumplock: a tall standing figure of pump-iron and pale river-moss, pipe "
  "segments for limbs, a valve wheel in the chest, moss hanging like "
  "a cloak, water streaming, empty hands. "
  "Fantasy game monster, single character, full body, standing "
  "upright, legs apart, arms slightly away from body.",
  "Mid-grey iron pipes with light rust, near-white bone, pale moss "
  "strands, near-white eyes.")

# ── floor 13 · The Counting Halls (Dwarves) ───────────────────────────
m("coin_sifter", "biped",
  "A kobold coin-sifter in a clerk's vest and eyeshade, dog-like "
  "snout, a small weighing hammer hung on the belt, coloured scrip "
  "stuffed in every pocket, empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey vest, pale paper scrip, "
  "near-white eyes.")
m("tally_engine", "biped",
  "A brass counting-engine walking upright: a humanoid automaton of "
  "brass rods and abacus frames, bead-rails across the chest, two "
  "jointed arms with bead-flicking fingers, two piston legs, a dial "
  "for a face. " + B,
  "Light brass with mid-grey joints, near-white dial face, pale beads.")
m("debt_collector", "biped",
  "A red orc in a full warframe painted with white tally-marks, heavy "
  "plate shoulders, tusked underbite, a ledger chained to the belt, "
  "empty gauntlets. " + B,
  "Mid-grey plate with near-white tally-marks, light brick-red skin, "
  "near-white tusks.")
m("ledger_wisp", "none",
  "A tall floating flame of dust and lamplight, a drifting teardrop "
  "of glowing motes with torn paper ledger pages caught in the haze, "
  "no limbs, no face, tapering to a point at the bottom. Fantasy "
  "game spirit, single object, floating, side readable silhouette.",
  "Near-white glowing motes, pale grey haze, light-grey numerals.")
m("scrip_rat", "quadruped",
  "A big rat with cheeks packed full of paper, scraps of coloured "
  "scrip stuck in its fur, long naked tail, beady eyes, whiskers. "
  + Q,
  "Mid-grey fur with pale paper scraps, near-white eyes and teeth, "
  "pale pink tail.")
m("warden_013", "biped",
  "Brassbone: a tall skeleton built of brass counting-rods and iron "
  "weight-plates, ribs of rods, a skull with dial eyes, weight-plate "
  "shoulders and feet, empty hands. " + B,
  "Light brass rods, mid-grey iron weight-plates, near-white dial "
  "eyes.")

# ── floor 14 · The Gear Halls (Dwarves) ───────────────────────────────
m("gear_kobold", "biped",
  "A kobold gear-thief in a tool harness, dog-like snout, big ears, a "
  "large wrench hung on the belt, small cogs strung on a cord round "
  "the neck, empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey wrench and cogs, pale "
  "harness, near-white eyes.")
m("loose_flywheel", "none",
  "A runaway iron flywheel the size of a millstone standing on its "
  "rim, thick spoked wheel with a heavy rim, a broken stub of axle at "
  "the hub, worn and scarred, seen side-on. Fantasy game monster, "
  "single object, upright wheel, side readable silhouette.",
  "Mid-grey iron rim and spokes with light worn edges, light rust "
  "streaks.")
m("pit_fighter", "biped",
  "A red orc pit-fighter in a battered warframe stripped to the arms "
  "and shoulders, bare scarred chest, tusked underbite, chalk on the "
  "knuckles, empty hands. " + B,
  "Light brick-red skin, mid-grey warframe arms with light dents, "
  "near-white tusks and chalk.")
m("belt_runner", "quadruped",
  "A sleek long weasel-like creature built for speed, low body, short "
  "legs, long neck, small ears, claws out, glossy coat. " + Q,
  "Dark grey glossy fur, pale throat, near-white eyes and claws.")
m("warden_014", "quadruped",
  "Gearhide: a huge beast walking on four legs of stacked cogs, a hide "
  "of clutch-iron plates, a gear-toothed spine, a heavy blunt head of "
  "meshed wheels, pistons at the joints. " + Q,
  "Mid-grey iron plates and cogs with light worn teeth, light rust "
  "streaks, near-white eyes.")

# ── floor 15 · The Core Vaults (Dwarves) ──────────────────────────────
m("glow_sick_kobold", "biped",
  "A sick kobold shedding faint light, fur out in patches, skin "
  "cracked and glowing at the seams, eyes wrong and wide, ragged "
  "tunic, empty hands, hunched. " + B,
  "Pale grey skin with near-white glowing cracks, mid-grey ragged "
  "tunic, near-white eyes.")
m("fuel_thief", "biped",
  "A red orc in a straining warframe with a heavy lead-lined pannier "
  "of glowing core-rods strapped on its back, tusked underbite, "
  "empty gauntlets. " + B,
  "Mid-grey plate, light brick-red skin, mid-grey lead pannier with "
  "near-white glowing rods, near-white tusks.")
m("forge_remnant", "biped",
  "A headless dwarven vault-tender automaton walking on heavy "
  "magnetic feet, a squat riveted iron body, no head, gauge dials on "
  "the chest, thick arms, empty hands. " + B,
  "Mid-grey riveted iron, light steel dials, light rust streaks, "
  "near-white gauge faces.")
m("rod_wisp", "none",
  "A tall upright spindle of white glow, a floating rod of light "
  "wrapped in drifting rings of haze, no limbs, no face, edges hazing "
  "into the air, tapering at both ends. Fantasy game spirit, single "
  "object, floating, side readable silhouette.",
  "Near-white glow, pale grey haze at the edges.")
m("warden_015", "quadruped",
  "Coreburn: a furnace-beast, a heavy four-legged body of black iron "
  "plates with a cracked glowing core in the chest, seams glowing "
  "bright, a blunt furnace-door head with glowing eyes, smoke from "
  "the shoulders. " + Q,
  "Dark grey iron plates, near-white glowing core and seams, "
  "near-white eyes.")

# ── floor 16 · The Forge Commons (Dwarves) ────────────────────────────
m("orc_armorer", "biped",
  "A red orc armorer in a leather smith's apron over warframe legs, "
  "bare scarred arms, tusked underbite, tongs and a hammer hung on "
  "the belt, empty hands. " + B,
  "Light brick-red skin, mid-grey leather apron, mid-grey warframe "
  "legs, near-white tusks.")
m("hammer_kobold", "biped",
  "A small kobold apprentice with a smith's hammer twice its height "
  "strapped across its back, leather apron, dog-like snout, big ears, "
  "empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey hammer head, pale apron, "
  "near-white eyes.")
m("half_forged", "biped",
  "A half-forged thing off the great anvil, a roughly man-shaped lump "
  "of hammered iron still glowing cherry-hot down one side, walking on "
  "two long blacksmith's-tong legs, stubby arms, no face. Fantasy game "
  "monster, single character, full body, standing upright, legs "
  "apart, arms slightly away from body.",
  "Dark grey hammered iron, near-white glowing hot side, mid-grey tong "
  "legs.")
m("bellows_hound", "quadruped",
  "A hound at a flat sprint, coat singed to wire, ribs sharp, ears "
  "back, mouth open, singed patches, thin whip tail. " + Q,
  "Mid-grey wiry singed coat, near-white teeth and eyes, dark grey "
  "burnt patches.")
m("warden_016", "quadruped",
  "Anvilback: a massive four-legged iron beast with an old blacksmith's "
  "anvil fused into its spine, hammer-scarred plates, a heavy blunt "
  "head, thick legs. " + Q,
  "Mid-grey iron plates with light hammer scars, near-white anvil "
  "face, near-white eyes.")

# ── floor 17 · The Smelters (Dwarves) ─────────────────────────────────
m("slag_rat", "quadruped",
  "A rat the size of a hound, coat shingled with flakes of black glass "
  "slag, long naked tail, beady eyes, whiskers, bared teeth. " + Q,
  "Dark grey glassy slag flakes over mid-grey fur, near-white teeth "
  "and eyes.")
m("ladle_crew", "none",
  "A wheeled iron ladle-carriage: a big smelting ladle on a hand-crank "
  "cart, three small kobolds clinging to it working the crank, sparks "
  "and slag at the ladle lip. Fantasy game monster, single object "
  "with riders, side readable silhouette.",
  "Mid-grey iron ladle and cart, light sandy-grey kobolds, near-white "
  "sparks and glow at the lip.")
m("smelter_boss", "biped",
  "A red orc smelter-boss in a warframe caked in metal spatter, heavy "
  "shoulders, tusked underbite, a long tapping-rod strapped across "
  "the back, empty gauntlets. " + B,
  "Mid-grey plate with near-white spatter, light brick-red skin, "
  "near-white tusks.")
m("heat_haunt", "biped",
  "A man-shaped standing shimmer of heat, a translucent figure of "
  "warped air with a faint glowing core, no face, arms slightly out. "
  "Fantasy game monster, single character, full body, standing "
  "upright, legs apart.",
  "Pale grey translucent body, near-white glowing core.")
m("warden_017", "quadruped",
  "Smeltjaw: a beast of half-set black slag on four thick legs, a seam "
  "of live molten metal for a throat and mouth, cracked glassy hide "
  "glowing in the cracks, smoke rising. " + Q,
  "Dark grey glassy slag, near-white glowing throat and cracks, "
  "near-white eyes.")

# ── floor 18 · The Deep Drifts (Dwarves) ──────────────────────────────
m("blind_digger", "biped",
  "A blind kobold digger pale as candle-wax, eyes milky and sunken, "
  "dog-like snout, big ears, a pick strapped across the back, rag "
  "wrappings, empty hands. " + B,
  "Near-white waxy skin, pale milky eyes, mid-grey pick, pale rags.")
m("winch_crawler", "none",
  "A winch head torn off its mounts, a heavy iron cable drum with two "
  "grabbing iron arms reaching forward, a loop of steel cable trailing "
  "behind, rivets and gears. Fantasy game monster, single machine, low "
  "shape, side readable silhouette.",
  "Mid-grey iron drum and arms with light rust, light steel cable.")
m("pit_hound", "quadruped",
  "A long low quiet hound, eyes milky, ears huge like a bat's, hairless "
  "pale hide, long neck, nose to the ground. " + Q,
  "Near-white hairless hide, pale milky eyes, mid-grey ear membranes.")
m("drift_moth", "none",
  "A giant grey moth the span of two hands, wings spread wide and "
  "level, powdery, feathered antennae, furry body, seen side-on in "
  "flight. Fantasy game monster, single creature, wings spread flat, "
  "side readable silhouette.",
  "Pale grey powdery wings with mid-grey markings, near-white fur "
  "body, near-white eyes.")
m("warden_018", "biped",
  "Deepwinch: a winch drum grown a body, a tall standing figure of "
  "iron cable wound over a drum torso, cable arms and legs, a hook "
  "for a head, cables singing taut, empty hands. Fantasy game "
  "monster, single character, full body, standing upright, legs "
  "apart, arms slightly away from body.",
  "Mid-grey iron drum, light steel cable, near-white hook, light rust.")

# ── floor 19 · The Breach (Dwarves) ───────────────────────────────────
m("door_breaker", "biped",
  "A red orc veteran in a warframe scarred black by dwarf-fire, one "
  "shoulder plate half melted, tusked underbite, a war-maul strapped "
  "on the back, empty gauntlets. " + B,
  "Mid-grey scorched plate with dark burn marks, light brick-red skin, "
  "near-white tusks.")
m("powder_kobold", "biped",
  "A kobold powder-boy in a scorched leather apron, fuse-cord looped "
  "round its neck like a scarf, a small powder keg strapped to its "
  "back, dog-like snout, grinning, empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey scorched apron, pale fuse "
  "cord, mid-grey keg.")
m("doorward_remnant", "biped",
  "A dwarven door-engine, a squat heavy iron automaton with a broad "
  "riveted chest, a slot visor for a face, two halberd-blade arms "
  "held down at the sides, thick piston legs. Fantasy game monster, "
  "single character, full body, standing upright, legs apart.",
  "Mid-grey riveted iron with light rust, near-white blade edges, "
  "near-white visor glow.")
m("breach_crow", "biped",
  "A crow the size of a dog standing on the ground, glossy feathers, "
  "heavy beak, wings folded, one eye scarred, scorch marks on the "
  "wingtips. Fantasy game monster, single creature, full body, "
  "standing upright, side readable silhouette.",
  "Dark grey glossy feathers, near-white beak and eye, mid-grey legs.")
m("scorch_rat", "quadruped",
  "A big rat with burn-bald patches on its hide, scarred pink skin "
  "showing through grey fur, long naked tail, flat calm eyes. " + Q,
  "Mid-grey fur with pale pink bald patches, near-white eyes and "
  "teeth.")
m("warden_019", "biped",
  "Gatebone: a giant built from breach wreckage, hinge-plates for "
  "shoulders, a slab of blown vault door held as a shield on one arm, "
  "riveted iron body, a helm of door-lock, empty other hand. Fantasy "
  "game monster, single character, full body, standing upright, legs "
  "apart.",
  "Mid-grey riveted iron with light scorch marks, light steel hinges, "
  "near-white eye slits.")

# ── floor 20 · The Warcamp (Dwarves) ──────────────────────────────────
m("honor_guard", "biped",
  "A red orc of the honor guard in a warframe polished to a dull red "
  "shine, tall crested helm, a glaive strapped upright on the back, "
  "tusked underbite, empty gauntlets. " + B,
  "Light red-tinted plate with near-white highlights, light brick-red "
  "skin, near-white tusks, mid-grey glaive shaft.")
m("warframe_champion", "biped",
  "A pit champion in a full salvaged warframe, mismatched heavy "
  "plates, huge shoulders, spiked knuckles, a grilled helm, tusks "
  "under the grille, empty gauntlets. " + B,
  "Mid-grey mismatched plates with light scratches, near-white spikes "
  "and tusks, light brick-red skin at the joints.")
m("camp_hound", "quadruped",
  "A starved rust hound with a short broken chain hanging from an "
  "iron collar, ribs sharp, wire showing through the hide, teeth "
  "bared. " + Q,
  "Mid-grey hide, light-grey wire, mid-grey collar and chain, "
  "near-white teeth and eyes.")
m("drum_kobold", "biped",
  "A small kobold with a great war-drum bigger than itself strapped "
  "to its front, drumsticks tucked in the belt, dog-like snout, big "
  "ears, empty hands. " + B,
  "Light sandy-grey scaly skin, mid-grey drum with near-white skin "
  "head, pale straps.")
m("camp_looter", "biped",
  "A scarred lean goblin looter, a bulging sack of buckles slung on "
  "the back, patched leather jerkin, knife sheathed at the hip, "
  "empty hands. " + B,
  "Light green skin, mid-grey jerkin, pale sack, near-white eyes and "
  "teeth.")
m("warden_020", "biped",
  "Warlord Skarn: a huge red orc in a magnificent warframe of "
  "dwarf-steel over orc muscle, layered plates, a horned helm, a "
  "great axe strapped across the back, cloak of three clan banners, "
  "empty gauntlets. " + B,
  "Light steel plates with mid-grey rivets, light brick-red skin, "
  "near-white tusks and horns, dark grey cloak.")


_lock = threading.Lock()


def build(cid):
    spec = M[cid]
    plan = spec["plan"]
    mpath = OUT / cid / "manifest.json"
    man = json.loads(mpath.read_text()) if mpath.exists() else {}

    def save():
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(man, indent=2))

    def stage(key, filename, create, preview=False):
        path = OUT / cid / filename
        if man.get(key, {}).get("done") and path.exists():
            return man[key]["task"]
        task_id = man.get(key, {}).get("task") or create()
        man[key] = {"task": task_id, "done": False}
        save()
        d = wait(task_id, f"{cid}/{key}")
        out = d.get("output", {})
        if out.get("model_url"):
            download(out["model_url"], path)
        if preview and out.get("rendered_image_url"):
            download(out["rendered_image_url"], OUT / cid / "preview.png")
        man[key]["done"] = True
        save()
        return task_id

    print(f"== {cid} ({plan}) ==", flush=True)
    gen = stage("gen", "00_base.glb", lambda: api(
        "POST", "/generation/text-to-model", {
            "prompt": spec["prompt"], "model": GEN_MODEL,
            "face_limit": FACE_LIMIT, "texture": False, "pbr": False,
            "smart_low_poly": True,
        })["task_id"])
    tex = stage("texture", "10_textured.glb", lambda: api(
        "POST", "/models/texture", {
            "input": gen, "model": TEXTURE_MODEL, "pbr": False,
            "texture_prompt": {"text": spec["texture"]},
        })["task_id"], preview=True)
    if plan == "none":
        return
    rig = stage("rig", "20_rigged.glb", lambda: api(
        "POST", "/animations/rig", {
            "input": tex, "model": RIG_MODEL_OF.get(plan, RIG_V25),
            "spec": "tripo", "rig_type": plan, "out_format": "glb",
        })["task_id"])
    stage("walk", "50_walk.glb", lambda: api(
        "POST", "/animations/retarget", {
            "input": rig, "animation": WALK_OF[plan],
            "out_format": "glb", "bake_animation": True,
            "animate_in_place": True,
        })["task_id"])


def safe(cid):
    try:
        build(cid)
        return f"{cid}: ok"
    except SystemExit as e:
        return f"{cid}: FAILED {e}"
    except Exception:
        return f"{cid}: FAILED\n{traceback.format_exc()}"


def status():
    bal = api("GET", "/account/balance")
    print(f"balance: {bal['balance']}  frozen: {bal['frozen']}")
    for cid, spec in M.items():
        mpath = OUT / cid / "manifest.json"
        man = json.loads(mpath.read_text()) if mpath.exists() else {}
        done = [k for k in ("gen", "texture", "rig", "walk")
                if man.get(k, {}).get("done")]
        pend = [k for k in ("gen", "texture", "rig", "walk")
                if man.get(k, {}).get("task") and not man[k].get("done")]
        print(f"  {cid:20s} {spec['plan']:10s} "
              f"{','.join(done) or '—'}"
              + (f"  (pending {','.join(pend)})" if pend else ""))


def main():
    args = sys.argv[1:]
    if args == ["status"]:
        status()
        return
    jobs = 4
    if args[:1] == ["-j"]:
        jobs = int(args[1])
        args = args[2:]
    picked = args or list(M)
    unknown = set(picked) - set(M)
    if unknown:
        sys.exit(f"unknown: {', '.join(sorted(unknown))}")
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        for line in ex.map(safe, picked):
            print(line, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
