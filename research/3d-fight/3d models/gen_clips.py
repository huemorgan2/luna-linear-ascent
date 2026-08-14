#!/usr/bin/env python3
"""Fetch fight clips for the rigged characters via Tripo retarget presets.

Each character's rig task feeds /animations/retarget once per preset. The
result GLB carries the same mixamo-named skeleton as 30_idle.glb, so demo2
extracts just the AnimationClip and plays it on the loaded character.

Presets (rig v1.0-20240301, from the retarget docs):
  slash -> preset:biped:slash          the blade strike
  shoot -> preset:biped:shoot         the bow release
  cast  -> preset:biped:cast_a_spell  the staff beam

Usage:
  python3 gen_clips.py               # all characters x all clips
  python3 gen_clips.py giant slash   # subset (any mix of names)

Resumable like gen_models.py — task ids land in models/manifest.json as
clip_<name>, files as models/<char>/40_<name>.glb.
"""
import sys

from gen_models import MANIFEST, api, stage

CHARS = ("giant", "elf", "human")
CLIPS = {
    "slash": "preset:biped:slash",
    "shoot": "preset:biped:shoot",
    "cast": "preset:biped:cast_a_spell",
}


def main():
    args = set(sys.argv[1:])
    unknown = args - set(CHARS) - set(CLIPS)
    if unknown:
        sys.exit(f"unknown names: {', '.join(sorted(unknown))}")
    chars = [c for c in CHARS if not (args & set(CHARS)) or c in args]
    clips = [k for k in CLIPS if not (args & set(CLIPS)) or k in args]
    for c in chars:
        rig = MANIFEST.get(c, {}).get("rig", {})
        if not rig.get("done"):
            sys.exit(f"{c}: no finished rig in manifest — run gen_models.py")
        print(f"\n== {c} ==")
        for k in clips:
            stage(c, f"clip_{k}", f"40_{k}.glb", lambda k=k: api(
                "POST", "/animations/retarget", {
                    "input": rig["task"], "animation": CLIPS[k],
                    "out_format": "glb", "bake_animation": True,
                    "animate_in_place": True,
                })["task_id"])
    print("\nAll clips done.")


if __name__ == "__main__":
    main()
