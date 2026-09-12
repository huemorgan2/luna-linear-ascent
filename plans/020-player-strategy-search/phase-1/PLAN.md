# Phase 1 — Correct observations and capable legal decisions

## Goal

Remove artificial session-boundary progression delays and demonstrate a planner using actual recovery, equipment, selling and training actions without changing game rules.

## Steps

Add historical/session and improvement-triggered probe modes. Cache only identical observation inputs and chain passed floors at the same time. Add configurable planner decisions, engine-sourced action/cost checks and route learning. Record resource/action causes and progression changes. Existing named heuristics remain available for comparisons.

## Verification

Regression tests for multiple same-time floor qualifications, no recheck on unchanged state, real healing consumption, actual pawn proceeds/equipment preservation, no repeated losing-route loop, full-state replay and CPU equality. Inspect short real-engine trajectories for invalid/ineffective planned actions before longer search.

## Rollback

Revert this phase's commit after reverting dependent phases; restart only the simulator. Saved baseline runs remain unchanged.

## Execution status

Implemented. 51 simulator tests pass (8.481 seconds), including actual medgel/pawn receipts, replay and existing CPU parity. Canary 20260912T193211Z-d17dd06f: 4 players, 3 days, seed 1701, 4 workers, 15.414 seconds. All four qualified for floor 4 within 0.0051–0.0058 days; final character level 2, 59–102 kills, 0–1 deaths. No invalid-action refusal. This combines improved observation and decisions; causal comparisons follow in phase 2. Engine fingerprint remains 3217d52ec623a7b41376921310173bf681573edbe6c9e9d730fccc6a7ae29dae. Historical runs preserved.


Longer-run regression: search 20260912T193841Z-1cedebc9 exposed repeated `close_in` refusals when the preferred blade was held in a side slot and the lead was ranged. A direct-core regression failed before the fix. The planner now scores only usable held attack rows; probes fail visibly on refusals and searches disqualify refused/looping decisions. The original 48-trial search is retained with status `invalid`; it cannot support a recommended path. New selection/validation seeds will be used after this correction.
