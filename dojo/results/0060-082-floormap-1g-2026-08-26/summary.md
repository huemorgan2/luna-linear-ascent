# Dojo run 0060 — 082 phase-1g: the burn toned down

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1e revision — unchanged)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = 0.110.2 (phase-1g changes uncommitted at run time;
  committed immediately after)
- **Verdict:** **PASS — 33/33 checks**

## What phase-1g changed (verified this run)

Pipeline-only phase (raw art unchanged): highlight ceiling 0.85 on the
tone ramp in `mock-map/map_gen.py` — pure paper now dithers at ~85%
density instead of saturating to solid ink.

| Metric (whole asset) | phase-1f | phase-1g |
|----------------------|----------|----------|
| near-solid-white 8x8 blocks (>90% ink) | 8.0% | **0.0%** |
| whole-image ink share | 59.9% | **50.8%** |
| mountain-band shadow blocks | 11.6% | 14.4% (spread kept) |

Ceiling sweep 0.85/0.78/0.70: below 0.85 the mountains' lit ridge
faces go flat (lit blocks 9.0% → 1.7% → 0.0%) — 0.85 picked.

Evidence: 03-map-on.png (halftone texture across the ground, no solid
white patches, mountain contrast intact).

## Artifacts

`screenshots/01…10`, `checks.json`.
