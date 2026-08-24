# Phase 6 — floors 51–60: full asset generation + gate to 1–60

## Goal

The arena (and the kill finisher) runs with full 3D assets on floors
51–60: 50 foe ids (40 encounters + wardens 051–060) each get a
monster GLB, a 320×112 kill background, and a 320×300 arena backdrop.
Gate widened to floors 1–60; suites green; dojo PASS; deployed.

## Steps

1. **Author prompts** (the human-scale work, from the floor YAMLs'
   arrival/lore/prose — same recipe as floors 2–20):
   - `research/3d-fight/gen_bg_floors.py`: 10 new `FLOOR` settings
     (floors 51–60) + 50 `SCENES` entries (wind/fire params per scene,
     wardens get the `GATE` prefix).
   - `research/3d-fight/3d models/gen_floors.py`: 50 creature prompts
     with body plans (quadruped/biped/hexapod/…/none) following the breed
     style bible (native/pressed/wrongmade, PLAN3).
2. **Monster GLBs** (Tripo, resumable): run a 5-creature batch first,
   record credits spent, project the phase total and report it before the
   fleet; then `gen_floors.py -j 4` for the rest. Failures retried; body
   plan "none" ships unrigged (`10_textured.glb`).
3. Ship: `ship_floors.sh` (copies + `optimize_glb.sh`), extending its
   "plan none" list for any new unrigged ids.
4. **Kill backgrounds**: canary one still, then `gen_bg_floors.py stills`
   (50) + `gifs`, then `make_bg_sheets.py` bakes into
   `worldd/static/site/fight3d/backgrounds/`.
5. **Arena backdrops**: `gen_bg_arena.py` floor range 51–60; canary,
   `stills` (50) + `sheets` into `backgrounds300/`.
6. Gate: `READY_FLOORS = frozenset(range(1, 61))` in `engine/arena.py` (plugin submodule); boundary tests:
   enabled on 51 and 60, disabled on 61. Pre-rsync diff, then `worldd/tools/vendor_game.sh`.
7. Census (see Verification), eyeball GLB gallery
   (`research/3d-fight/3d models/index.html`) and backdrop contact prints.
8. Targeted then full suites (plugin + worldd). Secret scan; commits:
   plugin gate → workspace vendor + pointer → assets (GLBs and sheets may
   split into two commits for reviewability).
9. Dojo: arena with backdrop + 3D monster on floors 51 and 60;
   classic 2D card on floor 61. Results under `dojo/results/`.
10. Deploy (`worldd/tools/deploy.sh`), verify a floor-51 fight live.
    Append Execution status here; commit.

## Verification

- Census: 0 ids missing for floors 51–60 across `monsters/`,
  `backgrounds/` (320×2688 sheets), `backgrounds300/` (320×7200, mode 1).
- Every shipped GLB loads in the gallery viewer without error and reads
  as its card (silhouette sanity vs the encounter banner).
- Gate boundary unit test: enabled on 51 and 60, disabled on 61.
- Dojo results folder with PASS rows + screenshots; no 404s on
  `monsters/<id>.glb` or the two background dirs during the fights.
- Live fight on floor 51 post-deploy shows monster + backdrop in 3D.

## Rollback

`git revert` the gate commits (plugin + workspace) and redeploy — floors
51–60 fall back to the classic card. Shipped assets stay (inert
until the gate returns). Tripo/Gemini spend is not recoverable — hence the
canary + 5-batch cost checkpoint before every fleet run.
