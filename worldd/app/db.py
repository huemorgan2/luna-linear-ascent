"""asyncpg pool + plain-SQL migration runner.

Migrations are files in worldd/migrations/*.sql applied in filename order,
tracked in a `schema_migrations` table, under a Postgres advisory lock so a
restarting single instance (or a race) applies each exactly once.
"""

from __future__ import annotations

import logging
import os

import asyncpg

log = logging.getLogger("worldd.db")

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")
# Fixed app-wide advisory lock ids (arbitrary but stable).
MIGRATION_LOCK = 0x00A5CE47
ROLLOVER_LOCK = 0x00A5CE48

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    assert _pool is not None, "db not initialized — call init_db() first"
    return _pool


async def init_db(database_url: str) -> None:
    global _pool
    if not database_url:
        log.warning("DATABASE_URL empty — running without a database")
        return
    _pool = await asyncpg.create_pool(database_url, min_size=1, max_size=10)
    await run_migrations()


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def ready() -> bool:
    return _pool is not None


async def run_migrations() -> None:
    pool = await get_pool()
    files = sorted(
        f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".sql"))
    async with pool.acquire() as conn:
        await conn.execute("SELECT pg_advisory_lock($1)", MIGRATION_LOCK)
        try:
            await conn.execute(
                """CREATE TABLE IF NOT EXISTS schema_migrations (
                       filename text PRIMARY KEY,
                       applied_at timestamptz NOT NULL DEFAULT now())""")
            applied = {
                r["filename"] for r in
                await conn.fetch("SELECT filename FROM schema_migrations")}
            for fname in files:
                if fname in applied:
                    continue
                sql = open(os.path.join(MIGRATIONS_DIR, fname)).read()
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES ($1)",
                        fname)
                log.info("migration applied: %s", fname)
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1)", MIGRATION_LOCK)
