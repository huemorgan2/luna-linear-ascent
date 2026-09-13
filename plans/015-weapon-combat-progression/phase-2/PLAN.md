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

Implementation in QA, browser verification in progress. Plugin commits `0ebba87`, `f73d853` and `46c432d` introduce candidate0.113.2. Enrollment remains off in production. Ownership migration is idempotent, exact School receipts refund once, overflow XP is retained, three deck cells use distinct owned instance IDs, and old shop/mail/pack paths cannot duplicate those instances. Legacy equipment retains its exact attack/honing/oil/condition. Existing local integer ledgers widen to BIGINT without removing history; rollback retains the wider columns.

Verification so far:

- Actual worldd full suite:229 passed in356.21s (`/tmp/ascent-phase2-worldd.txt`). The5 new cases cover two-client same-scene requests, same retry key across players, stale actions, web double-click and exact School refund.
- Plugin full suite after ownership bridge:1454 passed,10 pre-existing failures,2 skipped,1 expected failure in127.53s (`/tmp/ascent-phase2-ownership-plugin.txt`). The10 failures match phase1's named baseline failures; they remain release-gate work, not silently accepted new regressions.
- Latest collection/character/setup targeted checks:19 passed. Actual local PostgreSQL tests:3 passed in2.41s, including history preservation and a2^40 currency row. HTTP/web targeted checks:17 passed; repeating after final vendor refresh.
- Simulator regression suite:56 passed in68.910s. These are legacy regression checks, not evidence of the unimplemented group progression curve.
- All1573 package files match the vendored package. Wiki regeneration passes with425 distinct creature images.
- Browser regression found: Luna denied that the visible collection existed. Root cause: the character tool still returned old slug-only ownership and offered no collection action. Commit46c432d adds owned collection details/actions to the sheet and updates live tool guidance. The same user query is being repeated after the QA restart; no pass claimed yet.

Before candidate data writes, code rollback is `git revert 46c432d f73d853 0ebba87` in the plugin plus its matching parent vendor/service commits. After candidate writes, keep the collection reader/receipt settlement and disable new enrollment; do not restore older player snapshots. Root implementation commit and final browser report are recorded on phase completion. No production conversion or deployment has run.
