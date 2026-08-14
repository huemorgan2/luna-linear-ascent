#!/usr/bin/env python3
"""Bake the demo2 background GIF loops into GL spritesheets (PLAN4).

The kill-scene law bans GIF pixels on the floor-1 death card, so the
scenery moves into the post shader: each 24-frame 320x112 loop becomes
one vertical 320x2688 1-bit PNG, sampled per-frame by fight3d.js
(white -> uInk, black -> black — the frame stays one color).

Usage: python3 make_bg_sheets.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "demo2" / "backgrounds"
DST = (HERE.parent.parent / "worldd" / "static" / "site" / "fight3d"
       / "backgrounds")
W, H, FRAMES = 320, 112, 24

DST.mkdir(parents=True, exist_ok=True)
for gif in sorted(SRC.glob("*.gif")):
    im = Image.open(gif)
    sheet = Image.new("1", (W, H * FRAMES), 0)
    n = getattr(im, "n_frames", 1)
    for i in range(FRAMES):
        im.seek(i % n)
        fr = im.convert("L").point(lambda v: 255 if v >= 128 else 0, "1")
        sheet.paste(fr, (0, i * H))
    out = DST / f"{gif.stem}.png"
    sheet.save(out, optimize=True)
    print(f"{out.name}: {out.stat().st_size // 1024} KB ({n} frames in)")
