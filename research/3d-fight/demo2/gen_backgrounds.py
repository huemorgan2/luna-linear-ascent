#!/usr/bin/env python3
"""3d-fight demo2: floor-1 backgrounds at the game's exact 320x112.

Same pipeline as demo1 (designed 1-bit dither still -> density master ->
procedural perfect-loop GIF, fixed Bayer), but on the event-art grid:
320x112, generated at 21:9 (closest supported aspect) and center-cropped.
Scene prompts carry the floor_001.yaml arrival flavor.

Usage:
  python gen_backgrounds.py stills [id ...]   # model calls, skips existing
  python gen_backgrounds.py gifs   [id ...]   # local, always rebuilds
Key: LUNA_GEMINI_API_KEY from env, falling back to ../../../luna/.env.
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys

import numpy as np
from PIL import Image, ImageFilter, ImageOps

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..", "..", "..")
OUT = os.path.join(_HERE, "backgrounds")

_prov = os.path.join(_ROOT, "plugin-image-gen",
                     "plugin_image_gen", "providers.py")
if not os.path.exists(_prov):   # the plugin moved into luna-plugins
    _prov = os.path.join(_ROOT, "..", "luna-plugins", "plugins",
                         "plugin-image-gen", "plugin_image_gen",
                         "providers.py")
_spec = importlib.util.spec_from_file_location("providers", _prov)
providers = importlib.util.module_from_spec(_spec)
sys.modules["providers"] = providers
_spec.loader.exec_module(providers)

W, H = 320, 112
FRAMES, FRAME_MS = 24, 100
FLOOR_FRAC = 0.91          # floor line: combatants' feet at 0.78 * H
BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
])

# Exactly the shipped banner discipline (tools/generate_banners.py):
# the model paints designed gradients; the LOCAL post pass owns the
# dither. Never ask for "chunky dither pixels" — painted dither turns
# to mid-density mush when downscaled to the grid.
STYLE = (
    "1-bit pixel art banner in the classic Macintosh / Playdate / 1-bit "
    "Akira poster style. STRICTLY two colors: pure black and pure white "
    "— every midtone rendered as ordered Bayer dithering. The image "
    "must be FULL OF designed gradients: a large sky that fades "
    "smoothly from dense white dither at the horizon to black at the "
    "top (or the reverse), soft glow ramps radiating from every light "
    "source, gradient pools of light on the ground, atmospheric depth "
    "where far things dissolve into sparse dither. Wide cinematic "
    "shot, low horizon, one dominant subject, light from the top-left, "
    "rich dithered texture in ground and sky. No text, no borders, no "
    "watermark. "
)

FLOOR = (
    "Setting: floor one of the tower — The Fencerows. Stolen meadowland "
    "rolls out under the tower's floodlights; hedgerows still stand in "
    "their old lines, fencing fields no farmer will cut again. "
)

STAGE = (
    "EMPTY STAGE — absolutely no creatures, no people, no animals, no "
    "figures of any kind. The scene is viewed from the side like a "
    "theater stage: flat, level open ground fills the lower quarter of "
    "the frame edge to edge — the fighting floor where combatants will "
    "later stand — with nothing tall growing or standing on it, a "
    "designed gradient pool of light falling across the open grass. "
    "All hedges, structures and scenery sit BEHIND that open ground; "
    "the ground line is strictly horizontal. "
)

# Floor 1 — The Fencerows. wind: sway amplitude in px; fire: flicker.
SCENES: dict[str, dict] = {
    "grey_wolf": dict(wind=1.5, fire=False, prompt=(
        "A clear readable landscape: one long dark hedgerow runs "
        "horizontally behind the fighting floor, with a single torn "
        "dark gap in the hedge left of center. Above and behind it, "
        "night meadowland and two tower floodlights on poles casting "
        "designed cone-shaped glow beams down across the grass. Crisp "
        "distinct shapes, strong tonal separation.")),
    "feral_boar": dict(wind=1.2, fire=False, prompt=(
        "A ruined field between old hedgerow lines: turf torn up in "
        "dark furrows behind the fighting floor, broken fence posts "
        "leaning, churned earth, tower floodlights raking low across "
        "the grass from one side.")),
    "hedge_rat": dict(wind=1.1, fire=False, prompt=(
        "A fencerow at night with an abandoned granary behind it: the "
        "granary door stands open spilling a pale glow gradient, grain "
        "sacks burst on the ground behind the fighting floor, leaves "
        "drifting off the hedge.")),
    "lane_wolf": dict(wind=1.7, fire=False, prompt=(
        "A green lane between two tall hedgerows converging toward the "
        "horizon behind the fighting floor, cold floodlight beams "
        "crossing the lane from above, hedge shadows long across the "
        "grass.")),
    "goblin_straggler": dict(wind=0.7, fire=True, prompt=(
        "A low wooden gate and stile in a hedgerow behind the fighting "
        "floor, tall grass, an abandoned tiny campfire still burning "
        "to one side with a designed glow ramp radiating from the "
        "flames, night sky above.")),
    "ember_shade": dict(wind=2.4, fire=True, prompt=(
        "A rotten stile in a snarled blackthorn hedge behind the "
        "fighting floor, faint ember glow seeping out of the hedge "
        "line itself where spilled aether soaked the wood — small "
        "glowing points along the blackthorn, flood-lit haze above.")),
    "warden": dict(wind=1.4, fire=False, prompt=(
        "The floor's stair-gate: a riveted iron gate and humming "
        "stair-lift machinery behind the fighting floor, stairs rising "
        "into darkness beyond, two floodlight cones from the gate "
        "towers pooling on the ground, hard machine edges against a "
        "dithered night sky.")),
}


def api_key() -> str:
    key = os.environ.get("LUNA_GEMINI_API_KEY", "").strip()
    if key:
        return key
    env = os.path.join(_ROOT, "luna", ".env")
    if os.path.exists(env):
        for line in open(env):
            line = line.strip()
            if line.startswith("LUNA_GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("LUNA_GEMINI_API_KEY not set (env or luna/.env)")


async def gen_still(sid: str, key: str) -> str:
    prompt = (STYLE + FLOOR + STAGE + SCENES[sid]["prompt"] +
              " Very wide cinematic side-on shot.")
    res = await providers.generate(
        providers.MODELS["nano-banana-pro"], prompt, aspect="21:9",
        api_key=key)
    if "error" in res:
        return f"FAIL {sid}: {res['error']} — {str(res.get('detail'))[:160]}"
    open(os.path.join(OUT, f"{sid}.jpg"), "wb").write(res["image_bytes"])
    return f"ok   {sid}"


def density_master(sid: str) -> np.ndarray:
    """Model render -> 320x112 greyscale density field in [0, 1]."""
    img = Image.open(os.path.join(OUT, f"{sid}.jpg")).convert("L")
    iw, ih = img.size
    target = W / H
    if iw / ih > target:
        nw = int(ih * target)
        img = img.crop(((iw - nw) // 2, 0, (iw + nw) // 2, ih))
    else:
        nh = int(iw / target)
        img = img.crop((0, (ih - nh) // 2, iw, (ih + nh) // 2))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=1)
    return np.asarray(img, dtype=np.float64) / 255.0


def glow_mask(grey: np.ndarray) -> np.ndarray:
    """Bright-region mask (floodlights, windows, fire) in [0, 1]."""
    blur = Image.fromarray((grey * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(6))
    g = np.asarray(blur, dtype=np.float64) / 255.0
    return np.clip((g - 0.55) / 0.35, 0.0, 1.0)


def noise_fields(n: int = 3) -> list[np.ndarray]:
    """Smooth zero-mean noise fields for fire flicker (fixed seed)."""
    rng = np.random.default_rng(49)
    out = []
    for _ in range(n):
        f = rng.random((H, W))
        f = np.asarray(Image.fromarray((f * 255).astype(np.uint8)).filter(
            ImageFilter.GaussianBlur(2)), dtype=np.float64) / 255.0
        out.append((f - f.mean()) * 4.0)
    return out


def wind_shift(grey: np.ndarray, t: int, amp: float) -> np.ndarray:
    """Horizontal displacement above the floor line, perfect loop in t."""
    floor_y = int(H * FLOOR_FRAC)
    ys = np.arange(H, dtype=np.float64)[:, None]
    xs = np.arange(W, dtype=np.float64)[None, :]
    height = np.clip((floor_y - ys) / floor_y, 0.0, 1.0)
    a = amp * height ** 1.4
    ph = 2 * np.pi * t / FRAMES
    off = a * np.sin(ph + ys * 0.042 + xs * 0.015)
    sx = xs + off
    x0 = np.floor(sx).astype(int) % W
    x1 = (x0 + 1) % W
    frac = sx - np.floor(sx)
    rows = np.arange(H)[:, None].repeat(W, axis=1)
    return grey[rows, x0] * (1 - frac) + grey[rows, x1] * frac


def build_gif(sid: str) -> str:
    cfg = SCENES[sid]
    grey = density_master(sid)
    mask = glow_mask(grey)
    noises = noise_fields()
    ty, tx = np.indices((H, W))
    thresh = (BAYER8[ty % 8, tx % 8] + 0.5) / 64
    frames = []
    for t in range(FRAMES):
        ph = 2 * np.pi * t / FRAMES
        f = wind_shift(grey, t, cfg["wind"])
        f = f * (1.0 + 0.08 * mask * np.sin(ph + 1.3))
        if cfg["fire"]:
            k = len(noises)
            w = np.array([max(0.0, np.cos(ph - 2 * np.pi * j / k)) ** 2
                          for j in range(k)])
            w /= w.sum()
            flick = sum(wj * nj for wj, nj in zip(w, noises))
            f = f + 0.10 * mask * flick
        bits = np.where(np.clip(f, 0, 1) > thresh, 255, 0).astype(np.uint8)
        frames.append(Image.fromarray(bits).convert("P"))
    frames[0].save(os.path.join(OUT, f"{sid}.gif"), save_all=True,
                   append_images=frames[1:], duration=FRAME_MS, loop=0,
                   optimize=True)
    still = np.where(grey > thresh, 255, 0).astype(np.uint8)
    Image.fromarray(still).convert("RGB").resize(
        (W * 4, H * 4), Image.NEAREST).save(
        os.path.join(OUT, f"{sid}_still.png"))
    return f"gif  {sid} ({FRAMES}f)"


async def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("stills", "gifs"):
        sys.exit(__doc__)
    mode, names = sys.argv[1], sys.argv[2:]
    os.makedirs(OUT, exist_ok=True)
    bad = [n for n in names if n not in SCENES]
    if bad:
        sys.exit(f"unknown ids: {bad} (have {list(SCENES)})")
    if mode == "stills":
        key = api_key()
        todo = names or [s for s in SCENES if not os.path.exists(
            os.path.join(OUT, f"{s}.jpg"))]
        print(f"{len(todo)} stills -> {OUT}")
        for i in range(0, len(todo), 4):
            for line in await asyncio.gather(
                    *(gen_still(n, key) for n in todo[i:i + 4])):
                print(line, flush=True)
    else:
        todo = names or [s for s in SCENES if os.path.exists(
            os.path.join(OUT, f"{s}.jpg"))]
        for n in todo:
            print(build_gif(n), flush=True)
    print("done")


if __name__ == "__main__":
    asyncio.run(main())
