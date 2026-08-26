# Dojo run 0057 — 082 phase-1d: the gate is a stump, lines go up

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1c revision — unchanged)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = 0.109.0, monorepo `67c9d39` (phase-1d changes
  uncommitted at run time; committed immediately after)
- **Player:** web:dojomap457136, seeded floor 1, warrior L3
- **Verdict:** **PASS — 32/32 checks**

## What phase-1d changed (verified this run)

| Change | Check | Evidence |
|--------|-------|----------|
| Whole top section removed — the gate is a short, blocky, massive 2–3 storey structure | screenshots | 03-map-on.png |
| Two bold cable lines rise from it straight off the top edge | screenshots | 03-map-on.png |
| Small door + winch wheels kept; CAMP chip nudged onto the tents (45,59) | S4 + screenshots | chip labels |

Art + coords only — no renderer/engine change; the 32 checks are the
phase-1c set re-run green on the new asset.

## Artifacts

`screenshots/01…10`, `checks.json`.
