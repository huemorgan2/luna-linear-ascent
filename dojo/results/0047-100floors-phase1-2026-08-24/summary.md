# Dojo run 0047 — 100floors-attack3dscene phase 1 (floors 1–10)

- **Date:** 2026-08-24
- **Scenario:** `plans/100floors-attack3dscene/phase-1/dojo/01-arena-floors-1-10.md`
  (runner: `luna/dojo/tests/100floors-phase1/walkthrough.mjs`)
- **Environment:** local — worldd `uvicorn app.main:app` on :8600 serving
  `worldd/vendor` + `worldd/static`, ascent-postgres (docker, :5434),
  Playwright Chromium headless (swiftshader GL), node v22.20.0
- **Commits under test:** plugin `f4d7dca` (READY_FLOORS 1–10, labs arena
  feature removed), workspace `8de20cf` (vendor + pointer + arena3d.js),
  `5e263ec` (55 arena backdrops)
- **Verdict: PASS — 24/24 checks** (`screenshots/results.json`)

## Checks

| # | Check | Verdict | Evidence |
|---|-------|---------|----------|
| A | signup + seed floor 1 (fresh account, Labs never opened) | PASS | `dojoa299515`, level 8, rusted_sword |
| A1 | floor-1 town offers hunt | PASS | opts `hunt,keep,talk,gate,town` |
| A2 | floor-1 fight opener carries `data-arena`, no labs flag | PASS | `{"arena":true,"a3d":false}` — `01-f1-opener.png` |
| A3 | first strike mounts the 3D stage, 320×300 canvas | PASS | `[320,300]` — `02-f1-stage.png` |
| A3 | steady-state round settles < 12 s | PASS | round 1 7154 ms (stage mount + backdrop fetch), round 2 570 ms |
| A3 | HP bars both sides + combat log | PASS | `me:354/354`, `foe:14/14`, 2 log lines |
| A4 | backdrop behind the fighters, not a black void | PASS | `backgrounds300/lane_wolf.png` → 200; canvas PNG 10307 bytes (a black stage compresses to ~1 KB) |
| A5 | fight continues on the stage across rounds | PASS | `03-f1-mid-fight.png` |
| A6 | Labs card lists figure3d only — no arena row | PASS | `arenaRow:false, figRow:true` — `04-labs-card.png` |
| A7 | floor-8 fight opener carries `data-arena` | PASS | foe `ash_adder` |
| A8 | floor-8 stage up with its own backdrop | PASS | `ash_adder.png` → 200; canvas PNG 11632 bytes — `05-f8-stage.png` |
| A9 | DB: labs doc holds no arena key after all fights | PASS | `doc->'labs'` = `{}` |
| B | signup + seed floor 11 (beyond the rollout front) | PASS | `dojob579527` |
| B1 | floor-11 town offers hunt | PASS | opts include `hunt` |
| B2 | floor-11 fight is the classic 2D card | PASS | `{"arena":false,"a3d":false}`, opts `close_in,stand,run,shield_wall` — `06-f11-classic.png` |
| B3 | round resolves on the classic card | PASS | still no arena markers |
| B4 | DB: labs doc holds no arena key | PASS | `{}` |
| V | all backgrounds300 fetches returned 200 | PASS | `lane_wolf`, `ash_adder` |
| V | no console/page errors | PASS | 0 |
| V | no 4xx/5xx from /play/api | PASS | 0 |

## Harness notes (not regressions)

- First walkthrough attempt hung on full-page screenshots: the arena
  repaints continuously, so Playwright's default screenshot stability
  wait timed out. Fixed in the runner with `animations: 'disabled'`.
- A5/A6 originally raced a fast kill (10-HP foe → kill card swallowed
  the labs click). Runner now accepts a clean fight end and re-seeds to
  town before the Labs check.

## Regressions

None.
