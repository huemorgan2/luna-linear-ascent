#!/usr/bin/env python3
"""Generate the game's player characters + weapons with the Tripo3D API.

Pipeline per character (species matrix from ../PLAN2.md — elf|giant|human):
  1. text-to-model  (bare geometry, face_limit 2000 — roy's website recipe)
  2. texture        (texture_prompt written for the 1-bit dither pipeline,
                     per plugin-linear-ascent/vision/1bit-images.md: flat
                     regions, strong tonal separation, no micro-texture)
  3. auto-rig       (biped, mixamo bone names)
  4. retarget       (preset:biped:idle — the breathing stance)

Weapons (blade|bow|staff) stop after step 2 — they are static props the
viewer attaches to the characters' hand bone.

Everything is resumable: task ids + downloaded files are recorded in
models/manifest.json; finished stages are skipped on re-run.

Usage:
  python3 "gen_models.py"            # everything
  python3 "gen_models.py" status     # balance + manifest state
  python3 "gen_models.py" giant bow  # only the named assets

Key: TRIPO_API_KEY env var, or .env next to this file.
NOTE: Tripo bills web-app credits and API credits separately — a key from
an account with only web credits gets error 2010 on every task.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "models"
API = "https://openapi.tripo3d.ai/v3"

GEN_MODEL = "v3.0-20250812"      # stable; v3.1-20260211 = latest quality
TEXTURE_MODEL = "v3.0-20250812"  # must match the generation family
RIG_MODEL = "v1.0-20240301"      # biped-only, 90+ presets incl. idle
FACE_LIMIT = 2000                # roy's website recipe for the giant
IDLE = "preset:biped:idle"       # the breathing stance

# The texture request, phrased for the 1-bit pipeline (1bit-images.md):
# tonal separation by design, flat micro-texture, bold readable regions.
# Palette rule (the 1bit-images.md closeup lesson): never paint the figure
# dark — dark regions fall below the dither threshold and vanish into the
# black stage. Everything lives in the light-to-mid band; separation comes
# from mid-vs-light steps, and solid black stays reserved for the ink edges.
STYLE = (
    "Flat hand-painted game texture designed for 1-bit dithered pixel-art "
    "rendering. The WHOLE texture stays in the LIGHT-TO-MID tonal range — "
    "nothing darker than mid-grey, no black, no deep shadows. Large "
    "uniform colour regions with clear tonal steps between neighbouring "
    "regions (near-white against light against mid-tone), no fine "
    "micro-texture, no noise, no photorealistic surface detail, matte, "
    "bold simple readable shapes, bright and evenly lit."
)

CHARACTERS = {
    "giant": {
        "prompt": (
            "A giant, wide and tall, bulky and massive, with the beard and "
            "hair of a dwarf. Heavy build, thick arms, broad chest, simple "
            "worker tunic, heavy leather boots. Fantasy game character "
            "standing upright in A-pose, arms slightly away from the body, "
            "empty open hands."),
        "texture": ("Mid-grey tunic, mid-tone leather boots, light warm "
                    "skin, near-white beard and hair. " + STYLE),
    },
    "elf": {
        "prompt": (
            "A slim tall male elf ranger with long hair and pointed ears, "
            "cloak with the hood down, light tunic, high boots. Fantasy "
            "game character standing upright in A-pose, arms slightly away "
            "from the body, empty open hands."),
        "texture": ("Mid-tone green-grey cloak and boots, light skin, pale "
                    "near-white hair, light tunic. " + STYLE),
    },
    "human": {
        "prompt": (
            "A human woman fighter with practical armour: steel pauldrons "
            "on the shoulders, leather cuirass, hair tied in buns, athletic "
            "build. Fantasy game character standing upright in A-pose, arms "
            "slightly away from the body, empty open hands."),
        "texture": ("Mid-tone leather armour, near-white steel pauldrons, "
                    "light skin, mid-grey hair. " + STYLE),
    },
}

WEAPONS = {
    "blade": {
        "prompt": ("A one-handed medieval longsword, straight blade, simple "
                   "crossguard, leather-wrapped grip, blade pointing up. "
                   "Fantasy game prop, single object."),
        "texture": ("Bright polished near-white steel blade, mid-tone "
                    "leather grip, mid-grey crossguard. " + STYLE),
    },
    "bow": {
        "prompt": ("A wooden recurve bow with a taut string, simple curved "
                   "limbs, leather grip in the middle. Fantasy game prop, "
                   "single object."),
        "texture": ("VERY PALE near-white birch wood limbs — absolutely no "
                    "dark wood, no black, no brown — light-grey leather "
                    "grip, bright near-white string. " + STYLE),
    },
    "staff": {
        "prompt": ("A wizard's staff of gnarled wood, as tall as a person, "
                   "a small rough crystal held in twisted roots at the top. "
                   "Fantasy game prop, single object."),
        "texture": ("Mid-tone grey-brown gnarled wood, bright glowing "
                    "near-white crystal at the top. " + STYLE),
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
        sys.exit(
            "\nTripo error 2010: the key has no API credits.\n"
            "API credits are separate from tripo3d.ai web-app credits — "
            "top up at https://platform.tripo3d.ai/billing (API billing), "
            "then re-run; finished stages are skipped.")
    if out.get("code") != 0:
        sys.exit(f"API error on {path}: {out}")
    return out["data"]


def wait(task_id, label):
    start = time.time()
    while True:
        d = api("GET", f"/tasks/{task_id}")
        st = d.get("status")
        if st == "success":
            print(f"\r  {label}: done "
                  f"({d.get('credits_consumed', '?')} credits)      ")
            return d
        if st not in ("queued", "running", "pending"):
            sys.exit(f"\n{label}: task {task_id} ended '{st}': {d}")
        if time.time() - start > 1800:
            sys.exit(f"\n{label}: timed out after 30 min ({task_id})")
        print(f"\r  {label}: {st} {d.get('progress', 0)}%   ",
              end="", flush=True)
        time.sleep(6)


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r:
        path.write_bytes(r.read())
    print(f"  saved {path.relative_to(ROOT)} "
          f"({path.stat().st_size // 1024} KB)")


def load_manifest():
    p = OUT / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_manifest(m):
    OUT.mkdir(exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(m, indent=2))


MANIFEST = load_manifest()


def stage(asset, key, filename, create, preview=False):
    """Run one pipeline stage unless its file already exists. Returns task id."""
    entry = MANIFEST.setdefault(asset, {})
    path = OUT / asset / filename
    if entry.get(key, {}).get("done") and path.exists():
        print(f"  {key}: already done ({filename})")
        return entry[key]["task"]
    task_id = create()
    entry[key] = {"task": task_id, "done": False}
    save_manifest(MANIFEST)
    d = wait(task_id, f"{asset}/{key}")
    out = d.get("output", {})
    if out.get("model_url"):
        download(out["model_url"], path)
    if preview and out.get("rendered_image_url"):
        download(out["rendered_image_url"], OUT / asset / "preview.png")
    entry[key]["done"] = True
    save_manifest(MANIFEST)
    return task_id


def build(asset, spec, rig):
    print(f"\n== {asset} ==")
    gen = stage(asset, "gen", "00_base.glb", lambda: api(
        "POST", "/generation/text-to-model", {
            "prompt": spec["prompt"], "model": GEN_MODEL,
            "face_limit": FACE_LIMIT, "texture": False, "pbr": False,
            "smart_low_poly": True,   # game topology: clean hand-crafted-style mesh

        })["task_id"])
    tex = stage(asset, "texture", "10_textured.glb", lambda: api(
        "POST", "/models/texture", {
            "input": gen, "model": TEXTURE_MODEL, "pbr": False,
            "texture_prompt": {"text": spec["texture"]},
        })["task_id"], preview=True)
    if not rig:
        return
    rigged = stage(asset, "rig", "20_rigged.glb", lambda: api(
        "POST", "/animations/rig", {
            "input": tex, "model": RIG_MODEL, "rig_type": "biped",
            "spec": "tripo", "out_format": "glb",   # presets can't retarget mixamo rigs (error 1004)
        })["task_id"])
    stage(asset, "idle", "30_idle.glb", lambda: api(
        "POST", "/animations/retarget", {
            "input": rigged, "animation": IDLE, "out_format": "glb",
            "bake_animation": True, "animate_in_place": True,
        })["task_id"])
    # attack clips, one per weapon type; the viewer plays them on the
    # 30_idle.glb skeleton (same rig, tracks bind by bone name)
    for key, anim, fname in [
        ("slash", "preset:biped:slash",        "40_slash.glb"),
        ("shoot", "preset:biped:bow",          "41_shoot.glb"),
        ("cast",  "preset:biped:cast_a_spell", "42_cast.glb"),
    ]:
        stage(asset, key, fname, lambda a=anim: api(
            "POST", "/animations/retarget", {
                "input": rigged, "animation": a, "out_format": "glb",
                "bake_animation": True, "animate_in_place": True,
            })["task_id"])


def status():
    bal = api("GET", "/account/balance")
    print(f"balance: {bal['balance']}  frozen: {bal['frozen']}")
    for asset in list(CHARACTERS) + list(WEAPONS):
        entry = MANIFEST.get(asset, {})
        done = [k for k, v in entry.items() if v.get("done")]
        print(f"  {asset}: {', '.join(done) or '—'}")


def main():
    args = [a for a in sys.argv[1:]]
    if args == ["status"]:
        status()
        return
    picked = set(args) or set(CHARACTERS) | set(WEAPONS)
    unknown = picked - set(CHARACTERS) - set(WEAPONS)
    if unknown:
        sys.exit(f"unknown assets: {', '.join(sorted(unknown))}")
    for name, spec in CHARACTERS.items():
        if name in picked:
            build(name, spec, rig=True)
    for name, spec in WEAPONS.items():
        if name in picked:
            build(name, spec, rig=False)
    print("\nAll done. Open index.html (see README.md) to view.")


if __name__ == "__main__":
    main()
