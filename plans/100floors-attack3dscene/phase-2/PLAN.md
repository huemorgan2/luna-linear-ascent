# Phase 2 — floors 11–20: backdrops + gate to 1–20

## Goal

The arena runs for everyone on floors 1–20. 53 new arena backdrops cover
every floor-11–20 id (43 encounters + wardens 011–020; GLBs and kill
backgrounds already shipped with the kill finisher). Gate widened, suites
green, dojo PASS, deployed.

## Steps

1. `engine/arena.py`: `READY_FLOORS = frozenset(range(1, 21))` (plugin
   submodule, then `worldd/tools/vendor_game.sh` after the pre-rsync diff).
2. `tests/test_067_arena.py`: gate boundary tests move to 20/21
   (enabled on 11 and 20, disabled on 21).
3. `gen_bg_arena.py`: set the floor range to 11–20 (the phase-1 rework
   already derives ids from the YAMLs; `gf.SCENES` + `gf.FLOOR` cover
   floors 2–20 — no new prompt authoring needed this phase).
4. Canary one still, eyeball, then `stills` (53) + `sheets`.
5. Census: all floor-11–20 ids in `backgrounds300/`, each new PNG
   320×7200 mode-1. Eyeball contact prints.
6. Targeted then full test suites (plugin + worldd).
7. Secret scan; commits: plugin gate bump → workspace vendor + pointer →
   assets.
8. Dojo: rerun `phase-1/dojo/01-arena-floors-1-10.md` semantics shifted up:
   3D with backdrop on floors 11 and 20, classic 2D on floor 21. Results
   folder under `dojo/results/`.
9. Deploy (`worldd/tools/deploy.sh`), verify a floor-11 fight live.
10. Append Execution status here; commit.

## Verification

- Census script: 0 missing `backgrounds300` ids for floors 1–20.
- `arena.enabled` boundary: True at 20, False at 21 (unit test).
- Dojo results folder with PASS rows and screenshots for floors 11, 20, 21.
- Live floor-11 fight shows the backdrop post-deploy.

## Rollback

`git revert` the gate-bump commits (plugin + workspace) and redeploy —
floors 11–20 drop back to the classic card. New PNGs stay (inert).
