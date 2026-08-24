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

## Execution status (2026-08-24) — COMPLETE

- Gate: `READY_FLOORS = frozenset(range(1, 21))` — plugin `a897b61`,
  vendored surgically (file copy, no rsync — parallel session WIP in tree)
  in workspace `91d370c` with the submodule pointer.
- Backdrops: 53 new sheets (43 encounters + wardens 011–020), 2 transient
  Gemini failures retried ok. Census: 122/122 ids floors 1–20, missing 0,
  bad 0, all 320×7200 1-bit, 3188 KB total. Workspace `6af67e1`
  (159 files incl. stills/masters).
- Tests: targeted 34 passed; plugin suite 1362 passed / 4 pre-existing
  failures (test_048_no_classes + 3× test_kill3d, present before phase 2);
  worldd suite 206 passed / 7 failed + 1 error — bisected by restoring the
  phase-1 gate: identical failures, caused by the parallel session's
  uncommitted 074–079 WIP plus the known local leaderboard top-200
  artifact. Not phase-2 regressions.
- Dojo: walkthrough parameterized (luna `5e2aa7b`), run 0048 with
  FLOOR_LOW=11 FLOOR_HIGH=20 FLOOR_OFF=21 — **24/24 PASS** (arena +
  backdrop on floors 11 and 20, classic card on 21, labs doc clean,
  steady-state round 2547 ms). Results committed `4abdc6b`.
- Deploy: dep-da6amhvqj5pc73f4hmag live 2026-08-24 20:43 UTC, `/health`
  0.101.0 (origin/main also carried the parallel session's released
  0.101.0 + 079 commits). Production walkthrough **6/6 PASS** (floor-1
  arena, grey_wolf, canvas 11581 B). Floor-11 live: deployed assets
  verified directly — warden_011.png 200/29857 B, kobold_scavenger.png
  200/27136 B, warden_020.png 200/30965 B; floor-11 fight itself proven
  in local dojo (same code paths; prod accounts start at floor 1, prod DB
  not seedable — phase-1 precedent).
- Rollback unchanged: revert `a897b61` + `91d370c`, redeploy.
