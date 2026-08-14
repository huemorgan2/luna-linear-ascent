"""056 — the Playing tab: one write door, one cursor, two scopes.

Rules under test: every feed line walks through add_happening and bumps
the in-process head (the 2s peek never asks Postgres "anything new?");
the world tab is scope='world' only; the faction tab is every row tagged
with MY faction across both scopes, membership checked server-side; no
faction is an answer (the CTA payload), never an error; faction-grain
rows die at 14 days, world rows don't.
"""

import json
import uuid

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402
from tests.test_world_api import make_tenant, signed  # noqa: E402


def _reset_caches():
    social._feed_head["id"] = None
    social._online_cache.update(at=None, n=0)


async def _add(conn, **kw):
    kw.setdefault("kind", "climb")
    kw.setdefault("line", "test line")
    await social.add_happening(conn, **kw)


async def test_add_happening_bumps_the_head(client):
    _reset_caches()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        before = await social.feed_head(conn)
        await _add(conn, line="the head moves")
        bumped = social._feed_head["id"]
        assert bumped > before
        # and the lazy init agrees with the table
        social._feed_head["id"] = None
        assert await social.feed_head(conn) == bumped


async def test_world_tab_is_world_scope_only(client):
    _reset_caches()
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    async with pool.acquire() as conn:
        since = await social.feed_head(conn)
        await _add(conn, line=f"world news {tag}")
        await _add(conn, line=f"faction grain {tag}", scope="faction",
                   faction="The Test Banner")
        out = await social.playing_feed(conn, "t-none", "nobody",
                                        "world", since)
    lines = [r["line"] for r in out["rows"]]
    assert f"world news {tag}" in lines
    assert f"faction grain {tag}" not in lines
    assert out["head"] >= since + 2


async def test_faction_tab_needs_membership_and_merges_scopes(client):
    _reset_caches()
    secret = await make_tenant(client, "t-ply")
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    fac = f"Banner {tag}"
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO ascent_factions (name) VALUES ($1) "
            "ON CONFLICT DO NOTHING", fac)
        await conn.execute(
            "INSERT INTO ascent_faction_members (tenant, player, faction) "
            "VALUES ('t-ply','member-1',$1) ON CONFLICT (tenant, player) "
            "DO UPDATE SET faction=$1", fac)
        since = await social.feed_head(conn)
        await _add(conn, line=f"{tag} world deed", faction=fac)
        await _add(conn, line=f"{tag} floor step", scope="faction",
                   faction=fac)
        await _add(conn, line=f"{tag} stranger", faction="Other Banner",
                   scope="faction")

        # a member sees both scopes of THEIR banner, nothing else
        out = await social.playing_feed(conn, "t-ply", "member-1",
                                        "faction", since)
        lines = [r["line"] for r in out["rows"]]
        assert out["faction"] == fac
        assert f"{tag} world deed" in lines
        assert f"{tag} floor step" in lines
        assert f"{tag} stranger" not in lines

        # no banner is an answer, not an error — the CTA payload
        out = await social.playing_feed(conn, "t-ply", "loner",
                                        "faction", 0)
        assert out == {"ok": True, "faction": None,
                       "head": out["head"], "rows": []}
        assert out["head"] > 0


async def test_presence_carries_the_two_ints(client):
    _reset_caches()
    secret = await make_tenant(client, "t-ply2")
    body, headers = signed(secret, "t-ply2", {"player": "peeker"})
    r = await client.post("/v1/presence", content=body, headers=headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert isinstance(d["online"], int)
    assert isinstance(d["feed_head"], int)


async def test_playing_feed_door(client):
    _reset_caches()
    secret = await make_tenant(client, "t-ply3")
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    async with pool.acquire() as conn:
        since = await social.feed_head(conn)
        await _add(conn, line=f"door test {tag}")
    body, headers = signed(secret, "t-ply3", {
        "player": "walker", "scope": "world", "since": since})
    r = await client.post("/v1/playing_feed", content=body, headers=headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["ok"] and d["faction"] is None
    assert f"door test {tag}" in [row["line"] for row in d["rows"]]


async def test_online_counts_the_window(client):
    _reset_caches()
    pool = await db.get_pool()
    # a real doc, not a stub — the roster scans every playing player,
    # so a bare {"stage": "playing"} row would poison the whole suite
    doc = json.dumps({"stage": "playing", "name": "OnlineTest", "level": 1,
                      "gear": {}, "floor": 1, "gold": 0, "xp": 0})
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO ascent_tenants (tenant, secret) "
            "VALUES ('t-online','test-secret') ON CONFLICT DO NOTHING")
        try:
            await conn.execute(
                "INSERT INTO ascent_players (tenant, player, doc) "
                "VALUES ('t-online','fresh',$1::jsonb) "
                "ON CONFLICT (tenant, player) DO UPDATE SET doc=$1::jsonb, "
                "updated_at=now()", doc)
            await conn.execute(
                "INSERT INTO ascent_players (tenant, player, doc) "
                "VALUES ('t-online','stale',$1::jsonb) "
                "ON CONFLICT (tenant, player) DO UPDATE SET doc=$1::jsonb, "
                "updated_at=now() - make_interval(mins => $2)",
                doc, social.ONLINE_WINDOW_MIN + 1)
            n = await social.online_count(conn)
            assert n >= 1
            # the 30s cache holds: a call inside the TTL is the cache
            await conn.execute(
                "UPDATE ascent_players SET updated_at=now() "
                "WHERE tenant='t-online' AND player='stale'")
            assert await social.online_count(conn) == n
        finally:
            await conn.execute(
                "DELETE FROM ascent_players WHERE tenant='t-online'")


async def test_faction_grain_dies_at_fourteen_days_world_rows_stay(client):
    _reset_caches()
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    async with pool.acquire() as conn:
        await _add(conn, line=f"old world {tag}")
        await _add(conn, line=f"old grain {tag}", scope="faction",
                   faction="Sweep Banner")
        await conn.execute(
            "UPDATE ascent_happenings SET created_at = "
            "now() - interval '15 days' WHERE line LIKE $1", f"old %{tag}")
        # force the day-lock to fire regardless of prior test runs
        await conn.execute(
            "DELETE FROM ascent_world WHERE key='feed_sweep_day'")
        await social.maybe_sweep_feed(conn)
        rows = await conn.fetch(
            "SELECT line FROM ascent_happenings WHERE line LIKE $1",
            f"old %{tag}")
    lines = [r["line"] for r in rows]
    assert f"old world {tag}" in lines
    assert f"old grain {tag}" not in lines
