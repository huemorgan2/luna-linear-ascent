# 080 scenario — portrait regression (phase 1 must change nothing)

## Preconditions

- Local worldd on :8600, static served.
- Phase 1 (lib/character.js + model move) deployed locally.

## Scenario

1. Capture a BEFORE screenshot of
   `/static/site/figure3d/test.html` (all three races, worn gear) at the
   pre-phase-1 commit, or use the 0049 dojo run's portrait screenshots.
2. Open the same harness after phase 1. Wait for all figures to render.
3. Screenshot; zoom-crop each race.

## Expected behavior

Same silhouettes, same gear placements (sword on hip, bow on back, shield
on forearm, staff in fist), same shading character (solid-black shadow
cores, sparse-dot rolloff, white lit sides), same frame composition
(feet on baseline, 1/8 right shift, giant towers).

## Fail conditions

- Any figure missing, T-posed, or floating.
- Gear placement visibly different from before.
- Console errors (404 on moved GLBs, import failures).
- Hover tint no longer works on the gearmap.

## Verify

- Network tab: player/item GLBs load from `/static/site/lib/models/…`,
  none from `figure3d/models/…`.
- `pytest tests/test_071_figure3d.py -q` green.
