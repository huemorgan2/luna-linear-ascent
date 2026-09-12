# Phase 8 — Explicit release and measured rollout

## Goal

Release one coherent, source-pinned game after review and verification, preserving player investment and confirming both new/returning play and shared wardens on the actual serving system.

## Steps

1. Require phase1–7 reports, approved rules/target decisions, rollback runbook and source/art/content manifests. Inventory production active fights/wounds/pledges and snapshot before the planned conversion. Snapshot is evidence/recovery input, not permission to overwrite later progress.
2. Canary the complete release in an isolated QA world; verify health, new-account opening, migration and a shared warden. Do not mix old/new rules among players damaging the same boss.
3. Commit plugin implementation first; push its branch/revision; update and commit parent submodule/vendor, service, clients and generated wiki together. Run secret-pattern scans and all required release checks before commits.
4. Deploy only after explicit release authorization: push intended release revision, trigger the deployment API, poll serving revision/health, execute the reviewed migration boundary and verify receipts. The current planning-task push is not this deployment.
5. Immediately verify real opening/profile/collection/group/Forge/reconnect and two-player warden behavior. Verify the service imports the pinned game path/hash and wiki labels reflect implemented rules.
6. Observe group clear/escape/death rates, net recovery cost, exhausted kills, duplicate/refused actions, stalled floor/material gates, deck/route choices and actual warden demand. Compare the reviewed schedule/cohort to its predictions; do not disguise population differences as balance improvement.
7. Pause new candidate entries and execute the tested rollback path if ownership/reward integrity fails. Investigate pacing deviations before changing coefficients; version future tuning. Append execution evidence and deployed SHAs to every phase.

## Verification

Use the exact deployment, health, migration/reconciliation and rollback commands recorded in phase7 for the chosen environment. Do not substitute hypothetical endpoints. Run S14 post-deploy on authorized test accounts, inspect persisted receipts and actual serving version, and record response times/screenshots. Verify monitoring covers lost/duplicate rewards and zero-resource recovery as well as HTTP health. Keep production data and historical kills/eras intact.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Execute the phase7 rehearsed runbook: stop new candidate entries, retain readers, drain/settle groups once, compensate selected receipts and revert routing/version at the recorded world boundary. Roll back the release through the recorded deployment API/revision if compatible. Never restore an old database over new progress, duplicate compensation, or reopen a closed rewarded era. Record every operation and post-rollback verification.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Not started. Rewritten for the three-weapon/group design on12 September2026; awaiting the user's plan review. This document is not evidence that runtime changes or tests have run.
