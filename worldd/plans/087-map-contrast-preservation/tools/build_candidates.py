#!/usr/bin/env python3
"""Build measured floor-2 reduction candidates without changing game art."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "worldd/plans/085-floor-maps-standard/art/sources/map_002_v1.png"
OLD = ROOT / "plugin-linear-ascent/plugin_linear_ascent/content/art/maps/map_002_492x369.png"
OUT = Path(__file__).resolve().parents[1] / "evidence"
W, H = 492, 369
INK = (217, 217, 211, 255)
BAYER = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21],
], dtype=float)
REGIONS = {
    "lower_left_water": (15, 245, 120, 305),
    "mid_left_water": (35, 88, 150, 135),
    "bright_quarry": (360, 175, 485, 300),
    "central_shadow": (270, 145, 365, 230),
}


def crop(source: Image.Image) -> Image.Image:
    box = source.point(lambda p: 255 if p > 40 else 0).getbbox()
    image = source.crop(box) if box else source
    width, height = image.size
    target = W / H
    if width / height > target:
        new_width = int(height * target)
        return image.crop(((width - new_width) // 2, 0,
                           (width + new_width) // 2, height))
    new_height = int(width / target)
    return image.crop((0, (height - new_height) // 2,
                       width, (height + new_height) // 2))


def encode(image: Image.Image, target: Path) -> None:
    values = np.asarray(image, dtype=float) / 255
    thresholds = np.tile((BAYER + 0.5) / 64,
                         ((H + 7) // 8, (W + 7) // 8))[:H, :W]
    mask = values > thresholds
    pixels = np.zeros((H, W, 4), dtype=np.uint8)
    pixels[:, :, 3] = 255
    pixels[mask] = INK
    Image.fromarray(pixels, "RGBA").save(target)


def local_values(image: Image.Image) -> np.ndarray:
    pixels = np.asarray(image.convert("L"), dtype=float)
    scale = 217 if len(image.getcolors(maxcolors=1000) or []) == 2 else 255
    pixels /= scale
    return np.array([
        pixels[y:y + 24, x:x + 24].mean()
        for y in range(0, H - 23, 24)
        for x in range(0, W - 23, 24)
    ])


def metrics(image: Image.Image, reference: Image.Image) -> dict:
    actual = local_values(image)
    expected = local_values(reference)
    pixels = np.asarray(image.convert("L"), dtype=float) / 217
    data = {
        "tone_range": round(float(np.ptp(actual)), 4),
        "tone_stddev": round(float(actual.std()), 4),
        "source_correlation": round(float(np.corrcoef(expected, actual)[0, 1]), 4),
        "ink_percent": round(float(pixels.mean() * 100), 2),
        "regions": {},
    }
    for name, (x0, y0, x1, y1) in REGIONS.items():
        data["regions"][name] = round(float(pixels[y0:y1, x0:x1].mean()), 4)
    return data


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source = crop(Image.open(SOURCE).convert("L"))
    reference = source.resize((W, H), Image.Resampling.BOX)
    candidates = {
        "box_direct": reference,
        "box_mild_unsharp": reference.filter(
            ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=3)),
        "lanczos_direct": source.resize((W, H), Image.Resampling.LANCZOS),
        "lanczos_mild_unsharp": source.resize((W, H), Image.Resampling.LANCZOS).filter(
            ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=3)),
    }
    results = {"source": str(SOURCE.relative_to(ROOT)), "candidates": {}}
    old_metrics = metrics(Image.open(OLD), reference)
    old_metrics["sha256"] = hashlib.sha256(OLD.read_bytes()).hexdigest()
    results["old"] = old_metrics
    for name, image in candidates.items():
        target = OUT / f"map_002_{name}_492x369.png"
        encode(image, target)
        result = metrics(Image.open(target), reference)
        result["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        results["candidates"][name] = result
    (OUT / "metrics.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
