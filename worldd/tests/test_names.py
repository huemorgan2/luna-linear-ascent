"""004 — one name, one world.

The climber's name IS their username: one word, unique across every tenant
and the site's door alike. worldd is the only judge of that, so these tests
go through the real doors — /v1/act for the gate, /signup for the site.
"""

import uuid

import pytest

from app import db, names
from tests.test_world_api import act, make_tenant, scene


def uniq(stem: str = "Nam") -> str:
    return f"{stem}{uuid.uuid4().hex[:8]}"


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def tenant_b(client):
    return await make_tenant(client, "tenant-b")


async def at_the_registrar(client, secret, tenant):
    """A fresh climber, race and class picked, waiting to be named."""
    player = f"p-{uuid.uuid4().hex[:8]}"
    await scene(client, secret, tenant, player)
    for _ in range(9):
        await act(client, secret, tenant, player, option="next")
    await act(client, secret, tenant, player, option="begin")
    await act(client, secret, tenant, player, option="human")
    await act(client, secret, tenant, player, option="warrior")
    return player


async def doc_of(tenant: str, player: str) -> dict:
    import json
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player)
    return json.loads(row["doc"])


# ── the registry ─────────────────────────────────────────────────────────

async def test_claim_is_created_then_mine_then_taken(client):
    pool = await db.get_pool()
    name = uniq("Fleet")
    async with pool.acquire() as conn:
        assert await names.claim(conn, name, names.CLIMBER, "tenant-a",
                                 "p-1") == names.CREATED
        # the same hands again: a retry, or the next era after a reset
        assert await names.claim(conn, name, names.CLIMBER, "tenant-a",
                                 "p-1") == names.MINE
        # anyone else, any casing
        assert await names.claim(conn, name.lower(), names.CLIMBER,
                                 "tenant-b", "p-2") == names.TAKEN
        assert await names.claim(conn, name.upper(), names.CLIMBER,
                                 "tenant-a", "p-3") == names.TAKEN


async def test_release_puts_a_name_back(client):
    pool = await db.get_pool()
    name = uniq("Give")
    async with pool.acquire() as conn:
        await names.claim(conn, name, names.CLIMBER, "tenant-a", "p-1")
        await names.release(conn, name, "tenant-a", "p-1")
        assert await names.holder(conn, name) is None


async def test_the_door_and_the_gate_share_one_namespace(client):
    """Both directions: an account's name is closed to climbers, and a
    climber's name is closed at the door."""
    pool = await db.get_pool()
    door_name, gate_name = uniq("Door"), uniq("Gate")
    r = await client.post("/signup", json={"username": door_name,
                                           "password": "hunter2",
                                           "password2": "hunter2"})
    assert r.status_code == 200
    async with pool.acquire() as conn:
        assert await names.claim(conn, door_name, names.CLIMBER,
                                 "tenant-a", "p-9") == names.TAKEN
        await names.claim(conn, gate_name, names.CLIMBER, "tenant-a", "p-9")
    r = await client.post("/signup", json={"username": gate_name,
                                           "password": "hunter2",
                                           "password2": "hunter2"})
    assert r.status_code == 409
    # and the refused signup left no account behind
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_accounts WHERE lower(username)=lower($1)",
        gate_name) == 0


async def test_the_registry_outlives_the_era(client):
    from app import era
    assert "ascent_names" in era.PERMANENT_TABLES
    assert "ascent_names" not in era.TRANSIENT_TABLES


# ── the gate, through /v1/act ────────────────────────────────────────────

async def test_the_gate_claims_the_name_it_carves(client, tenant_a):
    name = uniq("Carve")
    player = await at_the_registrar(client, tenant_a, "tenant-a")
    s = await act(client, tenant_a, "tenant-a", player, text=name)
    assert name in s["headline"]
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        held = await names.holder(conn, name)
    assert held["kind"] == names.CLIMBER
    assert (held["tenant"], held["player"]) == ("tenant-a", player)


async def test_a_second_tenant_cannot_take_the_same_name(client, tenant_a,
                                                         tenant_b):
    """The whole point of the service: one world, so one Fleet."""
    name = uniq("Fleet")
    first = await at_the_registrar(client, tenant_a, "tenant-a")
    await act(client, tenant_a, "tenant-a", first, text=name)

    second = await at_the_registrar(client, tenant_b, "tenant-b")
    s = await act(client, tenant_b, "tenant-b", second, text=name)
    assert "already climbs" in s["shard_note"]
    assert (await doc_of("tenant-b", second))["stage"] == "creation_name"
    # and the second climber gets in under a name of their own
    other = uniq("Fleets")
    s = await act(client, tenant_b, "tenant-b", second, text=other)
    assert other in s["headline"]
    assert (await doc_of("tenant-b", second))["stage"] == "playing"


async def test_two_words_at_the_gate_become_one_name(client, tenant_a):
    stem = uniq("Master")
    player = await at_the_registrar(client, tenant_a, "tenant-a")
    s = await act(client, tenant_a, "tenant-a", player,
                  text=f"{stem} Chief")
    assert f"{stem}Chief" in s["headline"]
    assert (await doc_of("tenant-a", player))["name"] == f"{stem}Chief"


async def test_a_name_the_engine_refuses_is_not_left_reserved(client,
                                                              tenant_a):
    """The registrar claims before the engine runs, so a refusal has to
    give the row back — otherwise a typo would eat a name forever."""
    player = await at_the_registrar(client, tenant_a, "tenant-a")
    taken_by_nobody = uniq("Short")
    await act(client, tenant_a, "tenant-a", player, text="x")   # too short
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        assert await names.holder(conn, "x") is None
        # and a legal name refused for any other reason is released too
        await names.claim(conn, taken_by_nobody, names.CLIMBER,
                          "tenant-a", player)
        await names.release(conn, taken_by_nobody, "tenant-a", player)
        assert await names.holder(conn, taken_by_nobody) is None


async def test_an_imported_character_takes_the_nearest_free_name(client,
                                                                 tenant_a):
    """An offline character cannot be sent back to the gate to pick again."""
    pool = await db.get_pool()
    name = uniq("Import")
    async with pool.acquire() as conn:
        await names.claim(conn, name, names.CLIMBER, "tenant-b", "p-other")
        got = await names.claim_free(conn, name, "tenant-a", "p-mine")
    assert got == f"{name[:23]}2"
