# Phase 3 — experiments

## Goal

Run paired multi-seed experiments and report progress against provisional target ranges.

## Steps

Add a batch CLI and website experiment view. Run original model, audited model with old decision logic, improved decisions, and single-factor repair/durability/group/recovery changes. Keep seed/policy/activity cohorts fixed; preserve every run. Report reached fractions, full-population quantiles, paired deltas and failures. Recommend a next design experiment with no hidden defaults.

## Verification

Verify batch resumption/config identity, seed coverage and aggregate math. Run horizon extensions where needed; do not infer eventual completion from censored cohorts.

## Rollback

Revert the phase implementation commit recorded below; preserve saved runs and baseline files. Stop/restart only the simulator server if its API changed.

## Execution status

Not started.
