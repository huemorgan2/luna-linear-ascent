# worldd execution — Phase 4: Boss quorum commits, guilds, frontier advance

Parent: [plans/001-worldd](../../001-worldd/plan.md) phase 4.

## Goal

Group play: milestone Wardens fall to async quorums; guilds exist; the frontier advances for everyone.

## Deliverables

- `migrations/005_guilds.sql`: `guilds`, `guild_members`, `boss_commits` (player, floor, committed_at, energy escrow)
- `app/guilds.py` — `POST /guilds` (found), `POST /guilds/{id}/join`, `/leave`, `GET /guilds/{id}` (roster, board)
- `app/boss.py` — `POST /boss/commit` (5⚡ escrow, 24h window, one commit per player per window), `GET /boss/{floor}/status` (quorum count, committed names, server-computed window countdown text); resolution when quorum met (or window lapses → refund): server-side fight vs milestone Warden stats (economy §5), per-participant payouts via ledger, `kills` + happenings broadcast, names on Stone, `world.frontier_floor` advance — the floor opens for every tenant
- Regular (non-milestone) Warden first-kill also advances/opens floors (`floor_progress` + world first-clear record)
- Quorum sizes from economy §5, configurable via `world` row for small launch populations
- Tests: quorum resolution exactly-once under concurrent commits, window lapse refunds, frontier visibility to a non-participant

## Exit gate

Async Gnarl (floor 10) clear: 3 players commit across 2 tenants within the window → resolution fires once, all 3 get 4,000 XP / 5,000g ledger rows, a 4th player who never fought sees floor 11 open and the names on the Stone.
