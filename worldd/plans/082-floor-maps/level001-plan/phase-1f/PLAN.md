# 082 phase-1f — bring the mountain tones back (roy, 2026-08-26)

## Goal

The phase-1e wash pass asked for "lighter far mountains" — on the card
the mountains went white and toneless. Roy wants them as they were
before phase-1e: lots of shades — dense hatching, deep shadows, full
tonal range — while keeping phase-1e's ground washes, chip inks and
tag positions.

Measurable: the mountain region's dark-pixel share on the 1-bit asset
returns to (or exceeds) the phase-1d level; dojo re-walk PASS.

## Approach (per `plugin-linear-ascent/vision/1bit-images.md`)

The doc's headline lesson: **don't extract 1-bit from a greyscale
render — have the model DESIGN the dither as art, then only enforce
the grid.** Phase-1e's grey-wash pass was the documented anti-pattern
("beware washed-out renders … can silently kill the gradients").
So the fix is a designed-dither re-render, not another wash.

## Steps

1. Art: Gemini pass with TWO refs — the current shaded raw
   (composition) and the phase-1d raw (`raw_map_stump.png`, mountain
   tone reference). Prompt per the doc: strictly two colors, every
   midtone as designed ordered-dither gradients, "use the FULL
   greyscale range, deep and moody, not pale", dense hatching and
   deep cast shadows on the mountains, large chunky dither pixels.
2. `map_gen.py`: since the raw is designed dither (not washes), the
   gamma likely returns toward neutral (1.0–1.15, tuned by eye) —
   post-process is enforcement only. Regen, compare the mountain band
   by eye and by dark-pixel share; copy asset to the plugin.
3. `version.py` → 0.110.1. Vendor sync.
4. Targeted 082 tests; dojo re-walk, results folder 0059.

## Verification

- Mountain band (upper-right quadrant) dark-pixel share ≥ phase-1d's.
- `test_082_floormap.py` green; dojo run 0059 PASS with screenshot.

## Rollback

Labs flag off is the live mitigation. Full revert: revert phase-1f
commits (asset included), vendor re-sync.

## Execution status

Executed 2026-08-26. Shipped in plugin 0.110.1; vendor synced.

- **Art:** one Gemini designed-dither pass (refs: 1e raw for
  composition, `raw_map_stump.png` for mountain tone) — composition
  held, mountains back to dense hatching with solid-black cast
  shadows. Gamma sweep 1.0/1.15/1.3: 1.15 kept (mountain-band block
  spread matches phase-1d exactly: shadow 11.6%=11.6%, lit 27.6% vs
  26.6%; phase-1e was 7.3%/15.1%).
- **Markers:** all six anchors verified on the new art (red-dot
  overlay + zooms); no coordinate changes.
- **Tests:** `test_082_floormap.py` 11/11.
- **Dojo:** run 0059 (`dojo/results/0059-082-floormap-1f-2026-08-26/`)
  **33/33 PASS**.
- Deploy not requested this phase (live remains 0.109.0).
