# S14 — Migration, rollback and serving verification

## Preconditions

Phases 7,8. Phase7 uses isolated QA for a full dress rehearsal. Phase8 repeats on explicitly authorized release/test accounts after all prior gates. Exact migration/deploy/rollback runbook and snapshots exist.

## Scenario

Preview/apply/reconcile conversion, earn new XP/items, then rehearse compensation. Verify serving source hashes and health. Play the opening and returning-player collection, resume a group, perform Forge action and exercise two-player warden visibility. Inspect generated wiki and public profile. Record post-release integrity metrics.

## Expected behavior

Release serves one coherent ruleset; new and returning players preserve ownership and progress. Rollback retains post-conversion earnings. Visible behavior and receipts match the pinned version; both web and multi-turn Luna work.

## Fail conditions

Stale vendor replacing engine code, mixed rules on one shared boss, old snapshot restoring over new earnings, failed compensation, secret material in Git, false health-only success, or release without recorded authorization.

## Verify

Record root/plugin/vendor/serving SHAs, executed commands, world IDs, receipt reconciliation, timing and screenshots in a numbered result folder. Zero untriaged integrity regressions; runtime release status is separate from documentation readiness.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
