# Phase 1 — Baseline and reviewed contracts

## Goal

Pin one current game/vendor/service/wiki revision, establish a measured old-game baseline, and freeze the reviewed collection/group/energy/UX contracts and initial progression target before changing gameplay.

## Steps

1. Integrate published `origin/main` work (observed at `1897edd`) with completed simulator work (`65f3c1c`) in a clean checkout. Preserve unrelated local edits. Record root/plugin/vendor/wiki versions and engine hashes; resolve source differences without retuning gameplay.
2. Review the parent plan and its three companion documents. Freeze sequential-first, collection naming, starter access, XP reserve, death/haul policy, Air Power exception, candidate exhaustion and target pacing. Record what remains optional, especially simultaneous waves and dry-streak protection. Measure and settle the separate warden energy/cadence proposal before phase 6 sizes bosses.
3. Inventory every affected game action, scene, storage/ownership consumer and world effect. Produce a before/after schema/action map and baseline creature/item/reference table exports. The plugin, vendor, local backend, HTTP backend, wiki and simulator inherit these contracts.
4. Reproduce normal/deep entry, School slots, XP clipping, Shield wall and ordinary/milestone wardens through real QA web and Luna. Record actual action/request/display times and finite energy; no per-swing refills. Use S01.
5. Repeat a small actual-engine search/comparison on the integrated source. Keep the old 0.111.0 reports immutable. Identify policy failures separately from economic or world gates; do not run the historical proposal model as the new baseline.
6. Write baseline findings and concrete screen/action review fixtures. Commit these contracts before phase 2 begins.

## Verification

After integration, run `python3 -m unittest discover -s simulation/tests -v` and `python3 worldd/tools/gen_wiki.py --check`. Run the bounded comparison command in `research/simulation-strategy-search/RESULTS.md`, recording new run IDs/hashes rather than replacing old reports. Verify sample action replay. In S01 record floors 1/10/31/50/99/100, entry/swing energy, maximum legal swings, accepted timestamps and shared HP settlement. Document unavailable QA prerequisites rather than passing missing checks.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Record the integration commit and both parent SHAs before proceeding. Before any new rules exist, revert that integration with `git revert -m 1 <recorded-merge-sha>` if a merge was used, or revert its recorded integration commits in reverse order; revert only this phase's adapter/report changes. Preserve all historical result files. No production or player-state conversion belongs to this phase.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Baseline captured and contracts committed on13 September2026; proceed to phase2 candidate implementation. See BASELINE.md and dojo/results/0064-015-legacy-baseline-2026-09-13 in the parent repository. Server224 tests and simulator56 tests pass; source alignment retains the same10 pre-existing plugin failures. Exact replay, Vault timing, finite-energy probes and real Luna creation/School/Vault/normal-hunt are recorded. The bounded baseline did not exercise every older S01 browser case; those unrun cases are explicitly listed and must be covered on the candidate before release. No new gameplay or production conversion has occurred. Baseline/alignment commits: root4e51eb6 and213062a, plugin06134b0 and1f1b661. Rollback alignment with git revert1f1b661 (with normal spaces); root integration with git revert -m1 1f45fb1.
