#!/usr/bin/env python3
"""Generate floor-1 MONSTER models with the Tripo3D API (PLAN3 Part A).

Monsters, not pets: the breed style bible from research/3d-fight/PLAN3.md —
native = gaunt/bone-spurred/scarred, pressed = scrap-iron war-gear,
wrongmade = wrong geometry, metallic shells, glowing seams.

Pipeline per creature: text-to-model → texture. NO rig — the kill scene
animates them procedurally (walk bob, lunge, flinch) in fight3d.js, so the
quadruped-rig problem never arises.

Resumable per creature: models/monsters/{id}/manifest.json (one manifest
per asset so parallel runs never race).

Usage:
  python3 gen_monsters.py grey_wolf      # one creature
  python3 gen_monsters.py                # all six, sequential
  python3 gen_monsters.py status
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "models" / "monsters"
API = "https://openapi.tripo3d.ai/v3"

GEN_MODEL = "v3.0-20250812"
TEXTURE_MODEL = "v3.0-20250812"
FACE_LIMIT = 2000

# Same palette law as gen_models.py (1bit-images.md): the whole texture
# lives in the light-to-mid band — dark paint vanishes into the black stage.
STYLE = (
    "Flat hand-painted game texture designed for 1-bit dithered pixel-art "
    "rendering. The WHOLE texture stays in the LIGHT-TO-MID tonal range — "
    "nothing darker than mid-grey, no black, no deep shadows. Large "
    "uniform colour regions with clear tonal steps between neighbouring "
    "regions (near-white against light against mid-tone), no fine "
    "micro-texture, no noise, no photorealistic surface detail, matte, "
    "bold simple readable shapes, bright and evenly lit."
)

POSE_Q = ("Fantasy game monster, single creature, full body, standing on "
          "all fours in a neutral stance, side readable silhouette.")
POSE_B = ("Fantasy game monster, single creature, full body, standing "
          "upright in A-pose, arms slightly away from the body.")

MONSTERS = {
    "grey_wolf": {
        "prompt": ("A gaunt dire wolf, ribs showing through matted fur, "
                   "jagged bone spikes growing along the spine, scarred "
                   "muzzle, bared oversized fangs, hackles raised. "
                   + POSE_Q),
        "texture": ("Light grey matted fur, near-white bone spikes and "
                    "fangs, mid-grey scarred muzzle. " + STYLE),
    },
    "feral_boar": {
        "prompt": ("A massive feral boar, cracked tusks capped with rusted "
                   "iron, bony armour plates grown over the shoulders and "
                   "back, bristled ridge, small furious eyes. " + POSE_Q),
        "texture": ("Mid-tone bristled hide, near-white tusks with "
                    "light-grey iron caps, light bone armour plates. "
                    + STYLE),
    },
    "hedge_rat": {
        "prompt": ("A dog-sized plague rat, scabrous hairless patches, "
                   "needle teeth, a row of spiked vertebrae, long naked "
                   "segmented tail, hunched aggressive posture. " + POSE_Q),
        "texture": ("Light grey mangy fur, pale pink scabrous skin "
                    "patches, near-white needle teeth and spine spikes. "
                    + STYLE),
    },
    "lane_wolf": {
        "prompt": ("A lean veteran pack wolf, leaner and rangier than a "
                   "dire wolf, one torn ear, an old brand scar on the "
                   "flank, bone spurs at the shoulders, bared fangs. "
                   + POSE_Q),
        "texture": ("Pale grey short fur, near-white fangs and bone "
                    "spurs, mid-grey brand scar and torn ear. " + STYLE),
    },
    "goblin_straggler": {
        "prompt": ("A hunched goblin deserter, wiry and mean, scrap-metal "
                   "pauldron on one shoulder, dented stolen helm, ragged "
                   "tunic, jagged cleaver in hand, long ears, underbite "
                   "with crooked teeth. " + POSE_B),
        "texture": ("Light sickly green skin, mid-grey scrap iron pauldron "
                    "and helm, light-brown ragged tunic, near-white "
                    "crooked teeth. " + STYLE),
    },
    "ember_shade": {
        # v2 prompt: v1 ("woven from briars and fenceposts") generated
        # disconnected floating arms — force one solid connected mass.
        "prompt": ("A hulking humanoid wood golem, one single solid "
                   "connected body, carved from charred oak beams, thick "
                   "heavy arms firmly joined to broad shoulders, sturdy "
                   "legs, iron nails studding the forearms, glowing ember "
                   "cracks across the chest, hollow burning eyes, short "
                   "thorny spikes on the back. Massive and solid, no "
                   "gaps, no floating parts. " + POSE_B),
        "texture": ("Light ash-grey charred wood weave, near-white "
                    "glowing ember seams and eyes, mid-grey iron nails, "
                    "pale thorns. " + STYLE),
    },
}


def load_key():
    key = os.environ.get("TRIPO_API_KEY")
    if not key and (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text().splitlines():
            if line.startswith("TRIPO_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("No TRIPO_API_KEY (env var or .env next to this script).")
    return key


KEY = load_key()


def api(method, path, body=None):
    req = urllib.request.Request(
        API + path, method=method,
        headers={"Authorization": f"Bearer {KEY}",
                 "Content-Type": "application/json"},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        try:
            out = json.load(e)
        except Exception:
            sys.exit(f"HTTP {e.code} on {path}")
    if out.get("code") == 2010:
        sys.exit("Tripo error 2010: the key has no API credits.")
    if out.get("code") != 0:
        sys.exit(f"API error on {path}: {out}")
    return out["data"]


def wait(task_id, label):
    start = time.time()
    while True:
        d = api("GET", f"/tasks/{task_id}")
        st = d.get("status")
        if st == "success":
            print(f"  {label}: done "
                  f"({d.get('credits_consumed', '?')} credits)", flush=True)
            return d
        if st not in ("queued", "running", "pending"):
            sys.exit(f"{label}: task {task_id} ended '{st}': {d}")
        if time.time() - start > 1800:
            sys.exit(f"{label}: timed out after 30 min ({task_id})")
        time.sleep(8)


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r:
        path.write_bytes(r.read())
    print(f"  saved {path.relative_to(ROOT)} "
          f"({path.stat().st_size // 1024} KB)", flush=True)


def build(asset, spec):
    mpath = OUT / asset / "manifest.json"
    man = json.loads(mpath.read_text()) if mpath.exists() else {}

    def save():
        mpath.parent.mkdir(parents=True, exist_ok=True)
        mpath.write_text(json.dumps(man, indent=2))

    def stage(key, filename, create, preview=False):
        path = OUT / asset / filename
        if man.get(key, {}).get("done") and path.exists():
            print(f"  {key}: already done ({filename})", flush=True)
            return man[key]["task"]
        task_id = create()
        man[key] = {"task": task_id, "done": False}
        save()
        d = wait(task_id, f"{asset}/{key}")
        out = d.get("output", {})
        if out.get("model_url"):
            download(out["model_url"], path)
        if preview and out.get("rendered_image_url"):
            download(out["rendered_image_url"], OUT / asset / "preview.png")
        man[key]["done"] = True
        save()
        return task_id

    print(f"== {asset} ==", flush=True)
    gen = stage("gen", "00_base.glb", lambda: api(
        "POST", "/generation/text-to-model", {
            "prompt": spec["prompt"], "model": GEN_MODEL,
            "face_limit": FACE_LIMIT, "texture": False, "pbr": False,
            "smart_low_poly": True,
        })["task_id"])
    stage("texture", "10_textured.glb", lambda: api(
        "POST", "/models/texture", {
            "input": gen, "model": TEXTURE_MODEL, "pbr": False,
            "texture_prompt": {"text": spec["texture"]},
        })["task_id"], preview=True)


def status():
    bal = api("GET", "/account/balance")
    print(f"balance: {bal['balance']}  frozen: {bal['frozen']}")
    for asset in MONSTERS:
        mpath = OUT / asset / "manifest.json"
        man = json.loads(mpath.read_text()) if mpath.exists() else {}
        done = [k for k, v in man.items() if v.get("done")]
        print(f"  {asset}: {', '.join(done) or '—'}")


def main():
    args = sys.argv[1:]
    if args == ["status"]:
        status()
        return
    picked = set(args) or set(MONSTERS)
    unknown = picked - set(MONSTERS)
    if unknown:
        sys.exit(f"unknown assets: {', '.join(sorted(unknown))}")
    for name, spec in MONSTERS.items():
        if name in picked:
            build(name, spec)
    print("done", flush=True)


if __name__ == "__main__":
    main()
