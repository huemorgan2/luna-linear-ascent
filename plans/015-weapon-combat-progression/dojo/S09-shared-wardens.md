# S09 — Concurrent wardens and the true finale

## Preconditions

Separate QA world, version-matched clients, multiple actual browser players plus authenticated load clients for larger parties; bosses 10/50/100, fixed HP/healing and finite budgets.

## Scenario

Observe idle healing, attack from two browsers and watch shared HP change per accepted hit. Compare staggered with overlapping attacks. Add finite-energy group load, disconnect/rejoin, duplicate requests and nearly simultaneous killing blows. Kill100 through actual combat.

## Expected behavior

HP/healing follows server time. Prepared overlapping groups win within their budgets; insufficient groups and the strongest permitted solo finale build fail. One real death awards once and closes the era once at 100.

## Fail conditions

Private damage is banked; pledges resolve victory; clicks change tick speed; infinite-energy assumptions; rewards/refunds repeat; no viable UI cadence; a second final blow ends the era again.

## Verify

Inspect player costs, per-action IDs/timestamps, boss state, status clocks, contribution and kill receipts, frontier and era records. Load tests support rather than replace the multi-browser walkthrough.

Record SHAs, environment, PASS/FAIL with notes, screenshots and any regressions in a numbered dojo results folder. Fix failures and rerun the affected scenario before marking its phase complete.
