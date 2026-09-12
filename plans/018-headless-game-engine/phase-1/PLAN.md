# Phase 1 — Actual engine adapter

## Goal
Execute legal actions through the same imported core as worldd, with deterministic isolated time and source fingerprints.

## Steps
Add adapter/clock, replay entry point and source manifest. Verify character creation, combat, repairs, regeneration and exact document/scene/RNG parity with direct core calls. The game library remains unchanged.

## Verification
Targeted adapter unittest suite; inspect imported source paths; compare full canonical documents and scenes, not just final damage.

## Rollback
After reverting later phases, run `git revert 667f237`; preserve recorded runs. This removes the local adapter and its tests without touching game or database state.

## Execution status
Implemented: same worldd gamepath resolution, unmodified imported core, context-local virtual clock, source manifest, replay guard. Five adapter tests verify full document/scene/RNG parity, real entry costs, XP-gated repairs, source guard and concurrent clock isolation. Full simulator suite: 37 tests passed. The actual game loader emits existing unclosed-YAML ResourceWarnings; no game source was changed.
