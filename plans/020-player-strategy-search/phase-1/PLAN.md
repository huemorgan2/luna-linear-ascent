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

Pending.
