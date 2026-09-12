# S03 — First session and first upgrade

## Preconditions

A fresh candidate character with normal authored starter resources.

## Scenario

Type “play linear ascent”; use plain-text “2” for an actual numbered choice; hunt, reach floor 2, inspect +1 requirements, collect opening rewards, visit Forge, upgrade and fight again. Ask “where am I?” twice.

## Expected behavior

The player has a clear next step, earns the first upgrade without needing a random rare drop, sees its real benefit and spends resources once. Reads change no game state.

## Fail conditions

Developer grants/refills are needed; text choices fail; a read rerolls loot; a broken or unaffordable starter prevents progress; prose invents results without an action.

## Verify

Record the first 10 committed actions and all resource deltas. Verify grade/level/art, one transaction receipt and the floor/character gate.

Record SHAs, environment, PASS/FAIL with notes, screenshots and any regressions in a numbered dojo results folder. Fix failures and rerun the affected scenario before marking its phase complete.
