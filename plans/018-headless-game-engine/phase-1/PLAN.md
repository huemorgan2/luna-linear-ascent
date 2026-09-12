# Phase 1 — Actual engine adapter

## Goal
Execute legal actions through the same imported core as worldd, with deterministic isolated time and source fingerprints.

## Steps
Add adapter/clock, replay entry point and source manifest. Verify character creation, combat, repairs, regeneration and exact document/scene/RNG parity with direct core calls. The game library remains unchanged.

## Verification
Targeted adapter unittest suite; inspect imported source paths; compare full canonical documents and scenes, not just final damage.

## Rollback
Revert this phase's implementation commit; preserve recorded runs.

## Execution status
Not started.
