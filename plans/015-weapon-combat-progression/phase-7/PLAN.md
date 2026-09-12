# Phase 7 — Full playthrough and migration rehearsal

## Goal

Demonstrate that new and returning players can understand and play the complete redesign across clients, and that converting/rolling back real-shaped saves preserves every owned item and earned balance.

## Steps

1. Rehearse the complete migration in isolated copies of representative saves: all old weapon/slot states, full/overflow XP, storage/faction assets, pending trades, broken items, legacy active fights, wounded wardens and pledges. Use anonymized fixtures; no credentials or player secrets in Git.
2. Run conversion preview, apply twice, reconcile and compensate using implemented tooling. Record exact executable commands, source SHAs, world IDs, receipts and inverse operations in a runbook. Demonstrate post-conversion progress is preserved on rollback, not replaced by old snapshots.
3. Walk every S01–S14 browser scenario, including multi-turn Luna and web, keyboard/tap, desktop/390px, profile/collection/popup and public/private visibility. Inspect ledgers and shared state beyond the displayed cards.
4. Run two-user/two-tab flows: A prepares a deck, B acts elsewhere, A reconnects; trade/refund/upgrade/final-kill races; active legacy fight finishing before new groups; stale cards attempting a fourth weapon.
5. Assess the actual opening and later mixed-group pacing. Ask the tester to explain current enemy, next threat, energy, weapon choice and pending reward. Record active minutes/actions and any repeated navigation. Regressions are filed with evidence before fixes and rerun.
6. Repeat representative real-engine strategy/warden validations after migration changes. Freeze release versions and the full art/content bundle only when all hard gates pass.

## Verification

Run targeted regression tests first, then `PYTHONPATH=plugin-linear-ascent python3 -m pytest plugin-linear-ascent/tests -q`, the full `worldd` pytest suite against an explicitly isolated test database, `python3 -m unittest discover -s simulation/tests -v`, content lint and wiki generation check. Zero untriaged new failures. Complete all browser scenarios with screenshots, client/root/plugin hashes and PASS/FAIL tables in a numbered results folder. Both a real multi-turn Luna walkthrough and web play are mandatory; a simulation or screenshot of a fixture alone does not substitute.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Use the rehearsed compensation runbook on the isolated converted world, retain compatibility readers, and preserve all newly earned receipts/items/XP. Revert only the phase's code fixes that are unsafe, then rerun affected scenarios and reconciliation. Production remains unchanged until phase8. A failed rollback rehearsal blocks release.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Not started. Rewritten for the three-weapon/group design on12 September2026; awaiting the user's plan review. This document is not evidence that runtime changes or tests have run.
