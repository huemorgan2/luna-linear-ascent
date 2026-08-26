#!/usr/bin/env python3
"""Floor 1 map — the Fencerows, model-painted, forced to true 1-bit.

Pipeline = the banner discipline (tools/generate_banners.py), map-shaped:
  1. Gemini (nano-banana-pro via .cursor/skills/gemini-image/scripts/gen.py)
     paints a high-angle aerial 1-bit-styled map — sculpted 3D volumes with
     lit faces and cast shadows, NOT flat icons; the gate arch + camp at the
     very center; mountain + keep upper right; a bright stream winding
     across; burnt farmhouse, market cross, culvert, bridge, hedged fields;
     terrain running past all four edges (the floor is far bigger than the
     map).  ->  raw_map.png
  2. This script forces it to spec: center-crop 4:3, downscale to the
     native 640x480 grid, autocontrast, Bayer 8x8 ordered dither ->
     exactly two states, ink #d9d9d3 (--art) on black.

Labels/markers are NEVER in the pixels — the mock overlays them as HTML
(the scene is dithered, the UI is typography).

Usage: python3 map_gen.py   (needs raw_map.png beside it)
       -> map_001_492x369.png
"""

from PIL import Image, ImageOps

W, H = 492, 369   # phase-1b (roy): 77% of 640x480
INK = (217, 217, 211, 255)      # --art

BAYER = [
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
]

img = Image.open("raw_map.png").convert("L")
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
img = ImageOps.autocontrast(img, cutoff=1)   # keep the gradient ramps wide
# The model paints on light-grey paper; the game is ink on black. Gamma
# pushes the flat mid-grey ground down to sparse dither while lit faces,
# the stream and the glow pools stay bright.
img = img.point(lambda p: int(255 * (p / 255) ** 1.45))

out = Image.new("RGBA", (W, H), (0, 0, 0, 255))
po = out.load()
pi = img.load()
for y in range(H):
    for x in range(W):
        if pi[x, y] / 255 > (BAYER[y % 8][x % 8] + 0.5) / 64:
            po[x, y] = INK

out.save("map_001_492x369.png")
print("wrote map_001_492x369.png")
