# S06 — Forge, inventory and accessibility

## Preconditions

All64 variants, materials, +0/+19/+20 instances, two tabs and two QA players.

## Scenario

Inspect through hover, focus and tap; attempt upgrade outside the Forge and during combat. At the Forge, retry one request and submit competing quotes from two tabs. Try insufficient materials/gold, a stale item version, +20 and another player's instance.

## Expected behavior

Only a valid Forge transaction upgrades once. Every surface shows the same grade art, condition and owned/needed values. Selecting an upgrade never reserves the same materials on every card.

## Fail conditions

Double charge, free/remote upgrade, ownership leak, stale quotes accepted incorrectly, invented attack delta on a durability-only level, or unreadable phone controls.

## Verify

Inspect transaction receipts and both players' inventories, plus desktop and390px screenshots. Verify all 64 drawings and all 84 level states through data and representative UI cases.

Record SHAs, environment, PASS/FAIL with notes, screenshots and any regressions in a numbered dojo results folder. Fix failures and rerun the affected scenario before marking its phase complete.
