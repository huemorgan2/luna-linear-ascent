#!/usr/bin/env python3
"""Enforce the accepted floor-1 grid/tone recipe on model-designed map art.

Usage: python prepare_map.py SOURCE OUTPUT
Keeps the 082 phase-1g parameters verbatim; does not modify the source.
"""
from pathlib import Path
import argparse
from PIL import Image, ImageFilter, ImageOps

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("source", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
W, H = 492, 369
INK = (217, 217, 211, 255)

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]

img = Image.open(args.source).convert("L")
# phase-1b: the model paints a decorative black frame — trim it before
# the crop so the frame never eats map real estate.
_bb = img.point(lambda p: 255 if p > 40 else 0).getbbox()
if _bb:
    img = img.crop(_bb)
w, h = img.size
target = W / H
if w / h > target:
    nw = int(h * target)
    img = img.crop(((w - nw) // 2, 0, (w + nw) // 2, h))
else:
    nh = int(w / target)
    img = img.crop((0, (h - nh) // 2, w, (h + nh) // 2))
img = img.resize((W, H), Image.LANCZOS)
# phase-1c: the downscale blurs the engraving's thin lines to mid-grey,
# which the dither turns to speckle — an unsharp pass re-crisps them
# (the winch wheels and the small door live or die on this).
img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=180, threshold=2))
img = ImageOps.autocontrast(img, cutoff=1)   # keep the gradient ramps wide
# The model paints on light-grey paper; the game is ink on black. Gamma
# pushes the flat mid-grey ground down to sparse dither while lit faces,
# the stream and the glow pools stay bright.
# phase-1f: the raw is model-DESIGNED dither art now (vision/
# 1bit-images.md discipline) — grey washes died white. 1.15 lands the
# mountain band's tonal spread exactly on the phase-1d reference.
# phase-1g: highlight ceiling 0.85 — pure paper dithers at ~85%
# density instead of saturating to solid ink, so nothing burns white;
# below 0.85 the mountains' lit ridge faces go flat.
img = img.point(lambda p: int(255 * ((p / 255) ** 1.15) * 0.85))

out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
po = out.load()
pi = img.load()
for y in range(H):
    for x in range(W):
        if pi[x, y] / 255 > (BAYER[y % 8][x % 8] + 0.5) / 64:
            po[x, y] = INK

args.output.parent.mkdir(parents=True, exist_ok=True)
out.save(args.output)
print(f"wrote {args.output}")
