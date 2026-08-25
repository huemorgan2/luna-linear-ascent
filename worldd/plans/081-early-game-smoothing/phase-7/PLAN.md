# 081 phase-7 — dojo walkthrough + judgment

## Goal

All six scenarios in `worldd/tests/081-early-game-smoothing/` walked in
a real browser against a local env running the same code paths as
production, judged with evidence. Results folder under `dojo/results/`
with summary.md (date, worldd + plugin SHAs, environment), per-scenario
PASS/FAIL table, screenshots, regressions list. Execution status
appended to every phase PLAN.md and committed.

## Steps

1. Bring up local env (same code paths as prod), seed three players:
   sender (level ≥ 2, funded), receiver (fresh level 1), bystander.
2. Walk scenarios 01–06 in order (01-relay-collect, 02-pity-misses,
   03-directed-toasts, 04-levelup-hint, 05-gear-clarity,
   06-encounter-type-clarity), screenshotting each Expected-behavior
   checkpoint and running each Verify block (DB queries, ledger reads).
   Scenarios 05 and 06 are walked on BOTH a desktop and a mobile
   viewport.
3. Any FAIL is filed as a regression in the results folder — not fixed
   mid-run.
4. Write `dojo/results/00NN-081-early-game-smoothing-<date>/summary.md`
   + screenshots.
5. Append "Execution status" to phases 1–7 PLAN.md files; commit.
6. Deploy (explicit: push, trigger via API, poll to live), then
   post-deploy verification: re-run scenario 01's Verify queries against
   prod, confirm huemorgan4's ledger evidence recorded in phase-1.

## Verification

The results folder itself, plus green full suites at the walked SHAs.

## Rollback

Not applicable (no system change in this phase); deploy rollback is the
standard revert-and-redeploy of the offending phase commit.
