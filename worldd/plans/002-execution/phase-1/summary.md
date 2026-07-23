# worldd Phase 1 — execution summary

Status: **complete** (integration-tested against local Postgres).

## Built

- Schema (`migrations/002_world.sql`): `ascent_tenants`, `ascent_players` (tenant+player → JSONB doc), `ascent_ledger` (append-only), `ascent_idempotency`, `ascent_world` (shared frontier).
- HMAC tenant auth (`app/auth.py`): `X-Ascent-Tenant/Ts/Signature/Api`, signature = HMAC-SHA256(secret, `{ts}.{body}`), ±300s skew, constant-time compare, 60s secret cache, 426 on wrong API version.
- Admin API (`X-Admin-Key`): `POST/GET /admin/tenants` (secret generated server-side, returned once), `GET /admin/world` (frontier, player count, ledger totals).
- Game API: `POST /v1/scene`, `/v1/act` (option/text/idem), `/v1/character`.
- **Architecture decision:** worldd runs the *same engine* the plugin ships (`plugin_linear_ascent.engine` — Luna-free by construction, imported via `app/gamepath.py`: env `ASCENT_GAME_PATH` → `vendor/` → sibling checkout). One source of game truth; no reimplementation drift.
- Concurrency: `SELECT … FOR UPDATE` per player row serializes turns; idempotency rows replay identical responses for retried mutations.

## Verified (7 tests)

Unsigned/bad-signature/stale-timestamp rejection; full creation flow over signed HTTP; idempotent act replay (state advances exactly once); world frontier inherited across tenants; identical player ids isolated per tenant.
