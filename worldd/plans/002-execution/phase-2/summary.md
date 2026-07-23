# worldd Phase 2 — execution summary

Status: **complete**, with a deliberate design simplification.

## Design note: no rollover job

The plan called for a world-day rollover worker (interest, regen, presents). The engine computes all of these **lazily from server timestamps** (meter regen from `energy_ts`/`mana_ts`, vault interest from `bank_day` on visit, presents from `last_seen` ≥20h) — so a scheduled job would only duplicate math that already happens deterministically at read time. worldd therefore ships **no cron**: world-day is a pure function of UTC time (`state.world_day`), per-day counters reset lazily via `touch_daily`, and there is nothing to miss or double-run. The advisory-lock rollover slot remains in `db.py` if a future feature (e.g. lodge eviction news) needs a true tick.

## What phase 2 delivered instead

- Shared frontier: `ascent_world['frontier']`, synced into each doc before the engine runs, raised transactionally on warden/boss unlocks.
- Presents/interest/regen verified through the HTTP surface (same engine paths already unit-tested in the plugin suite).

## Verified

Frontier inheritance across tenants (`test_frontier_is_shared_across_tenants`); daily caps and interest via plugin unit tests (shared engine).
