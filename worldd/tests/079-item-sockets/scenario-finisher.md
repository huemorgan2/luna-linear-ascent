# Scenario: attack-scene weapons in hand (fight3d harness)

## Preconditions

- Local worldd running on :8600, `/health` ok.
- Browser opens `http://127.0.0.1:8600/static/site/fight3d/test.html`.

## Scenario

1. Trigger one finisher per weapon family available in the harness: blade,
   bow, staff (use the harness's kill/replay controls; re-equip path runs on
   every replay).
2. Screenshot mid-swing for each (pause or repeat until a frame with the
   weapon at the strike apex is captured), plus one idle frame before the
   strike.

## Expected behavior

- The weapon rides the striking hand through the entire swing: hilt/grip
  stays in the fist volume from windup to impact — no drift, no floating
  beside the hand, no lag behind the arm.
- Blade reads blade-forward at the apex; bow reads held at its grip in the
  draw pose (the hand-keyed draw from PLAN4 unchanged); staff reads gripped,
  not balanced.
- Strike timing/arc unchanged from before the refactor (compare against a
  pre-change screenshot if in doubt).

## Fail conditions

- Weapon origin visibly outside the hand at any captured frame.
- Weapon scale or orientation changed vs. pre-refactor captures.
- Re-equip on replay leaks (two weapons after replaying a kill) — the wrap
  removal contract broke.
- Any console error from `fight3d.js` or `lib/sockets.js`.

## Verify

- Replay the same kill twice; traverse the scene from console and count
  weapon wraps on the hand bone — exactly one.
- `node --check` both modules; pytest `worldd/tests/test_web_play.py` green.
