# worldd execution — Phase 2: World-day rollover, interest, regen, presents

Parent: [plans/001-worldd](../../001-worldd/plan.md) phase 2.

## Goal

Server truth for time: the world-day rolls lazily and exactly once; interest, regen, presents, and lodge expiry all resolve server-side.

## Deliverables

- `migrations/003_time.sql`: `presents`, lodge fields on players (`lodged_until_day`), `world.last_rollover`, `happenings` table (created here, filled more in phase 3)
- `app/worldday.py` — lazy rollover: on any request, if `now` crossed the world-day boundary (fixed UTC hour) since `world.last_rollover`, take advisory lock, apply the day: vault interest (5%/day compound, credited on visit per economy §7 — accrual marker per account), lodge expiry, PvP allotment reset, presents eligibility (≥20h away), happenings digest row
- `POST /world/tick` — idempotent nudge (also called by the plugin's daily tick)
- Energy/mana lazy regen finalized: computed from `updated_at` timestamps at read time (1⚡/45min, 1✦/90min, caps per level), never stored hot
- Presents roll on `players/ensure`/state read when eligible: gift table from economy §7 (40% gold 50×L / 25% potion / 15% full energy / 10% rumor / 8% repair token / 2% jackpot), luck-charm + halfling modifiers
- Tests: time-travel fixtures (freeze/advance clock), interest paid exactly once across concurrent requests (advisory lock test), presents never double-roll

## Exit gate

Two concurrent `/world/tick` calls across a day boundary apply interest exactly once (test proves it); a player away >20h gets exactly one present; energy shown in `/state` matches hand-computed regen.
