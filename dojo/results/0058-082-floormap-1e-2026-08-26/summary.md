# Dojo run 0058 — 082 phase-1e: chip ink + tag drop + shaded dither

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1e revision)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = 0.110.0, monorepo `bd6c256` (phase-1e changes
  uncommitted at run time; committed immediately after)
- **Player:** web:dojomap211992, seeded floor 1, warrior L3
- **Verdict:** **PASS — 33/33 checks** (one new check vs 0057)

## What phase-1e changed (verified this run)

| Change | Check | Evidence |
|--------|-------|----------|
| Chip text bright white, [N] gold | S4 (new) | `{ink:"rgb(251, 251, 247)", num:"rgb(245, 184, 37)"}` |
| GATE tag dropped onto the structure's face (56,40 → 56,50) | screenshots | 03-map-on.png |
| Shaded dither — painted grey washes in the raw + gamma 1.45 → 1.15 keep midtone halftone instead of stark white/black | screenshots | 03-map-on.png |

First run of the night 31/32: the new `mknum` span broke the
walkthrough's label reader (it read only the chip's first node) —
harness fix, re-run 33/33.

## Artifacts

`screenshots/01…10`, `checks.json`.
