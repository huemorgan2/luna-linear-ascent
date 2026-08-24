"""078 Phase 2 — the world snapshot cache.

Everything in doc["_world"] that does not depend on WHO is looking —
the frontier, the boards, the roster, the census, the rooms, the warden —
used to be recomputed inside every act's transaction. This module computes
it at most once per WORLD_TTL_S, process-wide, single-flight:

- A fresh snapshot is served as-is.
- A stale snapshot is served immediately while ONE background coroutine
  rebuilds (stale-while-revalidate — no click ever waits for the rebuild).
- `invalidate()` drops the snapshot entirely for the moments staleness is
  user-visible inside one click (the frontier rising); the next reader
  rebuilds synchronously.

numInstances: 1 (render.yaml) makes this module-level cache the truth —
the same load-bearing assumption `_presence_cache` and `_feed_cache`
already stand on.

Consumers get the SAME nested objects — nobody may mutate a snapshot
(gated by test_078_worldcache.test_acts_do_not_mutate_the_snapshot).
"""

from __future__ import annotations

import asyncio
import json
import os

from .gamepath import ensure_game_importable

ensure_game_importable()

from plugin_linear_ascent.engine import state as pstate  # noqa: E402

# <= 0 disables caching: every reader builds fresh (same code path, no
# staleness) — the test suite runs this way so multi-actor contracts see
# each other's writes immediately.
WORLD_TTL_S = float(os.environ.get("ASCENT_WORLD_TTL_S", "10"))

_cache: dict = {"at": None, "data": None}
_lock = asyncio.Lock()


def invalidate() -> None:
    """The frontier rose (warden fall / milestone boss) — the stale world
    would show a closed floor that is open. Drop it; next reader rebuilds."""
    _cache.update(at=None, data=None)


async def snapshot(conn) -> dict:
    if WORLD_TTL_S <= 0:
        return await _build(conn)
    now = pstate.now()
    at, data = _cache["at"], _cache["data"]
    if data is not None:
        if at is not None and (now - at).total_seconds() < WORLD_TTL_S:
            return data
        _spawn_refresh()               # serve stale, refresh off-request
        return data
    async with _lock:                  # boot / post-invalidate: build now
        if _cache["data"] is not None:
            return _cache["data"]      # a racer built it while we waited
        data = await _build(conn)
        _cache.update(at=pstate.now(), data=data)
        return data


def _spawn_refresh() -> None:
    if _lock.locked():
        return                         # one rebuild is already on its way
    asyncio.create_task(_refresh())


async def _refresh() -> None:
    if _lock.locked():
        return
    async with _lock:
        now = pstate.now()
        at = _cache["at"]
        if at is not None and (now - at).total_seconds() < WORLD_TTL_S:
            return                     # someone else already refreshed
        from . import db
        pool = await db.get_pool()
        async with pool.acquire() as conn:
            data = await _build(conn)
        _cache.update(at=pstate.now(), data=data)


async def _build(conn) -> dict:
    """One pass over the viewer-independent world. Every section keeps the
    exact shape inject_world used to compute inline."""
    from . import factions, social
    day = pstate.world_day()

    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    frontier = int(json.loads(row["value"])) if row else 1

    happ = await conn.fetch(
        "SELECT kind, line, floor FROM ascent_happenings "
        "WHERE world_day >= $1 ORDER BY id DESC LIMIT 20", day - 1)
    happenings = social._condense_war([dict(r) for r in happ])[:5]

    stone = await conn.fetch(
        "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 8")
    # 022/007: the Stone of Eras — permanent, readable in every era.
    eras = await conn.fetch(
        "SELECT era, data FROM ascent_eras ORDER BY era DESC LIMIT 5")
    era_lines = [
        (lambda d: f"ERA {r['era']} — fell on day {d.get('world_day', '?')}"
                   f" to {d.get('finisher', '?')} and "
                   f"{max(0, len(d.get('war_party', [])) - 1)} blades")
        (json.loads(r["data"])) for r in eras]

    roster, roster_count = await social._roster(conn)
    census = await social._census(conn)
    active = int(census.get("total", 0))
    warden = await social._world_warden(conn, frontier, active)
    fallen = await social._fallen_map(conn)
    rooms, rooms_n = await social._rooms(conn)
    fire = await social._long_fire(conn)

    factions_hall = await social._faction_hall(conn)
    factions_total = await conn.fetchval(
        "SELECT count(*) FROM ascent_factions")
    guild_dir = await factions.directory(conn)
    hall_board = await factions.hall_board(conn)

    return {
        "frontier": frontier,
        "happenings": happenings,
        "stone": [r["line"] for r in stone],
        "eras": era_lines,
        "roster": roster, "roster_count": roster_count,
        "census": census,
        "warden": warden, "fallen": fallen,
        "rooms": rooms, "rooms_n": rooms_n,
        "fire": fire,
        "factions_hall": factions_hall,
        "factions_total": int(factions_total or 0),
        "faction_banners": factions.banner_slugs(),
        "guild_dir": guild_dir,
        "hall_board": hall_board,
    }
