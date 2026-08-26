# 082 phase-1e — chip ink + tag drop + shaded dither (roy, 2026-08-26)

## Goal

Three review fixes on the live phase-1d card:

1. **GATE tag lower** — the chip floats above the stump's top; anchor
   it down onto the structure's face.
2. **Chip text bright white** — marker chips read in TEXT grey
   (#adaba0); they switch to BRIGHT (#fbfbf7).
3. **More shading** — the dither is near-binary white/black; soften
   the tone curve (gamma toward 1.1–1.2, tuned by eye against the
   phase-1d asset) so midtones survive as halftone shading.
4. **The [number] gold** — the chip's `[N]` prefix reads in GOLD
   (#f5b825); flips to INK on hover like the rest of the chip.

Measurable: chip computed color rgb(251,251,247); GATE chip overlaps
the structure; the asset's mid-band (halftone) pixel share rises vs
phase-1d; dojo re-walk PASS.

## Steps

1. `engine/floormap.py`: gate anchor (56,40) → onto the face (~56,50);
   mock `index.html` matched.
2. `render.py`: `.mk` color `{TEXT}` → `{BRIGHT}`; the number wrapped
   `<span class="mknum">[N]</span>` in GOLD, INK on hover.
3. `mock-map/map_gen.py`: gamma 1.45 → the eye-picked value; regen
   `map_001_492x369.png`; copy to the plugin.
4. `version.py` → 0.110.0. Vendor sync.
5. Targeted 082 tests; dojo re-walk, results folder 0058.

## Verification

- `test_082_floormap.py` green.
- Dojo run 0058 PASS; screenshot shows the shaded map, white chip
  text, GATE tag on the structure.

## Rollback

Labs flag off is the live mitigation. Full revert: revert phase-1e
commits (asset included), vendor re-sync.
