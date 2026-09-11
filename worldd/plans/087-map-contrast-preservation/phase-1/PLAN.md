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

Complete — 2026-09-11.

- Baseline `map_002_492x369.png` SHA-256: `36c8e54a8a446eb4be147b52335db7c95b90342ca93d9009795066abd3294a61`.
- The current conversion retained `0.4096` territory tone range and `0.0756` standard deviation, against `0.497` and `0.104` in the approved source reference.
- Four candidates were generated and measured in `../evidence/metrics.json`. All passed the numerical floor; native-size inspection selected `box_direct` because it had the best source correlation (`0.9955`) and retained the source tone range (`0.4994`) without the extra edge noise introduced by sharpening.
- Selected recipe: trim the decorative frame, crop to 4:3, reduce directly to 492×369 using Pillow `BOX`, then apply the existing 8×8 Bayer threshold and the existing black/`#d9d9d3` palette. No autocontrast, gamma, highlight ceiling, or sharpening is applied.
- Selected candidate SHA-256: `d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e`.
- Production and packaged game assets were not changed in this phase.
