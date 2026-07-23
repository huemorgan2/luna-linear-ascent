# Plan 001 — worldd: the shared Linear Ascent world

Authoritative multiplayer backend for [plugin-linear-ascent](https://github.com/huemorgan2/plugin-linear-ascent). Every Luna tenant running the plugin is a thin client of one world hosted here. Companion to the plugin's `plans/002-full-game/plan.md` (workstream F) and `plans/001-buildfirst` phase 3.

## Why a service

- **One world:** the frontier, milestone-Warden quorums, PvP, letters, grants, and the Stone of the Climb only mean something if all players share them.
- **Server truth for time:** Luna agents have no clock and turns die with their SSE stream. worldd owns the world-day, interest, regen, fade, and offline PvP resolution; the plugin only ever reads server-computed ages/countdowns and reports what already happened.
- **Anti-cheat:** clients send *intents* (fight, deposit, attack player); worldd rolls the dice, applies economy formulas, and returns the outcome. A tenant can never post a result.

## Stack

FastAPI + asyncpg + Postgres 16, deployed from the root `render.yaml`:
one **starter** web service (lowest paid plan, always-on) + one **starter** Postgres, region oregon, `numInstances: 1`. No Redis, no workers, no cron add-ons — everything in-process, which `numInstances: 1` makes safe.

## Auth

Two layers, same pattern as luna-whatsapp:

- **Tenant auth:** each Luna install registers via `/admin/tenants` (guarded by `ASCENT_ADMIN_KEY`) and gets a tenant id + secret. Every plugin request is HMAC-signed (`X-Ascent-Tenant`, `X-Ascent-Signature` over timestamp+body, ±300s window) with `ASCENT_SHARED_SECRET` as the bootstrap secret for the first tenant.
- **Player scoping:** the plugin passes its stable Luna user id; worldd maps (tenant, luna_user) → player. Tenants can only act as their own players.

API versioned with `X-Ascent-Api: 1`; plugin and service bump it together.

## Schema (v1)

`tenants`, `players` (stats, floor, energy/mana snapshots + `updated_at` for lazy regen), `vault_accounts` (balance, last_interest_day), `ledger` (append-only gold/xp deltas, idempotency key), `inventories`, `world` (singleton: world_day, frontier_floor), `floor_progress` (per-player), `boss_commits` (player, boss, committed_at — quorum resolution), `pvp_attacks`, `letters`, `grants`, `presents`, `guilds` + `guild_members`, `happenings` (daily feed), `kills` (Stone of the Climb).

All money/XP mutations go through `ledger` with a client idempotency key — retried turns must not double-pay.

## Time model

No background scheduler. On any request, worldd lazily rolls forward: if `now` crosses a world-day boundary since `world.last_rollover`, take a Postgres advisory lock and apply the day (interest, energy/mana reset, fade checks, presents, happenings digest). Single instance + advisory lock = exactly-once. A Render cron-less fallback: the plugin's daily scheduler tick also calls `/world/tick`, so a quiet day still rolls.

## Endpoints (mirror of the plugin's `StateBackend` seam)

| Group | Endpoints |
|---|---|
| health | `GET /health` (ok, api, server_time) |
| admin | `POST /admin/tenants`, `GET /admin/world` |
| player | `POST /players/ensure`, `GET /players/{id}/state` (includes server-computed energy/mana, countdowns, pending events) |
| actions | `POST /actions/fight`, `/actions/deposit`, `/actions/withdraw`, `/actions/buy`, `/actions/sleep`, `/actions/heal`, `/actions/climb` |
| boss | `POST /boss/commit`, `GET /boss/{floor}/status` (quorum count, window) |
| pvp | `GET /pvp/targets`, `POST /pvp/attack` (offline defense resolved server-side) |
| social | `POST /letters`, `GET /letters/inbox`, `POST /grants`, `GET /happenings/today`, `GET /stone` |
| guilds | `POST /guilds`, `POST /guilds/{id}/join`, `GET /guilds/{id}` |
| world | `POST /world/tick` (idempotent rollover nudge) |

Request/response bodies are the plugin's `StateBackend` dataclasses serialized 1:1 — the local backend and this HTTP client stay drop-in interchangeable, and the plugin's phase-1 test suite runs against both.

## Phases

| # | Scope | Exit gate |
|---|---|---|
| 0 | Scaffold (done): /health, render.yaml blueprint deploys green | Render URL returns ok |
| 1 | Schema migrations + tenant HMAC auth + players/actions/ledger | plugin's StateBackend contract tests pass against a deployed instance |
| 2 | World-day rollover (advisory lock), vault interest, regen, presents | two tenants see the same world_day; interest paid exactly once |
| 3 | Social: letters, grants, happenings, Stone; PvP with offline defense | 3-account drama scenario (plugin plan 002 step 4) passes cross-tenant |
| 4 | Boss quorum commits + guilds; frontier advance | async Gnarl clear by 3 accounts on 2 tenants |
| 5 | Hardening: rate limits per tenant, ledger audit view, backup/restore drill, `X-Ascent-Api` bump policy | soak week with dojo agents; restore from backup rehearsed |

## Ops notes

- Cost: 1× starter web + 1× starter Postgres — the floor for an always-on paid setup.
- Migrations: plain SQL files in `worldd/migrations/`, applied at startup under the advisory lock (single instance makes this safe).
- Logs are the debug surface; no admin UI in v1 beyond `GET /admin/world`.
- Secrets only in the Render dashboard (`sync: false`) — never in git.
