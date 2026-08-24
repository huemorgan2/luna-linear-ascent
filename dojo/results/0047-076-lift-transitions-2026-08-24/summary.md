# Dojo run 0047 — 076 lift transitions

- **Date:** 2026-08-24
- **Environment:** local worldd on :8000 (uvicorn, test DB postgres :5434),
  Playwright headless Chromium, viewport 760x900
- **Commits:** plugin-linear-ascent 898015b (0.99.1, lift transitions),
  workspace ada047a + uncommitted 076 vendor/tests (committed immediately
  after this run)
- **Scenario:** luna/dojo/tests/lift-transitions/scenario.md
- **Runner:** luna/dojo/tests/lift-transitions/walkthrough.mjs
- **Verdict: PASS — 21/21 checks** (results.json)

| # | Check | Verdict | Evidence |
|---|-------|---------|----------|
| S1 | signup + boot load plays no overlay | PASS | no `#liftlay` 1.5s after card |
| S1 | intro walk reaches Roothollow | PASS | 01-roothollow.png |
| S2 | gate → floor 1: ascent overlay up, masked with `lift_ascent_320x112.gif?t=<nonce>` | PASS | 02-ride-up-mid.png |
| S2 | place dimly visible behind (rgba(0,0,0,0.8)) | PASS | 02-ride-up-mid.png |
| S2 | overlay gone ≤7s after click (measured ~5.0s total) | PASS | 03-floor1-arrival.png |
| S3 | first-visit reel: skip exit plays no second ride | PASS | 04-floor1-camp.png |
| S4 | return to Roothollow: descent overlay, masked with `lift_descent_320x112.gif?t=<nonce>` | PASS | 05-ride-down-mid.png |
| S4 | overlay fades, square behind, play not blocked | PASS | 06-back-on-the-square.png |
| S5 | page reload replays nothing | PASS | 07-reload-quiet.png |
| S6 | invalid floor pick refuses (toast payload, no `data-lift`, no overlay) | PASS | results.json |
| V1/V2 | act answers carried `data-lift="up"` and `"down"` | PASS | captured act JSON |
| V3 | both fxart GIFs serve 200 image/gif | PASS | results.json |
| V4 | browser console free of errors through both rides | PASS | zero entries |

## Notes
- S6 exercised `floor_15` on a fresh climber; the gate card does not list
  the row, so the refusal came from the paths guard ("That isn't one of
  the paths"), not the sealed-floor line. The sealed-floor refusal itself
  is covered by `tests/test_076_lift_transitions.py::
  test_sealed_refusal_carries_no_ride` (engine-level). Either way: no
  overlay, no ride — the anti-pattern under test.

## Regressions (pre-existing, filed — none from 076)
All four also fail on a clean checkout of plugin HEAD (verified in a
worktree at 0c734e7), and one worldd test fails with the working tree
stashed — none touch 076 surface:
- plugin `test_033_when_a_warden_falls.py::test_the_kill_clears_the_treeline_memory`
- plugin `test_048_no_classes.py::test_no_clazz_reads_outside_migrations`
  (clazz reads at scene.py:241, render.py:1149 — 074/075 in-flight work)
- plugin `test_kill3d.py::test_kill3d_card_ships_no_ending_gif` and
  `::test_kill3d_line_follows_the_class`
- worldd `test_web_play.py::test_leaderboard_marks_only_you`

## Production re-run (post-deploy, 2026-08-24)

Same walkthrough against `https://ascent-worldd.onrender.com` after deploy
dep-da681pojo6nc73c5dnvg went live (0.97.3 → 0.99.1): **21/21 PASS**.
Ascent overlay up 3.4s after the click with the ascent GIF mask, descent
ride down to the square, reload quiet, sealed-floor refusal rideless, both
GIFs 200 image/gif, console clean. Evidence in `production/`.
