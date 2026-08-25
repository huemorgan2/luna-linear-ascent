# 080 scenario — arena inherits everything

## Preconditions

- Local worldd on :8600, phases 1–3 deployed locally.
- A tenant with the Labs arena flag on and worn gear.

## Scenario

1. Start a wilds fight on /play with the arena stage active.
2. Screenshot the standoff, one player attack, one monster attack, and the
   finisher the arena plays itself.

## Expected behavior

- The arena's 320×300 stage shows the same ink law as the finisher after
  phase 2 (it shares createStage/renderFrame): no banding, bodies separate.
- The climber wears their real gear (phase 3 dressing runs through the
  same buildPlayer path).
- Turn flow unbroken: attacks animate, HP meters move, the kill hands off
  to the liberation sequence.

## Fail conditions

- Arena regressed to banded shading or lost the scenery.
- Player gear present in the kill finisher but missing in the arena (the
  two paths diverged again — the exact drift this plan exists to end).
- Any JS console error from arena3d.js.

## Verify

- `data-arena` payload unchanged in shape; only the visual layer moved.
- `pytest tests/test_web_play.py -q` green.
