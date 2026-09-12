# S04 — Reach, counters and effects

## Preconditions

Candidate ground/air and affinity fixtures, affordable blade/bow/staff loadouts, known trait examples.

## Scenario

Fight a Common enemy, a Power ground target and a spell-dispersing Power flyer. Try a wrong counter, change ammo, apply poison to immune/living targets, and inspect burn/bleed/stun/slow/Expose timing.

## Expected behavior

Bad choices have understandable consequences; the right tools improve the outcome; reach and immunity are explained before cost where applicable. Each effect ticks on its defined clock.

## Fail conditions

Blades hit Air; magic resistance is applied twice; fresh DoT ticks early; changing weapons resets cooldowns; repeated clients multiply status ticks.

## Verify

Read server combat events and exact HP/energy/ammo changes. Compare the UI's active durations, labels and damage channels with the resolver.

Record SHAs, environment, PASS/FAIL with notes, screenshots and any regressions in a numbered dojo results folder. Fix failures and rerun the affected scenario before marking its phase complete.
