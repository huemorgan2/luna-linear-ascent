# Phase 3 — Measurements and browser verification

## Goal
Show reproducible measurements from the imported engine and verify actual-engine play through a browser.

## Steps
Run targeted and full simulator tests, a short repeated cohort and CPU parity. In a browser, create a synthetic player, hunt through actual engine options, observe energy/rewards, inspect saved curves and download/replay. Record screenshots, source hashes and gaps.

## Verification
Real browser walkthrough and screenshot judgment, exact action replay, saved-data/UI agreement, responsive layout. Never treat synthetic heuristics as measured human demographics or local engine results as shared-world deployment validation.

## Rollback
Revert the final phase-3 verification/UI commit, then `git revert 45b97a5` to remove the recovery-policy correction. Restart only `simulation/serve.py`; preserve saved runs and browser evidence. The exact final commit is recorded in the parent plan after committing.

## Execution status
Complete for the personal-engine scope. Final simulator suite: 45 tests pass in 10.059s. Serial/two-worker complete-result equality, full-state replay, source mutation guards and a mocked 128-worker Windows dispatch pass. Six 12-player/30-day cohorts compare three matched seeds before/after adding the existing stew action to four policies, with no game rule changes. Afterward median readiness is floor 4 on every seed; the 36-player sample reaches at most floor 6 and does not establish human progression limits.

Real Chromium walkthrough: 21 recorded steps pass, zero JavaScript errors, exact 33-input replay, matching downloaded JSON and 390px mobile width without overflow. The agent inspected monster art/stats, combat receipts and mobile screenshots. Three browser regressions were recorded, corrected and rerun; failed-attempt evidence remains. See `simulation/verification/003/summary.md` and `research/simulation-audit/ENGINE-RESULTS.md`. This is a local actual-engine browser test, not a production Luna/shared-world test. Shared warden party sizes remain explicitly unmeasured.
