# S11 — Per-enemy energy, waiting and exhaustion

## Preconditions

Phases 3,7. Reproducible five-enemy group; one player starts with2energy and another with5; virtual-clock fixtures for regeneration/dawn and live-browser reconnect steps.

## Scenario

With2energy begin enemies1–5 and inspect each receipt; with5 leave after killing2. At zero energy kill an enemy, fail escape, revive, refresh and retry its start. Regenerate during an active member, then between members; inspect the waiting portrait and use a legal combat consumable to start it.

## Expected behavior

First two fights are funded, latter three exhausted, total charged2 assuming no regen. Retreat after two leaves3. Reads/failed actions do not start a member; a combat consumable does. Regeneration can fund the next enemy but cannot clear active exhaustion. Killed enemies grant normal XP.

## Fail conditions

Upfront5charge, normal/deep double fee, final paid enemy exhausted, repeated per-swing/start charge, negative energy, DoT halved twice, refresh/heal resetting the group, or charging an unstarted enemy on leave.

## Verify

Reconcile energy before/after and funded/exhausted latch on every member and request retry. Record direct/DoT/speed values and XP. Confirm no dawn/sleep/level-up HP injection mid-group.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
