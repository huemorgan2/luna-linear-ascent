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
