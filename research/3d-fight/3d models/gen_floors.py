#!/usr/bin/env python3
"""Floors 2–6 monsters + the six wardens (floors 1–6): the whole Tripo
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
