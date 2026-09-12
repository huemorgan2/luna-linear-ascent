# Phase 2 — Bounded search and independent validation

## Goal

Find reproducibly stronger legal strategies using ordinary deterministic software and available CPUs, and preserve every trial for inspection.

## Steps

Enumerate a bounded grid of weapon focus, investment priority and farming risk. Run matched initial players/seeds and schedules, save full candidate outputs, rank milestone coverage and time including unfinished players, then repeat finalists on separate seeds. Store training/validation sets explicitly and report variability and failures. Select a normal-swarm planner profile only after validation.

## Verification

Same search seed/worker-count gives the same ranking and semantic outputs; every report points to a valid saved actual-engine run. Held-out seeds do not enter selection. Report observed, not proven optimal, speed.

## Rollback

Revert phase commit; preserve candidate/validation results and the previous default profile.

## Execution status

Pending.
