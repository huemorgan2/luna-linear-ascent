# S02 — Returning players and item identity

## Preconditions

Preserved fixtures cover every old weapon, multiple copies, hone/style/oil/wear, equipped/held/pack/storage/offer/reward locations.

## Scenario

Preview conversion, apply it in QA, inspect each location through player UI, refresh, and rerun conversion. Buy/receive another copy and change one instance.

## Expected behavior

Each item remains owned, distinct and usable with its documented power/condition. A second conversion makes no additional change.

## Fail conditions

Merged copies, missing paid stats, free extra items/gold, lost oil/style, an item becoming usable past a closed gate, or old clients corrupting new items.

## Verify

Compare before/after instance reconciliation and append-only receipts; verify both local and HTTP backends and the planned compatibility rollback.

Record SHAs, environment, PASS/FAIL with notes, screenshots and any regressions in a numbered dojo results folder. Fix failures and rerun the affected scenario before marking its phase complete.
