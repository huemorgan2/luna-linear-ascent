# Phase 1 — Pinned rules and combat

## Goal

Provide reproducible source inputs for 100 floors, 425 creatures, 16 weapon families and 84 upgrade states, and executable group-combat contracts for fixed decks, exhaustion and reward settlement.

## Steps

1. Add `simulation/export_inputs.py` and a checked-in snapshot from the inspected wiki/released economy. Store source hashes, revision and reference economy/warden tables.
2. Add versioned configuration, player/item records and seeded combat using the proposal's counter matrix, distance, partial shields, techniques and one energy per enemy.
3. Make model assumptions explicit: derived training/defensive-equipment/repair/arrow policies, group composition, sleep, readiness threshold and proposed warden healing. Do not call this the production resolver.
4. Add targeted deterministic tests for provenance/shape, energy latched per enemy, partial retreat, full-haul settlement, status timing and reach.

## Verification

`python3 -m unittest discover -s simulation/tests -p 'test_combat.py' -v` and `python3 simulation/export_inputs.py --check` after the exporter is implemented. Compare the source-snapshot hashes and counts to the pinned release. Check no production files changed.

## Rollback

Revert the phase implementation commit recorded below with `git revert --no-edit <phase-commit>`. No live data or source game files are mutated.

## Execution status

Not started.
