# Audit, progression and playable group walkthrough

## Preconditions

Local simulator running; original and audited runs exist; no production account needed. First user action: open a run and inspect why a player stalled.

## Scenario

1. Open localhost:8766, select original run and inspect a player's resources; switch to an audited run and inspect the same panels. Confirm model revision is visible and missing legacy telemetry is explicit.
2. Inspect spending, next-upgrade deficits, recovery episodes, readiness causes and per-floor coverage. Match visible values to run JSON.
3. Open experiment results. Compare same seeds; inspect target floors with no qualifiers; verify no extrapolated zero-day successes.
4. Open the fight lab. Play a group with three weapons. Use the wrong and right affinity/reach choices; observe resource and damage differences. Use knockback/pullback and escape.
5. Start a group with fewer energy points than enemies. Observe the exact enemy where exhaustion begins. Win a full group and inspect secured haul; retreat after a kill and confirm XP retained, pending gold forfeited and queued energy unspent.
6. Inspect desktop and narrow layouts. Invalid input must not create a run or mutate a fight. Save screenshots and judgments.

## Expected behavior

One combat engine drives swarm and interactive prototype. Outcomes are reproducible, controls explain counters and costs, progress shows measured coverage and reasons, source revisions and experiment differences remain visible. No promise of production parity or human fun from bot results.

## Fail conditions

Negative resources, grant/repair loophole, stale run data, misleading averages, missing legacy fields shown as zero, hidden target fitting, weapon swaps exceeding three slots, early haul credit, or invisible exhaustion transition.

## Verify

Write numbered evidence at simulation/verification/002 with commit SHAs, test counts, run IDs, screenshots and an explicit qualitative verdict. Fix observed UI regressions and repeat affected steps. Record limits separately from failures.
