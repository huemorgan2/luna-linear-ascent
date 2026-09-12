# S08 — Kill XP, pending haul and all outcomes

## Preconditions

Phases 3,5,7. Groups with known reproducible reward seeds, full XP bar, full pack, contract/weekly progress, carried purse and previously secured materials; revive and rescue cases.

## Scenario

Kill a member and inspect XP/haul; try spending/trading/claiming its pending rewards. Finish one group, escape another, die on the final exchange, revive in place and use rescue extraction. Retry a final kill and claim from two tabs.

## Expected behavior

XP is earned once per resolved kill including overflow. Only a full clear while alive secures the haul; extraction/failure forfeits it. Earlier possessions are accounted separately. Contracts/assists cannot cash out unfinished loot; full-pack rewards remain claimable.

## Fail conditions

Clipped earned XP, double XP/item/gold, loot rerolled at claim, pending gold deducted from the purse on failure, death granting full-clear reward, lost overflow item or unlimited claim storage.

## Verify

Reconcile enemy kill IDs, XP/reserve/rested bonus, pending/secured ownership, objective receipts and outcome. Check that mutual final death keeps XP and forfeits haul.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
