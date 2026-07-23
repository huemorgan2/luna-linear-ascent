# worldd execution — Phase 0: Scaffold verification

Parent: [plans/001-worldd](../../001-worldd/plan.md) phase 0. Status at plan time: `app/main.py` scaffold exists (`/health` only), `render.yaml` blueprint written, nothing deployed.

## Goal

A runnable local worldd with project structure ready for the real API: config, db layer, migrations runner, test harness.

## Deliverables

- `worldd/app/__init__.py`, `app/main.py` (FastAPI app factory), `app/config.py` (env: `DATABASE_URL`, `ASCENT_SHARED_SECRET`, `ASCENT_ADMIN_KEY`, world-day hour)
- `worldd/app/db.py` — asyncpg pool, startup/shutdown hooks, migration runner (plain SQL files from `migrations/`, applied in order under advisory lock)
- `worldd/migrations/001_init.sql` — empty-but-real migrations table bootstrap
- `worldd/requirements.txt` pinned (fastapi, uvicorn, asyncpg)
- `worldd/tests/` — pytest + httpx AsyncClient harness; test: `/health` returns ok with `api: 1`, `db: true/false`
- Local Postgres for dev (docker container `ascent-postgres` on port 5433, db `ascent_world`)

## Steps

1. Restructure `app/` into config/db/main modules; keep `/health` contract exactly (`ok`, `api`, `server_time`, `db`).
2. Migration runner: `migrations` table (filename, applied_at), advisory lock id fixed constant, apply missing files in filename order at startup.
3. Docker: `docker run -d --name ascent-postgres -e POSTGRES_USER=ascent -e POSTGRES_PASSWORD=ascent -e POSTGRES_DB=ascent_world -p 5433:5432 postgres:16`.
4. Run `uvicorn app.main:app --port 8600`, hit `/health`.

## Exit gate (browser-verifiable)

`http://localhost:8600/health` in a real browser shows `"ok": true, "db": true`; pytest green.
