# Dojo run 0056 — 082 phase-1c: tower scale + pixel bolt

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1c revision)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = 0.108.0, monorepo `1861a96` (phase-1c changes
  uncommitted at run time; committed immediately after)
- **Player:** web:dojomap302045, seeded floor 1, warrior L3
- **Verdict:** **PASS — 32/32 checks**

## What phase-1c changed (all verified this run)

| Change | Check | Evidence |
|--------|-------|----------|
| Small first-floor-scale door, winch turn-wheels at the base, cable line up the shaft | screenshots | 03-map-on.png |
| Chip cost paints the pixel bolt glyph, not the ⚡ emoji | S4 | `{cost:"1", bolt:true, emoji:false, color:"rgb(69, 208, 192)"}` |
| Marker coords re-placed on the new art (GATE 56,40; ROOTHOLLOW 63,69 on the foot village; CAMP 43,60; BRACKJAW 91,26) | S4 | chip labels + screenshot |

## Full check list

32/32 PASS: signup+seed, list-off, labs toggle both ways with DB flag,
map card (size, bleed, shed prose, chips, labels, pixel-bolt cost, no
dead deep-hunt, chip-or-row-never-both), tooltip hover, Hobb rows +
return, gate lobby + back-row label + ride up, Roothollow round trip,
hunt (encounter, exactly 1 ⚡, flee out and back), Brackjaw keep (free
entry, leave, back at map), labs off restores the list, no console
errors.

## Artifacts

`screenshots/01…10`, `checks.json`.
