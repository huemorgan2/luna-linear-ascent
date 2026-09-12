# Phase 4 — fight-lab

## Goal

Make the proposed group mechanics playable locally and verify the diagnostic website in a real browser.

## Steps

Expose a bounded stateless action-prefix fight API using the same combat function. Show three weapons, legal attacks, gap, enemy type, energy, XP and pending haul; expose attack/pullback/escape. Use actual local creature art when available, bundled assets otherwise. Test actual proposed encounters and inspect screenshots; label this as a prototype and distinguish human fun from numerical outcomes.

## Verification

Complete coded suite; browser-run baseline/diagnostics/comparison; play counter/exhaustion/escape/victory scenarios, inspect wide/narrow layouts, and record evidence and remaining limits.

## Rollback

Revert the phase implementation commit recorded below; preserve saved runs and baseline files. Stop/restart only the simulator server if its API changed.

## Execution status

Superseded before implementation: user explicitly requested the actual game libraries instead of a duplicated proposal combat model. Plan 018 replaces this with a real-engine headless runner and inspector.
