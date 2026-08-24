"""078 Phase 2 — the world snapshot cache.

Laws under test: one rebuild per expiry however many readers race
(single-flight), a fresh snapshot is served without touching Postgres,
invalidation forces a synchronous rebuild, inject_world carries the
snapshot's sections plus live viewer-dependent ones, fight rounds skip
the social reads their card cannot render, and no act may mutate the
shared snapshot.
"""

import asyncio
import copy
import json

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social, worldcache  # noqa: E402
from tests.test_multiplayer import create_player  # noqa: E402
from tests.test_world_api import act, make_tenant  # noqa: E402


@pytest.fixture(autouse=True)
def _cache_on(monkeypatch):
    """The suite at large runs with the cache off (conftest sets TTL 0);
    these tests ARE the cache, so pin the production TTL here."""
    monkeypatch.setattr(worldcache, "WORLD_TTL_S", 10.0)
    worldcache.invalidate()
    yield
    worldcache.invalidate()


def _reset():
    worldcache.invalidate()


async def test_single_flight_one_build_for_many_racers(client, monkeypatch):
    _reset()
    calls = {"n": 0}
    real = worldcache._build

    async def counting(conn):
        calls["n"] += 1
        await asyncio.sleep(0.05)      # widen the race window
        return await real(conn)

    monkeypatch.setattr(worldcache, "_build", counting)
    pool = await db.get_pool()

    async def one():
        async with pool.acquire() as conn:
            return await worldcache.snapshot(conn)

    snaps = await asyncio.gather(one(), one(), one(), one())
    assert calls["n"] == 1
    assert all(s is snaps[0] for s in snaps)
    _reset()


async def test_fresh_snapshot_serves_without_rebuild(client, monkeypatch):
    _reset()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        first = await worldcache.snapshot(conn)

    async def boom(conn):
        raise AssertionError("a fresh snapshot must not rebuild")

    monkeypatch.setattr(worldcache, "_build", boom)
    async with pool.acquire() as conn:
        again = await worldcache.snapshot(conn)
    assert again is first
    _reset()


async def test_invalidate_forces_synchronous_rebuild(client):
    _reset()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        first = await worldcache.snapshot(conn)
        worldcache.invalidate()
        second = await worldcache.snapshot(conn)
    assert second is not first
    assert second["frontier"] >= 1
    _reset()


async def test_inject_world_rides_the_snapshot(client):
    _reset()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        snap = await worldcache.snapshot(conn)
        row = await conn.fetchrow(
            "SELECT tenant, player, doc FROM ascent_players "
            "WHERE stage='playing' ORDER BY updated_at DESC LIMIT 1")
        assert row, "need at least one playing player in the test world"
        doc = json.loads(row["doc"])
        await social.inject_world(conn, row["tenant"], row["player"], doc)
    w = doc["_world"]
    assert w["roster"] is snap["roster"]
    assert w["rooms"] is snap["rooms"]
    assert w["census"] is snap["census"]
    assert w["frontier"] == snap["frontier"]
    # live viewer-dependent sections still present
    for key in ("letters", "names", "pvp_targets", "grant_targets",
                "presence", "inbox_count"):
        assert key in w
    _reset()


async def test_fight_rounds_skip_the_social_reads(client):
    _reset()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT tenant, player, doc FROM ascent_players "
            "WHERE stage='playing' ORDER BY updated_at DESC LIMIT 1")
        doc = json.loads(row["doc"])
        # a fight round only exists inside an encounter — outside one,
        # "attack_<Name>" is a PvP initiation and gets the full injection
        doc["encounter"] = {"kind": "monster", "slug": "wolf", "hp": 5}
        await social.inject_world(conn, row["tenant"], row["player"], doc,
                                  option="attack")
    w = doc["_world"]
    assert w["letters"] == [] and w["names"] == []
    assert w["pvp_targets"] == [] and w["grant_targets"] == []
    assert w["profiles"] == {}
    # the world itself still rides in — the fight card needs the warden,
    # the census-backed quorums, the frontier
    assert "census" in w and "frontier" in w
    _reset()


async def test_acts_do_not_mutate_the_snapshot(client):
    """The snapshot's nested objects are shared by reference across every
    act — one engine mutation would poison every later click. Play real
    acts and hold the snapshot to its pre-act deep copy."""
    _reset()
    sec = await make_tenant(client, "tenant-cache")
    p = await create_player(client, sec, "tenant-cache", "Cachet")
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        snap = await worldcache.snapshot(conn)
    frozen = copy.deepcopy(snap)
    for option in ("gate", "floor_1", "hunt", "town"):
        await act(client, sec, "tenant-cache", p, option=option)
    # whatever the acts did, the object we hold equals its deep copy —
    # nobody wrote through the shared reference
    assert snap == frozen
    _reset()
