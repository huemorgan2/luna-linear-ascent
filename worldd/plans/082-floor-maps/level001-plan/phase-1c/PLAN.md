# 082 phase-1c — tower scale + pixel bolt (roy, 2026-08-26)

## Goal

Two review fixes on the phase-1b card:

1. **The door sells the scale.** The gate tower's door shrinks to the
   size of the tower's first floor — a small door against the massive
   build is what shows how massive it is. Add turn wheels (winch
   mechanism) at the base and a line (cable) running up the tower.
2. **No emoji on the chip.** The HUNT chip's energy cost renders a raw
   ⚡ emoji; everywhere else the game paints the pixelated bluish bolt
   glyph. The chip cost must go through the glyph substitution.

Measurable: chip cost HTML contains `class="eg"` mask span and no
literal ⚡; new art passes the dojo visual check.

## Steps

1. Art: Gemini `--ref` pass on `mock-map/raw_map.png` — same tower,
   door reduced to first-floor scale, winch turn wheels at the base,
   taut cable line rising up the shaft. `map_gen.py` → new
   `map_001_492x369.png`; re-check marker coords (mock `index.html`
   then `engine/floormap.py` if the door foot moved); copy asset to
   `plugin_linear_ascent/content/art/maps/`.
2. `render.py` `_map_html`: cost span text `_e(...)` → `_et(...)` so
   ⚡ becomes `_eglyph('bolt')` in the chip's ink (AETHER; INK on
   hover via currentColor). CSS: `.mk .eg` sized to the chip
   (12px, vertical-align tuned).
3. `version.py` → 0.108.0. Vendor sync (`worldd/tools/vendor_game.sh`).
4. Tests: extend `test_082_floormap.py` — cost chip has no literal ⚡,
   has an `.eg` span.
5. Dojo: re-walk 082 walkthrough (S4 chip-cost check updated to accept
   the glyph), results folder 0056.

## Verification

- `test_082_floormap.py` green; plugin suite at baseline.
- Dojo run 0056 PASS; screenshot shows small door + wheels + line and
  the pixel bolt on the HUNT chip.

## Rollback

Labs flag off is the live mitigation. Full revert: revert the phase-1c
plugin + monorepo commits (asset included), vendor re-sync.

## Execution status

Executed 2026-08-26. Shipped in plugin 0.108.0; vendor synced.

- **Art:** two Gemini passes (door shrink + wheels + cable, then the
  relight for 1-bit). The decisive fix was in the PIPELINE, not the
  paint: `map_gen.py` gained an UnsharpMask(1.2, 180%, 2) after the
  LANCZOS downscale — the engraving's thin lines blurred to mid-grey
  and dithered to speckle; the unsharp pass re-crisps the wheel
  spokes, the small door arch and the cable. Raws kept:
  `raw_map_smalldoor.png` (pass 1), `raw_map.png` (= relit final),
  `raw_map_1b.png` (phase-1b backup).
- **Coords re-placed** (engine + mock): gate 54,40→56,40; town
  58,64→63,69 (the village hugging the tower's foot); talk
  44,63→43,60; keep 90,31→91,26. hunt/hunt_deep unchanged.
- **Bolt:** `_map_html` cost `_e`→`_et` (⚡ → `_eglyph('bolt')` in
  currentColor); CSS `.mk .eg` 12px. Chip textContent is now "1 " —
  dojo scene() reads `.mkcost .eg` presence instead.
- **Tests:** `test_082_floormap.py` 11/11 (new:
  test_chip_cost_wears_pixel_bolt_not_emoji). Plugin suite 1411
  passed / 7 failed — the known flaky pool (kill3d ×3, 017 ×2, 022,
  048); none touch the map paths. worldd suite not re-run (no
  worldd/app change beyond vendor).
- **Dojo:** run 0056 (`dojo/results/0056-082-floormap-1c-2026-08-26/`)
  **32/32 PASS** — pixel bolt in energy teal on the HUNT chip, no
  emoji, wheels/door/cable legible on the card screenshot.
- Deploy not requested.
