# Phase 6 — Concurrent healing wardens and shared-world simulation

## Goal

All wardens, including100, lose HP from real accepted attacks and heal with server time. Actual finite-resource concurrent groups can win; measured solo/party outcomes and once-only unlock/reward/era effects replace pledges and formula-only claims.

## Steps

1. Freeze the reviewed warden energy/cadence and finite burst window using phase1 measurements and phase5 legal builds. The ordinary one-per-enemy policy must not become unlimited boss swings. Preserve exponential reference scale, then fit HP/regen to actual attacks and resources.
2. Implement authoritative hit/regen/status event settlement in worldd and matching engine effects. Validate actor state, per-account cadence and action IDs; commit each hit promptly. Use fixed-point/large-integer-safe values and deterministic timestamp/event ordering.
3. Replace milestone pledge/power-sum routing in keep scenes/tools/services. Reuse participant accounting, reward/kill receipts, frontier unlocks and era closure through the one actual shared-death transaction. Retire silence/pity mechanisms only through a documented wound conversion, not a hidden reset.
4. Specify contribution eligibility/reward shares, shared stun/Expose/DoT clocks and per-player gap. Add old-pledge refund and active-wound preview/reconciliation; migrate only at the planned world boundary.
5. Add an isolated-world headless adapter calling these same services with virtual time and independent world storage. Parallelize whole worlds/scenarios; verify its outcomes against the PostgreSQL-backed service. Include real unlock waiting and eligible hunter populations.
6. Measure staggered versus overlapping attacks and party sizes from actual capable players at all tested floors. Include specialists/generalists, high-power legacy builds, latency and finite energy. A required-player graph stays unavailable wherever no real service trial ran.
7. Rerun personal/economic conclusions under the actual shared frontier; tune only with recorded evidence. Show HP-over-time, healing, attack timestamps, energy exhaustion and successful/failed party traces.

## Verification

Add targeted shared-service tests for timestamp ordering, energy/cadence, two killing blows, retries, status ticks, cross-tenant identity and lossless floor100 values. Run both backend contracts and full worldd/engine/simulator suites in isolated storage. S09 uses two real browser players for overlapping attacks and a staggered control case; then real action-driven many-player trials for late wardens. Verify floor100 rewards and era closure occur once, that old pledges cannot win, and that a disconnect/refresh cannot bank damage or stall the world. Record minimum tested successful party and criterion, not a proven optimum.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Stop new candidate warden entry for the isolated world, pin/drain active battles and preserve all hits/rewards/era records. Reverse candidate routing only at a recorded world boundary with compatible readers. Apply the tested wound/pledge compensations once; never resurrect an already rewarded boss or rewind an era. Record concrete operations and receipt IDs during phase7 before any production conversion.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Not started. Rewritten for the three-weapon/group design on12 September2026; authorized for implementation by the subsequent user request. This document is not evidence that runtime changes or tests have run.
