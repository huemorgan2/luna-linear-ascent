# Phase 6 — Actual shared warden combat

## Goal

All wardens, including floor 100, accept actual player attacks against one continuously healing HP value. A sufficiently prepared group can finish within real energy/HP limits; the finale cannot be cleared by a legal single account.

## Steps

1. Freeze a reference party curve using the measured final combat rules. Tune HP, fixed healing and action cadence together; account for the current per-swing energy unit explicitly. The ranges in the main plan are initial targets, not counted quorums.
2. On each accepted action, advance server-time healing and settle damage immediately in one transaction with player energy/ammo/condition. Never bank private exchange damage for later submission. Use exact integer/fixed-point quantities and deliberate wire encoding for large values.
3. Deduplicate action IDs and serialize death settlement. Give boss DoTs independent real-time clocks, shared stun resilience, a shared bounded Expose state and per-attacker displacement. More clients must not produce extra ticks.
4. Replace every milestone pledge/combined-power route. Reuse verified contribution receipts, frontier advancement, rewards, memorials and floor 100 era closure.
5. Before live conversion, snapshot active boss state and pledge records. Select an idle/fallen boundary or an explicit wound conversion; refund each unconsumed pledge once. Do not silently erase earned damage.
6. Make healing speed, current HP, accepted damage and participation visible. Normal Luna/web latency must be viable; coordinate real attacks rather than requiring rapid raw requests.

## Verification

Run timestamped simulations with misses, setup, healing, withdrawal, death, disconnect and finite energy at every floor. Test intended and strongest legal legacy loadouts, solo bursts as well as sustained damage, and about 50 reference versus35 optimized players at 100. Run dojo S09 with multiple actual browser players on10/50/100; then server load tests at the intended larger group size. Staggered attacks must lose where an overlapping prepared burst wins. Test duplicate final blows and real floor 100 death → exactly one era closure.

## Rollback

Before settlement starts, disable the new warden rules and retain the original pool. After settlement begins, preserve the new damage/reward/era history; pause new boss actions if necessary while deploying a compatible correction. Refunds and compensations require unique receipts, never replayed awards. Do not restore a pre-kill snapshot over completed player progress.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
