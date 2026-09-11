"""087: floor 2 preserves the approved source's regional tone."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "worldd/plans/085-floor-maps-standard/art/sources/map_002_v1.png"
PLUGIN_MAP = (
    ROOT
    / "plugin-linear-ascent/plugin_linear_ascent/content/art/maps/map_002_492x369.png"
)
VENDORED_MAP = (
    ROOT / "worldd/vendor/plugin_linear_ascent/content/art/maps/map_002_492x369.png"
)
EXPECTED_SHA256 = "d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e"
W, H = 492, 369


def _crop_to_map(image: Image.Image) -> Image.Image:
    box = image.point(lambda pixel: 255 if pixel > 40 else 0).getbbox()
    image = image.crop(box) if box else image
    width, height = image.size
    target_ratio = W / H
    if width / height > target_ratio:
        new_width = int(height * target_ratio)
        return image.crop(
            ((width - new_width) // 2, 0, (width + new_width) // 2, height)
        )
    new_height = int(width / target_ratio)
    return image.crop(
        (0, (height - new_height) // 2, width, (height + new_height) // 2)
    )


def _territory_values(image: Image.Image, scale: float) -> np.ndarray:
    pixels = np.asarray(image.convert("L"), dtype=float) / scale
    return np.array(
        [
            pixels[y : y + 24, x : x + 24].mean()
            for y in range(0, H - 23, 24)
            for x in range(0, W - 23, 24)
        ]
    )


def test_floor_2_asset_preserves_approved_source_tones():
    source = _crop_to_map(Image.open(SOURCE).convert("L")).resize(
        (W, H), Image.Resampling.BOX
    )
    packaged = Image.open(PLUGIN_MAP).convert("RGBA")

    assert packaged.size == (W, H)
    assert packaged.getextrema()[3] == (255, 255)
    pixels = np.asarray(packaged).reshape(-1, 4)
    colors = {tuple(color) for color in np.unique(pixels, axis=0)}
    assert colors == {(0, 0, 0, 255), (217, 217, 211, 255)}
    assert hashlib.sha256(PLUGIN_MAP.read_bytes()).hexdigest() == EXPECTED_SHA256
    assert PLUGIN_MAP.read_bytes() == VENDORED_MAP.read_bytes()

    expected = _territory_values(source, 255)
    actual = _territory_values(packaged, 217)
    assert np.ptp(actual) >= 0.470
    assert actual.std() >= 0.095
    assert np.corrcoef(expected, actual)[0, 1] >= 0.970
