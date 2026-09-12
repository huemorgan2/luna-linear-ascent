# S12 — All creatures, weapon art and honest drop odds

## Preconditions

Phases 4,7. Generated wiki and candidate runtime use the same definition revision; all425 creature records and64 weapon-grade art records available.

## Scenario

Move the floor slider through early/middle/late floors; inspect actual animal images and traits. Open full loot settings, switch normal/deep and specimens, compare individual enemy and group chances. Select all four weapon grades and bought/crafted/dropped source cards.

## Expected behavior

Roster/images change with floor; no animal has more than three near-identical variants. Frames and weapon silhouettes vary by grade. Odds, quantities, source levels/condition and gates match the engine; group odds state completion assumptions.

## Fail conditions

Only eight recycled creatures, tint-only grade art, identical probabilities for every species, probabilities over their defined caps, summed independent odds, proposed settings advertised as implemented, or a second conflicting balance table.

## Verify

Run generator/lint checks, count IDs/assets, compare sampled dossier/loot/source parameters to engine calculations including tiny probabilities and caps. Capture floor and grade changes.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
