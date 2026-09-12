# 020 — Find and simulate stronger player strategies

## Problem and evidence

12 September 2026: the user requests fixing poor simulated decisions, finding strong progression paths and displaying fastest versus typical progress. Actual-engine run 20260912T190733Z-fba5d7a7 has a floor-5 population median of 28 days and earliest observed arrival of 8.6667 days. Trace inspection finds unused medgels, unsold obsolete equipment, repeated losing fights and a readiness host that credits at most one floor per session-boundary check. The user wants rapid day-one progress and gradual later deceleration, but asks to discover legal strategies rather than invent faster results.

## Root cause

The engine is shared correctly, but the decision layer covers too few legal choices. It buys some upgrades greedily, does not use carried road-healing supplies or pawn redundant equipment, and does not learn when a farming route is unsustainable. Probes run only at session boundaries and the staged world fixture waits for them, introducing artificial delays. A strategy's name is not evidence of competence. Fastest observations also mix skill with luck and need independent validation.

## Mitigation already taken

Real-engine imports and replay are in place. Historical results remain immutable. Plan 019 adds clear day/floor labels and the earliest observed player line; no game balance changes were made.

## Phases

1. Correct measurement timing and add a configurable, legal-action planner. Measure readiness after relevant improvements and allow successive already-qualified floors in one check; preserve the historical mode for paired audit. Use actual engine healing items, pawn offers, equip choices, training and prices. Add route-risk learning and exact action diagnostics. Do not grant resources, peek at future RNG, bypass gates or mutate game rules.
2. Implement deterministic CPU-parallel strategy search across a bounded parameter grid, save every candidate run and search report, then validate leading candidates on seeds not used to select them. Rank censored progression by milestone coverage and time, not by the fastest lucky survivor. Keep equal schedules and initial player seeds across candidates. Add the supported winning profile to the normal swarm.
3. Run baseline/corrected/planner comparisons and a longer validation where useful. Show source/settings differences, strongest observed paths and their holdout results in the local dashboard. Verify replay, CPU identity, immutable probes, valid costs, honest missing values and both fastest/median lines in a real browser. Document measured remaining game bottlenecks without claiming a mathematical optimum or a human forecast.

## Verification

Targeted actual-engine tests before each subsequent phase, then full simulator suite. Read saved trajectories and verify acquisition/healing/sales through engine receipts. Compare engines by fingerprint. Search must record candidate settings, failures, seeds, all run IDs and independent validation. Browser scenario: inspect the resulting cohort, fastest and median floor-5 tooltips, winning strategy/path, missing floors and exact replay. No LLM executes simulated players.

## Operational notes

Simulator code only. No production credentials or game accounts; no engine or worldd changes. Existing saved runs remain readable and are not deleted. The server must finish its current job before restart; fresh processes are required after changing Python runner source. Available CPU detection remains automatic. Shared-world warden victories remain unmeasured.

## Rollback

Revert phase implementation commits in reverse order (record exact SHAs after each phase), restart only simulation/serve.py, preserve simulation/game-runs and strategy-search reports. No database rollback.

## Execution status

Plan written before implementation. Investigation confirms carried road heals are legal via use_medgel/use_trauma_kit at the camp; actual pawn offers and equip APIs exist. Phase implementation pending.
