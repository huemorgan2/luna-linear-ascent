#!/usr/bin/env python3
"""Rig the floor-1 monsters and bake a real WALK cycle (PLAN4).

PLAN3 shipped the monsters rigless with a procedural bob; roy rejected
it — feet must actually move, like the mock's players. Tripo rig
v2.5-20260210 rigs non-humanoids, so each creature gets:

  rig (rig_type per body plan) -> retarget walk -> 50_walk.glb

The result is a self-contained animated GLB (geometry + texture + one
AnimationClip); fight3d.js plays the clip with an AnimationMixer and
keeps the attack lunge procedural on top. Quadrupeds have exactly one
preset (preset:quadruped:walk); bipeds use preset:walk.

Resumable — tasks land in the same per-creature manifest that
gen_monsters.py writes (models/monsters/{id}/manifest.json).

Usage:
  python3 gen_monster_clips.py             # all six
  python3 gen_monster_clips.py grey_wolf   # subset
  python3 gen_monster_clips.py status
"""
import json
import sys

from gen_monsters import OUT, api, download, wait

# rig v2.5 is the NON-humanoid rigger (quadruped/hexapod/...); it mislabels
# a humanoid's limbs and preset:walk comes out as a folded, headless mess
# (six goblin attempts, 2026-08-15). Bipeds must use the humanoid v1.0
# rigger, spec "tripo" (mixamo skeletons cannot be retargeted).
RIG_MODEL = {"quadruped": "v2.5-20260210", "biped": "v1.0-20240301"}

# body plan per creature — the wolves, boar and rat walk on four legs;
# the goblin is the one biped (v3: the ember shade is a flame hound)
PLANS = {
    "grey_wolf": "quadruped",
    "feral_boar": "quadruped",
    "hedge_rat": "quadruped",
    "lane_wolf": "quadruped",
    "goblin_straggler": "biped",
    "ember_shade": "quadruped",   # v3: hound of flame
}
WALK = {"quadruped": "preset:quadruped:walk", "biped": "preset:walk"}


def run(cid):
    plan = PLANS[cid]
    mpath = OUT / cid / "manifest.json"
    man = json.loads(mpath.read_text()) if mpath.exists() else {}
    if not man.get("texture", {}).get("done"):
        sys.exit(f"{cid}: no finished texture — run gen_monsters.py first")

    def save():
        mpath.write_text(json.dumps(man, indent=2))

    def stage(key, filename, create):
        path = OUT / cid / filename
        if man.get(key, {}).get("done") and (not filename or path.exists()):
            print(f"  {key}: already done", flush=True)
            return man[key]["task"]
        task_id = man.get(key, {}).get("task") or create()
        man[key] = {"task": task_id, "done": False}
        save()
        d = wait(task_id, f"{cid}/{key}")
        out = d.get("output", {})
        if filename and out.get("model_url"):
            download(out["model_url"], path)
        man[key]["done"] = True
        save()
        return task_id

    print(f"== {cid} ({plan}) ==", flush=True)
    rig = stage("rig", "20_rigged.glb", lambda: api(
        "POST", "/animations/rig", {
            "input": man["texture"]["task"], "model": RIG_MODEL[plan],
            "spec": "tripo",
            "rig_type": plan, "out_format": "glb",
        })["task_id"])
    stage("walk", "50_walk.glb", lambda: api(
        "POST", "/animations/retarget", {
            "input": rig, "animation": WALK[plan],
            "out_format": "glb", "bake_animation": True,
            "animate_in_place": True,
        })["task_id"])


def status():
    bal = api("GET", "/account/balance")
    print(f"balance: {bal['balance']}  frozen: {bal['frozen']}")
    for cid in PLANS:
        mpath = OUT / cid / "manifest.json"
        man = json.loads(mpath.read_text()) if mpath.exists() else {}
        rig = "rig✓" if man.get("rig", {}).get("done") else "rig…" \
            if man.get("rig", {}).get("task") else "rig—"
        wk = "walk✓" if man.get("walk", {}).get("done") else "walk…" \
            if man.get("walk", {}).get("task") else "walk—"
        glb = "glb✓" if (OUT / cid / "50_walk.glb").exists() else "glb—"
        print(f"  {cid:18s} {rig} {wk} {glb}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["status"]:
        status()
        sys.exit(0)
    todo = args or list(PLANS)
    unknown = set(todo) - set(PLANS)
    if unknown:
        sys.exit(f"unknown: {', '.join(sorted(unknown))}")
    for cid in todo:
        run(cid)
    print("\nAll walk clips done.")
