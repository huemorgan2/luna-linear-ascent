# S06 — Forge/source settings and concurrent item actions

## Preconditions

Phases 3,4,7. Common+0/+19/+20, damaged/broken items and a Legendary shop/drop pair; exact known materials/gold; two clients on the same owner.

## Scenario

Open upgrade details from profile/collection; navigate to Forge, request the same upgrade twice from two tabs, try insufficient resources and a stale quote. Upgrade a damaged/broken weapon. Inspect shop/craft/drop +level and condition. Try upgrading a committed group weapon.

## Expected behavior

Only Forge can perform the transaction. One level/cost is applied once; +20 is explicit; condition fraction is preserved. Shop Legendary+6/full and dropped+0/10% show their actual gates/stats. A committed weapon cannot be changed mid-group.

## Fail conditions

Remote card upgrade, duplicate deduction, full repair hidden in an upgrade, double honing multiplier, source gates bypassed, wrong item instance, or a broken item becoming usable without repair.

## Verify

Check quote/rules/instance revisions, paired material and gold deltas, level/endurance and transaction deduplication; verify the card and text reply match.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
