# worldd execution — Phase 1: Schema, tenant HMAC auth, players/actions/ledger

Parent: [plans/001-worldd](../../001-worldd/plan.md) phase 1.

## Goal

The core authoritative API: tenants authenticate with HMAC, players exist server-side, every action resolves server-side through the ledger.

## Deliverables

- `migrations/002_core.sql`: `tenants`, `players` (stats, floor, energy/mana snapshots + `updated_at`), `vault_accounts`, `ledger` (append-only, idempotency key UNIQUE), `inventories`, `world` (singleton), `floor_progress`
- `app/auth.py` — HMAC middleware: `X-Ascent-Tenant`, `X-Ascent-Signature` = HMAC-SHA256(secret, f"{ts}.{body}"), `X-Ascent-Ts` ±300s window; bootstrap tenant from `ASCENT_SHARED_SECRET`; `X-Ascent-Api: 1` check
- `app/admin.py` — `POST /admin/tenants` (guarded by `ASCENT_ADMIN_KEY`), `GET /admin/world`
- `app/players.py` — `POST /players/ensure` ((tenant, luna_user) → player, race/class/name), `GET /players/{id}/state` (server-computed energy/mana from timestamps, pending events)
- `app/actions.py` — `POST /actions/fight`, `/deposit`, `/withdraw`, `/buy`, `/sleep`, `/heal`, `/climb` — all mutations via ledger rows with client idempotency keys; combat resolved server-side with server RNG (seeded per player+day)
- `app/economy.py` — the formulas from `vision/economy.md` (monster stats 4F+2/3F/12F+25, XP 12F, gold 8F, need(L)=60·L^1.5, fade rule, gear tables, potion effects)
- Contract tests: same test file shape the plugin uses for its `StateBackend` (kept in sync)

## Steps

1. Write migration; apply locally.
2. Auth middleware + tests (valid sig, bad sig, stale ts, wrong tenant).
3. Economy module: pure functions, unit-tested against the economy.md sample table rows.
4. Players + actions endpoints; every gold/XP delta a ledger row; retry with same idempotency key returns the stored outcome.
5. `curl` smoke: register tenant, ensure player, fight, deposit — verify ledger.

## Exit gate

pytest green including idempotency replay tests; a signed `curl` round-trip (ensure → fight → state) works against localhost; economy functions match the sample tables in `vision/economy.md` §4 exactly.
