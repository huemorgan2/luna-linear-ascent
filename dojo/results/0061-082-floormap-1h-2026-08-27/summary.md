# Dojo run 0061 — 082 phase-1h: the number keys reach the map chips

- **Date:** 2026-08-27
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1h revision — two new checks)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = 0.110.3 (phase-1h changes uncommitted at run time;
  committed immediately after)
- **Verdict:** **PASS — 35/35 checks** (33 prior + 2 new)

## What phase-1h changed (verified this run)

The 041 number-row handler (`pane.py`) clicked `button.opt` rows by
DOM index; the map card's mapped options are chips (`button.mk`), so
the `[N]` the chips wear was decoration. The handler now matches the
DISPLAYED number across `button.opt, button.mk` (`.key` / `.mknum`
spans — both already numbered by scene.options position), with the
old DOM-order pick kept for buttons that print no number.

New checks:

| Check | Evidence |
|-------|----------|
| S5 number key 4 presses the GATE chip | keydown "4" → Tower Gate lobby |
| S5 back at the map after the keystroke ride | map card restored |

## Artifacts

`screenshots/01…10`, `checks.json`.
