"""022/003 — presence: tiers, the cache law, the peek endpoint.

Roy's rule under test: hot = acted on this floor within 3 minutes,
camped = within the hour, and the cache TTL stays strictly under the
hot window so the number can never be staler than the tier it claims.
"""

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402
from tests.test_multiplayer import create_player  # noqa: E402
from tests.test_world_api import act, enter_floor, make_tenant, signed  # noqa: E402


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def tenant_b(client):
    return await make_tenant(client, "tenant-b")


def _reset_cache():
    social._presence_cache.update(at=None, data=None)


async def _age(pool, player, minutes):
    await pool.execute(
        "UPDATE ascent_players SET updated_at = "
        "now() - make_interval(mins => $2) WHERE player=$1",
        player, minutes)


async def _fresh_presence():
    _reset_cache()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await social._presence(conn)


async def test_ttl_stays_under_the_hot_window():
    assert social.PRESENCE_TTL_S < social.PRESENCE_HOT_MIN * 60


async def test_presence_tiers_hot_camped_gone(client, tenant_a, tenant_b):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Hotto")
    pb = await create_player(client, tenant_b, "tenant-b", "Campa")
    for sec, ten, pl in ((tenant_a, "tenant-a", pa),
                         (tenant_b, "tenant-b", pb)):
        await act(client, sec, ten, pl, option="gate")
        await act(client, sec, ten, pl, option="floor_1")

    # 2 minutes old is HOT; 4 minutes is CAMPED
    await _age(pool, pa, 2)
    await _age(pool, pb, 4)
    pres = await _fresh_presence()
    slot = pres["by_floor"][1]
    assert slot["hot"] >= 1 and slot["camped"] >= 1
    names = [t["name"] for t in pres["torches"].get(1, [])]
    assert "Hotto" in names and "Campa" not in names   # torches are HOT only
    assert all(t["status"] for t in pres["torches"][1])

    # 61 minutes old is nobody
    camped_before = slot["camped"]
    await _age(pool, pb, 61)
    pres = await _fresh_presence()
    assert pres["by_floor"][1]["camped"] == camped_before - 1


async def test_town_idlers_hold_no_floor(client, tenant_a):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Towny")
    await enter_floor(client, tenant_a, "tenant-a", pa, 1)
    pres = await _fresh_presence()
    on_floor = pres["by_floor"].get(1, {}).get("hot", 0)
    # walk back to Roothollow: the doc keeps floor=1 but the body left
    await act(client, tenant_a, "tenant-a", pa, option="town")
    pres = await _fresh_presence()
    assert pres["by_floor"].get(1, {}).get("hot", 0) == on_floor - 1


async def test_injection_reaches_the_gate_list(client, tenant_a, tenant_b):
    pa = await create_player(client, tenant_a, "tenant-a", "Seen")
    pb = await create_player(client, tenant_b, "tenant-b", "Beacon")
    await act(client, tenant_b, "tenant-b", pb, option="gate")
    await act(client, tenant_b, "tenant-b", pb, option="floor_1")
    _reset_cache()
    s = await act(client, tenant_a, "tenant-a", pa, option="gate")
    row = next(o for o in s["options"] if o["id"] == "floor_1")
    assert "hot" in row["hint"]


async def test_presence_endpoint_serves_the_callers_floor(client, tenant_a):
    pa = await create_player(client, tenant_a, "tenant-a", "Peeker")
    await act(client, tenant_a, "tenant-a", pa, option="gate")
    await act(client, tenant_a, "tenant-a", pa, option="floor_1")
    _reset_cache()
    body, headers = signed(tenant_a, "tenant-a", {"player": pa})
    r = await client.post("/v1/presence", content=body, headers=headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["floor"] == 1
    assert d["hot"] >= 1                       # the caller's own torch
    assert d["camped"] >= 0


async def test_presence_endpoint_rejects_unsigned(client):
    # 426 = missing API version header — the auth gate's first refusal
    r = await client.post("/v1/presence", json={"player": "nobody"})
    assert r.status_code in (401, 403, 422, 426)
