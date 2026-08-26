# 082 phase-1g — tone the burn down (roy, 2026-08-26)

## Goal

Phase-1f brought the mountain tones back, but the image overall reads
burned white: 8.0% of the asset's 8x8 blocks are near-solid ink
(>90%), mostly blank-paper ground. Roy: "the mountains are better but
the image is burned white.. please fix it tone it down."

Measurable: near-solid-white block share drops to ~0 and whole-image
ink share drops noticeably (59.9% → ~50%), while the mountain band
keeps its phase-1f tonal spread (shadow blocks ≥ 11.6%, visible lit
ridge faces). Dojo re-walk PASS.

## Approach

Gamma cannot fix this: the designed-dither raw's midtones are already
committed, so a 1.3–1.9 sweep only moved ink 59.9% → 54.5% (burned
8.0% → 5.6%). The burn lives in large pure-white paper areas. The
right knob is a HIGHLIGHT CEILING on the tone ramp: scale the ramp so
pure paper lands at ~85% dither density instead of 100% — every light
surface carries halftone texture, nothing saturates to solid ink.

Ceiling sweep (with gamma 1.15 kept): 0.85 → ink 50.8%, burned 0.0%,
mountain shadow 14.4% / lit 9.0% (ridge faces still pop). 0.78 and
0.70 kill the mountains' lit faces (1.7% / 0.0% — flat). Pick 0.85.

## Steps

1. `mock-map/map_gen.py`: tone ramp `(p/255)**1.15` →
   `((p/255)**1.15) * 0.85`; regen `map_001_492x369.png`; copy to the
   plugin. No art pass — raw unchanged.
2. `version.py` → 0.110.2. Vendor sync.
3. Targeted 082 tests; dojo re-walk, results folder 0060.

## Verification

- Asset metrics: burned blocks ~0%, whole-image ink ~50%, mountain
  shadow blocks ≥ 11.6%.
- `test_082_floormap.py` green; dojo run 0060 PASS with screenshot.

## Rollback

Labs flag off is the live mitigation. Full revert: revert phase-1g
commits (asset included), vendor re-sync.
