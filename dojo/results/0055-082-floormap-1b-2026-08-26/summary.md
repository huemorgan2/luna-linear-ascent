# Dojo run 0055 — 082 phase-1b: floormap review fixes

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1b revision)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = the phase-1b tree (ran labeled 0.106.0; shipped as
  0.107.0 — 0.106.0 was taken by a parallel 084 commit; only the version
  string differs), monorepo `edf1549` (phase-1b changes uncommitted at
  run time; committed immediately after)
- **Player:** web:dojomap668116, seeded floor 1, warrior L3
- **Verdict:** **PASS — 32/32 checks**

## What phase-1b changed (all verified this run)

| Change | Check | Evidence |
|--------|-------|----------|
| Mapped card sheds floor art + headline + support + body; eyebrow bar rides under the map | S4 | `{banner:false, headline:false, support:false, order:true}` |
| Map full card width, no border | S4 | img 734px vs card 736px |
| 77% resolution | S4 | natural size 492×369 |
| Town chip renamed and moved to the tower's foot | S4 | `[5] ROOTHOLLOW` |
| Gate lobby row renamed | S7 | "Back to Roothollow" |
| Bug fix: Hobb card keeps plain rows, no map (was: map swallowed the rows, locking the player) | S6 | `{head:"Hobb Fennick — the last farmer", map:false, opts:[hunt,keep,talk,gate,town]}` |
| New art: massive built tower with massive door as the gate | screenshots | 03-map-on.png |

## Full check list

32/32 PASS: signup+seed, list-off, labs toggle both ways with DB flag,
map card (size, bleed, shed prose, chips, labels, cost inks, no dead
deep-hunt, chip-or-row-never-both), tooltip hover, Hobb rows + return,
gate lobby + back-row label + ride up, Roothollow round trip, hunt
(encounter, exactly 1 ⚡, flee out and back), Brackjaw keep (free entry,
leave, back at map), labs off restores the list, no console errors.

## Artifacts

`screenshots/01…10`, `checks.json`.
