# Phase 2 — Item instances, fixed decks and safe state

## Goal

Implement versioned item/deck/group/receipt state in QA with exactly three available slots and no lost or duplicated ownership. Both backends must accept the same valid actions and refuse the same invalid ones before the group loop is enabled.

## Steps

1. Implement the contracts in `RULES-AND-MIGRATION.md` in the plugin state/content/core and worldd ownership/persistence paths. IDs distinguish duplicate families and conditions; keep ten equipment bands, storage rules and unrelated defensive slots separate.
2. Set three available battle cells in creation and migration; remove only School offers/fees/locks for extra battle weapon slots (`carry 2` / `carry 3`) in all action and text paths. Keep the School, its other lessons/mastery/training, and already-earned learning; unrelated pack progression is retained. Replace first-held-family attack lookup with explicit selected-instance actions. Keep a compatibility reader for old documents and old active fights.
3. Add persisted offers, group/member lifecycle, deck locks, energy/kill/settlement receipt identities and XP reserve accounting. New instance/receipt fields must serialize losslessly, including large numbers.
4. Implement read-only conversion preview and reconciliation tooling (new tool path/CLI to be recorded before use). Audit old honing/style/oils, storage/pawn/gifts/faction assets and paid `carry 2`/`carry 3` receipts. Draft exact/capped fallback compensation from evidence; no production apply.
5. Add local/HTTP contracts for ownership, stale actions, duplicate receipt IDs, XP overflow/spending/cap30 and invalid deck changes. Add tests for serializers, profile visibility and tool payloads.
6. Commit plugin first, pin root submodule/vendor and matching service schema. Candidate rules remain isolated in QA; do not expose half-converted production players.

## Verification

Create targeted tests for the new instance/deck/migration contracts, then run them in both backends. Existing regression entry points include `PYTHONPATH=plugin-linear-ascent python3 -m pytest plugin-linear-ascent/tests/test_069_slots_not_pack.py -q` and, from `worldd`, `python3 -m pytest tests/test_web_play.py -q` against an isolated test database. Update old assertions only for explicitly changed contracts. S02/S10 inspect one/two/three-slot saves, two same-family weapons, complete ownership reconciliation, third-slot refund once and a read-only second player's profile. Run the phase's required full suites.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Disable candidate mutations in QA. Revert this phase's engine/UI commits in reverse order, retaining compatibility readers and original save fields if any candidate writes occurred. Reconcile ownership and XP from receipts; never replace a progressed player with a preview snapshot. Record concrete migration preview/apply/compensate command syntax and receipt selectors before phase 7 can execute conversion.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Not started. Rewritten for the three-weapon/group design on12 September2026; authorized for implementation by the subsequent user request. This document is not evidence that runtime changes or tests have run.
