# Dojo run 0059 — 082 phase-1f: the mountain tones return

- **Date:** 2026-08-26
- **Scenario:** `luna/dojo/tests/082-floor-maps/scenario.md` (walkthrough.mjs, phase-1e revision — unchanged)
- **Environment:** local worldd (uvicorn :8600), Postgres 16 docker :5434,
  vendor plugin = 0.110.1 (phase-1f changes uncommitted at run time;
  committed immediately after)
- **Player:** web:dojomap905399, seeded floor 1, warrior L3
- **Verdict:** **PASS — 33/33 checks**

## What phase-1f changed (verified this run)

Art-only phase. The phase-1e grey-wash raw left the mountains white and
toneless; per `plugin-linear-ascent/vision/1bit-images.md`, the raw was
re-rendered as model-DESIGNED dither art (two refs: the 1e raw for
composition, the 1d `raw_map_stump.png` for mountain tone).

Mountain band (upper-right quadrant), 8x8-block tonal spread on the
1-bit asset:

| Asset | shadow blocks (<25% ink) | halftone | lit blocks (>75% ink) |
|-------|--------------------------|----------|-----------------------|
| phase-1d (reference) | 11.6% | 61.7% | 26.6% |
| phase-1e (regression) | 7.3% | 77.6% | 15.1% |
| **phase-1f (shipped)** | **11.6%** | **60.7%** | **27.6%** |

Gamma stayed 1.15 (won the 1.0/1.15/1.3 sweep by matching the 1d
distribution exactly). All six marker anchors verified on the new art
by red-dot overlay — no coordinate changes.

Evidence: 03-map-on.png (shaded mountains, deep cast shadows, chip
inks unchanged).

## Artifacts

`screenshots/01…10`, `checks.json`.
