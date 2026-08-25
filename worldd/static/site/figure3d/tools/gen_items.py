#!/usr/bin/env python3
"""071: generate level-≤10 item GLBs with the Tripo3D API.

Lives inside worldd/static/site/figure3d/ so dropping the Labs folder
drops the generator. Resumable via models/manifest.json.

Usage:
  python3 tools/gen_items.py            # everything missing
  python3 tools/gen_items.py status
  python3 tools/gen_items.py cobbled_boots luck_charm
  python3 tools/gen_items.py --families   # only the fallback meshes

Key: TRIPO_API_KEY, or research/3d-fight/3d models/.env
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_LOCK = threading.Lock()

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                     # figure3d/
OUT = ROOT / "models"                  # raw Tripo sources + manifest stay here
# finished runtime items live in the shared lib (plan 080) — both 3D
# scenes load them from there
ITEMS = ROOT.parent / "lib" / "models" / "items"
API = "https://openapi.tripo3d.ai/v3"

# walk up to the workspace so we can import economy + the existing .env
WS = HERE
for _ in range(8):
    if (WS / "plugin-linear-ascent" / "plugin_linear_ascent").is_dir():
        break
    WS = WS.parent
sys.path.insert(0, str(WS / "plugin-linear-ascent"))

GEN_MODEL = "v3.0-20250812"
TEXTURE_MODEL = "v3.0-20250812"
FACE_LIMIT = 1800
CONCURRENCY = 3

STYLE = (
    "Flat hand-painted game texture designed for 1-bit dithered pixel-art "
    "rendering. The WHOLE texture stays in the LIGHT-TO-MID tonal range — "
    "nothing darker than mid-grey, no black, no deep shadows. Large "
    "uniform colour regions with clear tonal steps between neighbouring "
    "regions (near-white against light against mid-tone), no fine "
    "micro-texture, no noise, no photorealistic surface detail, matte, "
    "bold simple readable shapes, bright and evenly lit."
)

KIND_PROMPT = {
    "weapon:blade": (
        "A one-handed fantasy {name}, {flavor}. Single weapon prop, "
        "blade pointing up, simple grip, chunky readable silhouette, "
        "no stand, no character."),
    "weapon:bow": (
        "A wooden {name}, {flavor}. Single recurve or shortbow prop, "
        "taut string, upright, chunky limbs that read at low resolution, "
        "no stand, no character."),
    "weapon:staff": (
        "A wizard's {name}, {flavor}. Single staff prop as tall as a "
        "person, upright, a small focus at the top, chunky wood, "
        "no stand, no character."),
    "shield": (
        "A {name}, {flavor}. Single round or kite shield prop, face "
        "toward camera, chunky rim, no stand, no character."),
    "focus": (
        "A sorcerer's {name}, {flavor}. Single small handheld focus "
        "prop — orb, lens, bead or fetish — isolated, chunky, "
        "no stand, no character."),
    "armor": (
        "A wearable {name}, {flavor}. Single empty chest-piece / "
        "jerkin / coat prop, hollow, no body inside, front facing, "
        "chunky plates, no stand."),
    "shoes": (
        "A pair of {name}, {flavor}. Two matching fantasy boots side "
        "by side, chunky leather, no legs, no stand."),
    "charm": (
        "A {name} pendant on a short leather cord, {flavor}. Small "
        "amulet, isolated, chunky, no neck, no character."),
}

FAMILIES = {
    "blade": {
        "prompt": ("A one-handed medieval longsword, straight blade, simple "
                   "crossguard, leather-wrapped grip, blade pointing up. "
                   "Fantasy game prop, single object."),
        "texture": ("Bright polished near-white steel blade, mid-tone "
                    "leather grip, mid-grey crossguard. " + STYLE),
        "hold": "blade",
    },
    "bow": {
        "prompt": ("A wooden recurve bow with a taut string, simple curved "
                   "limbs, leather grip in the middle. Fantasy game prop, "
                   "single object."),
        "texture": ("VERY PALE near-white birch wood limbs — absolutely no "
                    "dark wood, no black, no brown — light-grey leather "
                    "grip, bright near-white string. " + STYLE),
        "hold": "bow",
    },
    "staff": {
        "prompt": ("A wizard's staff of gnarled wood, as tall as a person, "
                   "a small rough crystal held in twisted roots at the top. "
                   "Fantasy game prop, single object."),
        "texture": ("Mid-tone grey-brown gnarled wood, bright glowing "
                    "near-white crystal at the top. " + STYLE),
        "hold": "staff",
    },
    "shield": {
        "prompt": ("A round wooden buckler with an iron boss, chunky rim, "
                   "single shield prop facing the camera, no stand."),
        "texture": ("Pale wood face, mid-grey iron boss and rim. " + STYLE),
        "hold": "shield",
    },
    "focus": {
        "prompt": ("A small glass bead focus in a simple claw setting, "
                   "handheld sorcerer's orb, isolated, no stand."),
        "texture": ("Near-white glass, mid-grey metal claw. " + STYLE),
        "hold": "focus",
    },
    "armor": {
        "prompt": ("An empty padded leather jerkin / chest piece, hollow, "
                   "no body inside, front facing, chunky straps, no stand."),
        "texture": ("Mid-tone leather, near-white stitching. " + STYLE),
        "hold": "armor",
    },
    "boots": {
        "prompt": ("A pair of cobbled leather fantasy boots, chunky, "
                   "side by side, no legs, no stand."),
        "texture": ("Mid-tone leather, pale soles. " + STYLE),
        "hold": "shoes",
    },
    "charm": {
        "prompt": ("A small good-luck charm pendant on a short leather "
                   "cord, simple carved token, isolated, no neck."),
        "texture": ("Pale carved bone token, mid-tone cord. " + STYLE),
        "hold": "charm",
    },
}


def load_key() -> str:
    key = os.environ.get("TRIPO_API_KEY")
    env = (WS / "research" / "3d-fight" / "3d models" / ".env")
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("TRIPO_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("No TRIPO_API_KEY (env var or research/3d-fight/3d models/.env).")
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
        raise RuntimeError(f"API error on {path}: {out}")
    return out["data"]


def wait(task_id, label):
    start = time.time()
    while True:
        d = api("GET", f"/tasks/{task_id}")
        st = d.get("status")
        if st == "success":
            print(f"\r  {label}: done "
                  f"({d.get('credits_consumed', '?')} cr)      ")
            return d
        if st not in ("queued", "running", "pending"):
            raise RuntimeError(f"{label}: ended '{st}': {d}")
        if time.time() - start > 1800:
            raise RuntimeError(f"{label}: timed out ({task_id})")
        print(f"\r  {label}: {st} {d.get('progress', 0)}%   ",
              end="", flush=True)
        time.sleep(6)


def download(url, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Tripo's CloudFront signed URLs 403 the default Python-urllib UA.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        path.write_bytes(r.read())
    print(f"  saved {path.relative_to(ROOT)} "
          f"({path.stat().st_size // 1024} KB)")


def load_manifest():
    p = OUT / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def save_manifest(m):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(m, indent=2))


def stage(man, asset, key, dest: Path, create):
    with _LOCK:
        entry = man.setdefault(asset, {})
        if entry.get(key, {}).get("done") and dest.exists():
            print(f"  {asset}/{key}: already done")
            return entry[key]["task"]
        prior = entry.get(key, {}).get("task")
    task_id = prior or create()
    with _LOCK:
        entry = man.setdefault(asset, {})
        entry[key] = {"task": task_id, "done": False}
        save_manifest(man)
    d = wait(task_id, f"{asset}/{key}")
    out = d.get("output", {})
    url = out.get("model_url") or out.get("pbr_model_url") or out.get("base_model_url")
    if url:
        download(url, dest)
    elif dest.name.endswith(".glb") and (OUT / asset / "00_base.glb").exists():
        dest.write_bytes((OUT / asset / "00_base.glb").read_bytes())
    with _LOCK:
        entry = man.setdefault(asset, {})
        entry[key] = {"task": task_id, "done": dest.exists(),
                      "credits": d.get("credits_consumed")}
        save_manifest(man)
    return task_id


def build(man, asset, spec):
    print(f"\n== {asset} ==")
    dest = ITEMS / f"{asset}.glb"
    gen = stage(man, asset, "gen", OUT / asset / "00_base.glb", lambda: api(
        "POST", "/generation/text-to-model", {
            "prompt": spec["prompt"], "model": GEN_MODEL,
            "face_limit": FACE_LIMIT, "texture": False, "pbr": False,
            "smart_low_poly": True,
        })["task_id"])
    stage(man, asset, "texture", dest, lambda: api(
        "POST", "/models/texture", {
            "input": gen, "model": TEXTURE_MODEL, "pbr": False,
            "texture_prompt": {"text": spec["texture"]},
        })["task_id"])


def item_specs():
    from plugin_linear_ascent import economy
    out = {}
    for g in economy.FORGE.values():
        if g.style:
            continue
        if economy.rung_player_level_req(g) > 10:
            continue
        if g.slot == "weapon":
            path = economy.PATH_OF_LINE.get(g.line or "", "blade")
            kind = f"weapon:{path}"
            hold = path
        elif g.slot == "shield" and g.line == "sorcerer":
            kind, hold = "focus", "focus"
        else:
            kind = hold = g.slot
        tmpl = KIND_PROMPT.get(kind, KIND_PROMPT.get(g.slot, KIND_PROMPT["charm"]))
        out[g.slug] = {
            "prompt": tmpl.format(name=g.name, flavor=g.flavor or "plain"),
            "texture": STYLE,
            "hold": hold,
            "slot": g.slot,
            "line": g.line,
            "name": g.name,
        }
    out["luck_charm"] = {
        "prompt": KIND_PROMPT["charm"].format(
            name="Luck charm", flavor="a worn good-luck token"),
        "texture": STYLE,
        "hold": "charm",
        "slot": "charm",
        "line": "",
        "name": "Luck charm",
    }
    return out


def write_catalog(specs):
    rows = {}
    for slug, spec in specs.items():
        hold = spec["hold"]
        family = {
            "blade": "blade", "bow": "bow", "staff": "staff",
            "shield": "shield", "focus": "focus", "armor": "armor",
            "shoes": "boots", "charm": "charm", "potion": "charm",
        }.get(hold, "charm")
        dest = ITEMS / f"{slug}.glb"
        fam = ITEMS / f"{family}.glb"
        rows[slug] = {
            "hold": hold,
            "slot": spec.get("slot", ""),
            "line": spec.get("line", ""),
            "name": spec.get("name", slug),
            "file": f"items/{slug}.glb" if dest.exists() else None,
            "fallback": f"items/{family}.glb" if fam.exists() else None,
        }
    for fam, spec in FAMILIES.items():
        dest = ITEMS / f"{fam}.glb"
        rows[f"_{fam}"] = {
            "hold": spec["hold"],
            "slot": spec["hold"],
            "line": "",
            "name": fam,
            "file": f"items/{fam}.glb" if dest.exists() else None,
            "fallback": None,
        }
    (ROOT / "catalog.json").write_text(json.dumps(rows, indent=2))
    print(f"catalog: {len(rows)} rows → {ROOT / 'catalog.json'}")


def status():
    bal = api("GET", "/account/balance")
    print(f"balance: {bal['balance']}  frozen: {bal['frozen']}")
    man = load_manifest()
    for asset, entry in sorted(man.items()):
        done = [k for k, v in entry.items() if isinstance(v, dict) and v.get("done")]
        print(f"  {asset}: {', '.join(done) or '—'}")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    flags = {a for a in sys.argv[1:] if a.startswith("-")}
    if args == ["status"]:
        status()
        return
    man = load_manifest()
    specs = dict(FAMILIES)
    if "--families" not in flags:
        specs.update(item_specs())
    picked = set(args) or set(specs)
    unknown = picked - set(specs)
    if unknown:
        sys.exit(f"unknown assets: {', '.join(sorted(unknown))}")

    def run(name):
        # each thread gets its own manifest slice; we lock via rewrite
        build(man, name, specs[name])

    names = [n for n in specs if n in picked]
    if CONCURRENCY <= 1 or len(names) == 1:
        for n in names:
            try:
                run(n)
            except Exception as e:
                print(f"FAIL {n}: {e}")
    else:
        with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
            futs = {pool.submit(run, n): n for n in names}
            for fut in as_completed(futs):
                n = futs[fut]
                err = fut.exception()
                if err:
                    print(f"FAIL {n}: {err}")
    write_catalog(item_specs())
    print("\nDone. See catalog.json / ../lib/models/items/.")


if __name__ == "__main__":
    main()
