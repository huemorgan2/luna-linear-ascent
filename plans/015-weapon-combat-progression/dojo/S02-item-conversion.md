# S02 — Returning players and ownership conversion

## Preconditions

Phases 2,7. Isolated one/two/three-slot saves, duplicate old slugs, different honing/styles/condition, stored/faction items, complete and missing carry purchase histories, active old fight and full XP bar.

## Scenario

Preview conversion, open owner collection and another player’s profile, apply conversion twice, inspect each location and refund, finish the old fight then start a new hunt. Earn a new item/XP after conversion and rehearse compensation.

## Expected behavior

Three slots appear; item instances and ownership remain distinct; recorded fees refund once; XP overflow survives; other profiles cannot edit or expose private bank data. Old fight finishes under its old rules. Compensation preserves later earnings.

## Fail conditions

Item collapse/duplication, lost paid value, refund at an invented current price, double refund, mixed battle rules, stale snapshot replacing new progress, or a public profile carrying owner mutation actions.

## Verify

Reconcile per-owner item IDs, locations, XP/gold/refund totals and receipt IDs before/after both applies and compensation. Archive the exact implemented commands and inverse operations.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
