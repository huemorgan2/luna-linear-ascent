# Dojo run 0054 — 082 phase-1: Labs floormap

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin 0.105.0, monorepo `8fdbb08`, plugin working tree on top of
  `e3b2648` (082 changes uncommitted at run time; committed immediately after)
- **Player:** web:dojomap178734, seeded floor 1, warrior L3
- **Verdict:** **PASS — 28/28 checks** (final run; two earlier runs surfaced
  the fixes below)

## Checks

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| S1 | signup + seed floor 1 | PASS | 200, seeded L3 warrior |
| S2 | labs off → plain list, no map | PASS | opts hunt/keep/talk/gate/town, no `.mapwrap` |
| S3 | Labs card lists Floor maps, toggle ON, DB flag true | PASS | "Floor maps — ON · floors 1"; `doc.labs.floormap = true` |
| S4 | map block on camp card | PASS | 640×480 img rendered at 640px |
| S4 | chips = exactly the five camp options | PASS | hunt, keep, talk, gate, town; no DEEP-HUNT |
| S4 | chip labels + numbering | PASS | [1] HUNT · [2] BRACKJAW · [3] CAMP · [4] GATE · [5] TOWN |
| S4 | hunt chip wears `1 ⚡` in energy teal | PASS | rgb(69, 208, 192) |
| S4 | BRACKJAW chip carries no cost | PASS | cost span absent |
| S4 | mapped options are not rows too | PASS | one `data-opt` each |
| S5 | tooltip paints on hover | PASS | "The near fields — hunt for coin and XP." |
| S6 | CAMP chip → Hobb Fennick | PASS | "Hobb Fennick — the last farmer" |
| S7 | GATE chip → Tower Gate lobby → floor 1 → map again | PASS | headline + `.mapwrap` back |
| S8 | TOWN chip → Roothollow → gate up → map again | PASS | same |
| S9 | HUNT chip opens an encounter, exactly 1 ⚡ spent | PASS | 24 → 23; opts close_in/stand/run/shield_wall/pack |
| S9 | flee → gate town (by design) → ride up → map | PASS | back at Lamplit Steading map |
| S10 | BRACKJAW chip opens the keep, walking in free | PASS | "Warden Brackjaw — ATK 15 / DEF 3 / HP 426/426"; 23 → 23 |
| S10 | leave keep → back at the camp map | PASS | via town → gate → floor 1 |
| S11 | toggle off → DB flag false, plain list restored | PASS | `doc.labs.floormap = false`; no map, rows back |
| S12 | no console errors | PASS | empty |

## Regressions found and fixed during the run (before this PASS)

1. **Chip clicks were inert** — `wireOptions()` (pane.py) and the render.py
   bridge bind clicks by a CSS selector list that lacked `button.mk`. Added
   to both. This was the real product bug of the run.
2. Walkthrough-only fixes (not product): `/— ON/` toggle regex, `skipMovie()`
   for the first-ride floor intro, energy read from `.mv[data-m="en"]`,
   flee-lands-in-gate-town is by design (`combat.py` sets
   `location = "gate_town"`) — walkthrough now rides the pylon back up.

## Artifacts

`screenshots/01-list-off.png` … `10-list-restored.png`, `checks.json`.
