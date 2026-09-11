# Phase 1 — measured conversion canary

## Goal

Select one 492×369 floor-2 conversion that retains the approved source's local tonal separation without losing the tiny structures and transport lines that establish scale.

## Steps

1. Save the old output hash and quantitative source/output baseline.
2. Produce separate candidates using area-preserving BOX and LANCZOS sampling, with no global gamma/highlight compression; test at most one mild edge-restoration variant for each sampler.
3. Measure 24px territory-block range, standard deviation, source correlation, total ink, and representative water/ground regions.
4. Inspect the candidates at native size and at the game's pixelated display scale. Reject moiré, broken roads, lost doors, flattened water, and blown highlights.
5. Select the smallest recipe that meets the thresholds; record its formula and metrics. Commit and amend phase 2 with findings.

## Verification

The selected candidate meets the top-level numeric thresholds and passes side-by-side visual review. No shipped package file changes in this phase.

## Rollback

Revert the phase plan/evidence commit and remove unshipped candidate files. Production and game assets remain unchanged.

## Execution status

Not started.
