# Phase 0 — Scaffold verification: COMPLETE

Date: 2026-07-23

## What was built

- `app/` restructured: `config.py` (env config, test-resettable), `db.py`
  (asyncpg pool + plain-SQL migration runner under advisory lock
  `0x00A5CE47`), `main.py` (FastAPI lifespan wiring, `/health` contract kept:
  `ok/api/server_time/db`).
- `migrations/001_init.sql` — bootstrap file so the migration pipeline is
  exercised from first boot; `schema_migrations` table tracks applied files.
- `requirements.txt` pinned (fastapi 0.116.1, uvicorn 0.35.0, asyncpg 0.30.0)
  + `requirements-dev.txt` (pytest, pytest-asyncio, httpx).
- Test harness: `tests/conftest.py` (ASGI client against the real local DB),
  `tests/test_health.py`.
- Dev database: docker container `ascent-postgres` (postgres:16) on port
  **5434** (5433 was taken by luna-postgres), db `ascent_world`, user/pass
  `ascent`/`ascent`.
- Local venv: **Python 3.12** (`worldd/.venv`) — system 3.9 too old.

## Verification

- `pytest -q` → 1 passed (health returns `ok: true, api: 1, db: true`;
  migration runner applied 001 on startup).
- Real browser on `http://localhost:8600/health` →
  `{"ok":true,"api":1,"server_time":"2026-07-23T20:52:10Z","db":true}`. ✓

## Notes / deviations

- None. `/health` contract unchanged from the original scaffold.
- worldd runs in background on port 8600 for the rest of the execution.
