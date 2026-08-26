# 082 phase-1d — the tower is a stump; lines go up (roy, 2026-08-26)

## Goal

The phase-1c tower kept its full height — roy asked for the opposite
silhouette: **remove the whole top section**. The gate is a short,
blocky, massive structure — way shorter, wide, monolithic — and the
elevator **lines run straight up from it out of the top of the frame**
(the floor above is unseen; the lines say the tower goes on without
drawing it). Small door and winch wheels stay.

Measurable: on the card the structure tops out low (roughly the frame's
upper third at most), the cables visibly continue past it to the top
edge; dojo re-walk PASS. **Deploy requested** — push, trigger, poll to
live, post-deploy verification.

## Steps

1. Art: Gemini `--ref` pass on `mock-map/raw_map.png` — demolish the
   shaft: a blocky 2–3-storey massive base only; keep small door +
   winch wheels; bold taut cable lines rising from the winches straight
   up and off the top edge. `map_gen.py` (unchanged pipeline) → new
   `map_001_492x369.png`; re-place marker coords if the silhouette
   moves them (GATE chip drops to the stump); copy asset to the plugin.
2. `version.py` → 0.109.0. Vendor sync.
3. Tests: targeted 082 suite (no code change expected — art + coords
   only).
4. Dojo: re-walk, results folder 0057.
5. **Deploy**: commit chain, push, trigger deploy via API, poll to
   live 0.109.0, verify the live card serves the new art.

## Verification

- `test_082_floormap.py` green.
- Dojo run 0057 PASS; screenshot shows the short blocky gate with
  lines running off the top edge.
- Live version reports 0.109.0; live map art hash matches the new
  asset.

## Rollback

Labs flag off is the live mitigation. Full revert: revert phase-1d
commits (asset included), vendor re-sync, redeploy previous version.

## Execution status

Executed 2026-08-26. Shipped in plugin 0.109.0; vendor synced.

- **Art:** one Gemini pass on the phase-1c raw — shaft demolished to a
  blocky 2–3 storey plinth, flat top, small door + winch wheels kept,
  two bold cables straight off the top edge. Pipeline unchanged
  (phase-1c unsharp pass carried the detail). Raw kept as
  `raw_map_stump.png` (= new `raw_map.png`).
- **Coords:** only CAMP nudged 43,60 → 45,59 (onto the tents); the
  stump landed under the existing GATE/ROOTHOLLOW/KEEP anchors.
- **Tests:** `test_082_floormap.py` 11/11. No renderer/engine change —
  full suites not re-run (at baseline this same day, phase-1c).
- **Dojo:** run 0057 (`dojo/results/0057-082-floormap-1d-2026-08-26/`)
  **32/32 PASS**; card screenshot shows the stump with the lines off
  the top edge.
- **Deploy:** pushed (plugin, luna — rebased over two parallel remote
  commits, monorepo), `worldd/tools/deploy.sh` deploy
  dep-da7f7hmk1f9s73d7pgqg, 0.106.0 → **live 0.109.0** (/health).
- **Post-deploy verification (prod):** throwaway player dojoverify1d,
  labs floormap on — live card serves the new asset: natural 492×369,
  full bleed (img 734px / card 736px), all five chips, HUNT wears the
  pixel bolt (`.mkcost .eg` present, no ⚡ in text). Evidence:
  `dojo/results/0057-082-floormap-1d-2026-08-26/screenshots/11-prod-live-0109.png`.
