# Dojo run 0048 — 100floors-attack3dscene phase 2 (floors 11–20)

- **Date:** 2026-08-24
- **Environment:** local — worldd uvicorn :8600 (auto-reload, game 0.102.0 serving worldd/vendor), ascent-postgres docker :5434
- **Commits under test:** plugin `a897b61` (gate → floors 1–20), workspace `91d370c` (vendor gate + pointer) + `6af67e1` (53 backdrops), luna `5e2aa7b` (walkthrough parameterized)
- **Scenario:** `luna/dojo/tests/100floors-phase1/walkthrough.mjs` with `FLOOR_LOW=11 FLOOR_HIGH=20 FLOOR_OFF=21`
- **Verdict: 24/24 PASS**

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | A signup | PASS | dojoa604857 |
| 2 | A seed floor 11 | PASS | floor=11 warrior level=8 hp=400 |
| 3 | A1 floor-11 town offers hunt | PASS | hunt,hunt_deep,keep,gate,town |
| 4 | A2 opener carries data-arena, no labs flag | PASS | {"arena":true,"a3d":false} |
| 5 | A3 first strike mounts 3D stage | PASS | canvas 320×300 |
| 6 | A3 HP bars both sides + log lines | PASS | me:326/354, foe:400/400, 2 lines |
| 7 | A4 backdrop behind fighters, not black void | PASS | kobold_scavenger, HTTP 200, canvas PNG 12278 bytes |
| 8 | A3 steady-state round < 12 s | PASS | round1 3147 ms, round2 2547 ms |
| 9 | A5 fight continues or ends cleanly | PASS | a3d stage live |
| 10 | A re-seed floor 11 | PASS | clean town |
| 11 | A6 Labs lists figure3d only, no arena row | PASS | arenaRow:false, figRow:true |
| 12 | A seed floor 20 | PASS | floor=20 |
| 13 | A7 floor-20 opener carries data-arena | PASS | foe honor_guard |
| 14 | A8 floor-20 stage up with backdrop | PASS | honor_guard, HTTP 200, canvas PNG 11611 bytes |
| 15 | A9 DB: no arena key in labs doc | PASS | {} |
| 16 | B signup | PASS | dojob913696 |
| 17 | B seed floor 21 | PASS | floor=21 |
| 18 | B1 floor-21 town offers hunt | PASS | hunt,hunt_deep,keep,gate,town |
| 19 | B2 floor-21 fight is classic card | PASS | arena:false, a3d:false, 4 classic opts |
| 20 | B3 round resolves on classic card | PASS | still no arena |
| 21 | B4 DB: no arena key | PASS | {} |
| 22 | V backgrounds300 fetches all 200 | PASS | kobold_scavenger 200, honor_guard 200 |
| 23 | V no console/page errors | PASS | — |
| 24 | V no 4xx/5xx from /play/api | PASS | — |

Screenshots in `screenshots/` (01 f11 opener, 02 f11 stage, 03 f11 mid-fight, 04 labs card, 05 f20 stage, 06 f21 classic); raw verdicts in `screenshots/results.json`.

## Production verification (post-deploy, 0.101.0)

Deploy dep-da6amhvqj5pc73f4hmag reached live at 2026-08-24 20:43 UTC; `/health` game 0.101.0. `production.mjs` against https://ascent-worldd.onrender.com — **6/6 PASS**: fresh signup, intro walks to town in 15 steps, floor-1 opener carries data-arena (foe grey_wolf), 3D stage mounts 320×300, backdrop HTTP 200 with canvas PNG 11581 bytes, no console errors. Screenshots in `production/`.

Floor-11 live evidence: production accounts start at floor 1 and the production DB is not reachable for seeding, so (as in phase 1) the floor-11-specific fight was proven in the local dojo (24/24 above, same code paths) and the live check verifies the deployed floor-11–20 assets directly — `backgrounds300/warden_011.png` 200 (29857 B), `kobold_scavenger.png` 200 (27136 B), `warden_020.png` 200 (30965 B), byte-identical sizes to the built sheets.

## Regressions

None.

## Notes

- Backdrop census before the run: 122 ids (floors 1–20), missing 0, bad 0, all 320×7200 1-bit, 3188 KB total.
- worldd suite carries 7 failures + 1 error from the parallel session's uncommitted 074–079 WIP plus the known leaderboard top-200 local artifact — reproduced identically with the phase-1 gate restored, so not phase-2 regressions (bisect documented in the phase-2 plan).
- 02-f11-stage.png shows the full stage: rustwater-adit backdrop, both fighters, HP bars, banner "FLOOR 11 · IRONVALE · THE RUSTWATER ADIT".
