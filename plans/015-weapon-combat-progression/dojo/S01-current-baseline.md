# S01 — Current-game baseline

## Preconditions

Pinned old rules, fresh and frontier-strength QA characters, no automatic energy refills.

## Scenario

Start with “play linear ascent”. Hunt normally and deeply; visit ordinary keeps1/31/99 and milestone keeps10/50/100 using appropriate fixtures. Record entry, every paid swing, exit and the shared HP seen by a second player.

## Expected behavior

The report describes actual charges, timing and old milestone resolution without presenting either as the replacement design.

## Fail conditions

Per-round refill hides exhaustion; theoretical damage is reported as an observed kill; a production state is changed to make the test pass.

## Verify

Reconcile player energy/HP/gold and server timestamps after every exchange. Record the exact damage-report boundary and the suspected pool-calibration mismatch.

Record SHAs, environment, PASS/FAIL with notes, screenshots and any regressions in a numbered dojo results folder. Fix failures and rerun the affected scenario before marking its phase complete.
