#!/usr/bin/env python3
"""067 — Arena backgrounds at 320x300 for the Labs turn-based stage.

Same pipeline as gen_bg_floors.py (Gemini designed 1-bit still → density
master → perfect-loop frames → GL sheet), re-parametrized for the taller
arena frame: stills at 1:1 (closest supported aspect), center-cropped to
16:15, the STAGE prompt asks for open ground across the lower third and
a quiet upper third (the HUD sits there). Output: 24 frames of 320x300
baked straight into worldd/static/site/fight3d/backgrounds300/<id>.png
(320x7200, 1-bit) — the sheet arena3d.js samples. Floors 6–7 only.

Usage:
  python3 gen_bg_arena.py stills [id ...]   # Gemini, skips existing jpgs
  python3 gen_bg_arena.py sheets [id ...]   # local, rebuilds sheets
"""
from __future__ import annotations

import asyncio
import os
import sys

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gen_bg_floors as gf          # noqa: E402  (loads demo2 + providers)

g1 = gf.g1
providers = gf.providers

W, H, FRAMES = 320, 300, 24
FLOOR_FRAC = 0.80
OUT = os.path.join(_HERE, "backgrounds_arena")
DST = os.path.join(_HERE, "..", "..", "worldd", "static", "site",
                   "fight3d", "backgrounds300")

IDS = ["grave_moth", "guano_vole", "silk_broodling", "vault_weaver",
       "lane_boar", "wrapped_husk", "warden_006",
       "orchard_wolfpack", "rabid_boar", "hornet_swarm", "windfall_crow",
       "orchard_hare", "windfall_wight", "warden_007"]

STAGE300 = (
    "EMPTY STAGE — absolutely no creatures, no people, no animals, no "
    "figures of any kind. The scene is viewed from the side like a "
    "theater stage, a tall nearly square frame: flat, level open ground "
    "fills the LOWER THIRD of the frame edge to edge — the fighting "
    "floor where combatants will later stand — with nothing tall growing "
    "or standing on it, a designed gradient pool of light falling across "
    "it. All scenery sits BEHIND that open ground in the middle band; "
    "the UPPER THIRD is quiet — dark sky, roof or haze with soft "
    "gradients only, no busy detail (a heads-up display will sit over "
    "it). The ground line is strictly horizontal. "
)


def _retarget():
    g1.W, g1.H, g1.FLOOR_FRAC, g1.OUT = W, H, FLOOR_FRAC, OUT


async def gen_still(sid: str, key: str) -> str:
    cfg = gf.SCENES[sid]
    floor = gf.FLOOR.get(cfg["floor"], "")
    prompt = (gf.STYLE + floor + STAGE300 + cfg["prompt"] +
              " Side-on shot, tall frame.")
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], prompt, aspect="1:1",
        api_key=key)
    if "error" in res:
        return f"FAIL {sid}: {res['error']} — {str(res.get('detail'))[:160]}"
    open(os.path.join(OUT, f"{sid}.jpg"), "wb").write(res["image_bytes"])
    return f"ok   {sid}"


def build_sheet(sid: str) -> str:
    _retarget()
    cfg = gf.SCENES[sid]
    grey = g1.density_master(sid)              # 320x300 via g1.W/H
    mask = g1.glow_mask(grey)
    noises = g1.noise_fields()
    ty, tx = np.indices((H, W))
    thresh = (g1.BAYER8[ty % 8, tx % 8] + 0.5) / 64
    sheet = Image.new("1", (W, H * FRAMES), 0)
    for t in range(FRAMES):
        ph = 2 * np.pi * t / FRAMES
        f = g1.wind_shift(grey, t, cfg["wind"])
        f = f * (1.0 + 0.08 * mask * np.sin(ph + 1.3))
        if cfg["fire"]:
            k = len(noises)
            w = np.array([max(0.0, np.cos(ph - 2 * np.pi * j / k)) ** 2
                          for j in range(k)])
            w /= w.sum()
            flick = sum(wj * nj for wj, nj in zip(w, noises))
            f = f + 0.10 * mask * flick
        bits = np.where(np.clip(f, 0, 1) > thresh, 255, 0).astype(np.uint8)
        sheet.paste(Image.fromarray(bits).convert("1"), (0, t * H))
    os.makedirs(DST, exist_ok=True)
    out = os.path.join(DST, f"{sid}.png")
    sheet.save(out, optimize=True)
    still = np.where(grey > thresh, 255, 0).astype(np.uint8)
    Image.fromarray(still).convert("RGB").resize(
        (W * 2, H * 2), Image.NEAREST).save(
        os.path.join(OUT, f"{sid}_still.png"))
    return f"sheet {sid} -> {out} ({os.path.getsize(out) // 1024} KB)"


async def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("stills", "sheets"):
        sys.exit(__doc__)
    mode, names = sys.argv[1], sys.argv[2:]
    os.makedirs(OUT, exist_ok=True)
    bad = [n for n in names if n not in IDS]
    if bad:
        sys.exit(f"unknown ids: {bad}")
    if mode == "stills":
        key = g1.api_key()
        todo = names or [s for s in IDS if not os.path.exists(
            os.path.join(OUT, f"{s}.jpg"))]
        print(f"{len(todo)} stills -> {OUT}")
        for i in range(0, len(todo), 4):
            for line in await asyncio.gather(
                    *(gen_still(n, key) for n in todo[i:i + 4])):
                print(line, flush=True)
    else:
        todo = names or [s for s in IDS if os.path.exists(
            os.path.join(OUT, f"{s}.jpg"))]
        for n in todo:
            print(build_sheet(n), flush=True)
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
