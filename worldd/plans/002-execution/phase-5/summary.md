# worldd Phase 5 — execution summary (hardening + Render deploy)

Status: **complete — LIVE in production.**

## Hardening

- Per-tenant token-bucket rate limit (30 burst / 5 req/s sustained, env-tunable via `ASCENT_RATE_CAPACITY` / `ASCENT_RATE_REFILL`; in-process is safe because `numInstances: 1`). Returns 429 on `/v1/*`.
- Structured request log middleware: one line per request (tenant, method, path, status, ms).
- Ledger audit: `GET /admin/ledger?tenant=&player=&limit=` (admin-key guarded).
- API version pinning already enforced at auth (426 on mismatched `X-Ascent-Api`).
- Game engine vendored into `worldd/vendor/` (`tools/vendor_game.sh`) so the Render build never depends on submodule cloning.

## Deploy (via Render REST API — the dashboard needed an interactive GitHub login, the configured API key did not)

- `ascent-world-db`: Postgres 16, basic_256mb, oregon — `dpg-d9ha2okvikkc73ff4pqg-a`.
- `ascent-worldd`: web service, **starter plan ($7/mo, always-on)**, oregon, Python 3.12, health check `/health` — `srv-d9ha3csvikkc73ff5rg0`, https://ascent-worldd.onrender.com.
- Secrets (`ASCENT_SHARED_SECRET`, `ASCENT_ADMIN_KEY`) set as service env vars only — never in git. Local copy kept out of the repo.
- One build failure on the way: a bogus `pyyaml==0.30.0` pin (fixed to 6.0.3). Note: Render has no webhook access to the repo (public clone only), so deploys must be triggered via `POST /v1/services/{id}/deploys` after each push.

## Exit gate — all green

- `GET /health` → `{"ok":true,"api":1,"db":true}` with migrations applied at boot.
- Production tenant `roy-local` registered via `/admin/tenants`.
- A real fight played from local against production (creation → gate → floor 1 → grey wolf → attack) landed a ledger row (`kind=energy, note=wilds`) visible via `/admin/ledger`.
- Local Luna's chat UI pointed at production: Luna re-created the character against the fresh world and returned to town — `/admin/world` shows 2 players.
