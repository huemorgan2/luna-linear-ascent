# 082 phase-1b — review fixes (roy, 2026-08-26)

## Goal

Fix the five issues roy raised on the shipped phase-1 map (0.105.0):

1. **The mapped card IS the map.** Remove the floor art (banner) and the
   prose (headline, support, body lines) when the map renders; keep the
   grey eyebrow bar, riding directly under the map.
2. **Full width.** The map bleeds to the card edges — no border, no
   640px cap, no side padding.
3. **The town is at the tower's foot, not on the floor.** Roothollow is
   the base town at the elevator bottom — the chip moves to the base of
   the gate tower and says **ROOTHOLLOW**, not TOWN. The gate lobby's
   "Back to the square" row becomes "Back to Roothollow".
4. **Bug: the NPC card must not show the map.** Talk is a choice ON the
   map; the Hobb card re-rendered the map and swallowed its own rows
   (they are the same `_gate_town_options`, so all got mapped away).
   The map renders on `_floor_arrival_scene` ONLY — the `_npc_scene`
   and `_gate_town_scene` seams come out.
5. **The gate is a massive built tower with a massive door.** New
   Gemini art pass; marker coordinates re-placed on the new land.

Measurable: dojo re-walk PASS; on the camp card no `banner`/`headline`
in the fragment while the map is on; `talk` scene ships `map = None`.

## Steps

1. `engine/core.py` — delete the `s.map = floormap.payload(...)` lines
   in `_npc_scene` and `_gate_town_scene`; `_gate_scene`'s back row →
   "Back to Roothollow".
2. `engine/floormap.py` — `town` marker: label `ROOTHOLLOW`, position
   at the base of the gate tower, tip says "Down the tower…".
3. `render.py` — hoist the map computation above the banner branch;
   when the map renders suppress banner + headline + support +
   body_lines and emit the map first (eyebrow under it). CSS: `.mapwrap`
   `margin:-12px -2ch 0; border:0; max-width:none`.
4. New map art: territory scale as before, plus a massive built stone
   tower (the inter-floor elevator) with a massive door at its base.
   `gen.py` → `map_gen.py` → mock + plugin asset. Resolution reduced to
   **77%** (roy): 492×369 instead of 640×480 — the asset becomes
   `content/art/maps/map_001_492x369.png` (renderer seam updated); the
   img still stretches to full card width, pixelated.
   Re-place all marker coords on the new art (mock + `floormap.py`).
5. `version.py` → 0.106.0. Vendor sync.
6. Tests: update `test_082_floormap.py` (ROOTHOLLOW label, npc scene
   has no map, fragment sheds banner/headline when mapped).
7. Dojo: update walkthrough (labels, S6 = Hobb card has ROWS and no
   map), full re-walk, results folder 0055.

## Verification

- `test_082_floormap.py` green; plugin + worldd suites at baseline.
- Dojo run 0055 all checks PASS, screenshots showing the full-bleed
  map, ROOTHOLLOW at the tower's foot, Hobb card with plain rows.

## Rollback

Toggle off (labs flag) is the live mitigation. Full revert: revert the
phase-1b commits in plugin + monorepo (art asset included), vendor
re-sync. No player-doc migration.

## Execution status

Executed 2026-08-26. Shipped in plugin 0.107.0 (0.106.0 was taken by a parallel 084 commit); vendor synced.

- **Correction to step 1:** `_gate_town_scene` is the camp's
  steady-state card (loc `gate_town`), not the base town — its seam
  STAYS. Only the `_npc_scene` seam came out (that was the lock bug).
- **Art:** two Gemini passes on the existing raw (tower swap, then a
  relight so the tower survives 1-bit: near-white lit face, dark
  shadow side, black door arch). `map_gen.py` now trims the painted
  frame, gamma 1.45, 492×369 (77%). Asset renamed
  `map_001_492x369.png`; markers re-placed (gate 54,40; town→ROOTHOLLOW
  58,64 at the door; talk 44,63; keep 90,31; hunt 72,84; deep 18,20).
- **Tests:** `test_082_floormap.py` 10/10 (two new: npc-no-map,
  shed-art-and-prose). Plugin suite 1410 passed / 7 failed — all in the
  known pre-existing flaky set (kill3d ×3, 017 ×2, 022, 048); none touch
  the map paths. worldd suite not re-run (no worldd/app change beyond
  vendor; 221/0 in phase-1 same day).
- **Dojo:** run 0055 (`dojo/results/0055-082-floormap-1b-2026-08-26/`)
  **32/32 PASS** — full-bleed 492×369 map (img 734px on a 736px card),
  no banner/headline/support/body, eyebrow under the map, ROOTHOLLOW
  chip at the tower's foot, "Back to Roothollow" in the lobby, Hobb card
  with plain rows and no map, hunt exactly 1 ⚡, keep free, no console
  errors.
- Deploy not requested.
