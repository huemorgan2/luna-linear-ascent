# Phase 2 — Real engine swarm and explorer

## Goal
The default CLI and website run actual-engine players in parallel and expose replayable evidence and progression graphs.

## Steps
Add legal-action heuristics, virtual attendance/session schedule, disposable readiness probes, engine-specific result schema and source-aware saved runs. Make actual engine the default UI/CLI; retain proposals separately. Add a headless inspector that displays real Scene options and results, without another combat implementation.

## Verification
Serial/parallel identity, same-seed replay, full state and money ledgers, honest censoring, no false proposed mechanics, HTTP job/download/replay lifecycle.

## Rollback
After reverting phase 3, run `git revert 8935fb8` and restart only the local simulator server; retain both result directories.

## Execution status
Implemented actual-engine action policies, spawned CPU workers, separate schema-v2 runs, default CLI/dashboard, signed game ledgers, full-state replay and synthetic interactive inspector. The world frontier fixture is explicit and recorded; shared-party outcomes are null. Historical proposals remain under /proposal. Full suite: 43 tests passed in 34.667s, including two-CPU identity, complete trace replay and HTTP isolation. Browser and longer-cohort verification follow in phase 3.
