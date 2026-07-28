"""007 — one shared Warden per floor, world news, character import."""

import json
import uuid

import pytest

from app import db
from tests.test_world_api import act, make_tenant, scene, signed


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def tenant_b(client):
    return await make_tenant(client, "tenant-b")


@pytest.fixture
async def clean_world(client):
    """Frontier at 1, no live warden state — and restore afterwards."""
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")
    await pool.execute("DELETE FROM ascent_world WHERE key LIKE 'warden:%'")
    yield
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")
    await pool.execute("DELETE FROM ascent_world WHERE key LIKE 'warden:%'")


async def create_player(client, secret, tenant, name):
    player = f"p-{uuid.uuid4().hex[:8]}"
    await scene(client, secret, tenant, player)
    for _ in range(9):                                # 016: through the movie
        await act(client, secret, tenant, player, option="next")
    await act(client, secret, tenant, player, option="begin")
    await act(client, secret, tenant, player, option="human")
    await act(client, secret, tenant, player, option="warrior")
    await act(client, secret, tenant, player, text=name)
    return player


async def test_shared_warden_one_hp_pool_kill_opens_for_all(
        client, tenant_a, tenant_b, clean_world):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")

    # A walks to the floor-1 keep: the SHARED warden, one pool for all
    await act(client, tenant_a, "tenant-a", pa, option="gate")
    await act(client, tenant_a, "tenant-a", pa, option="floor_1")
    s = await act(client, tenant_a, "tenant-a", pa, option="keep")
    assert "whole world" in s["support"]
    assert any(o["id"] == "strike" for o in s["options"])

    # 022/001: the strike opens a REAL fight against the world's body
    s = await act(client, tenant_a, "tenant-a", pa, option="strike")
    ids = {o["id"] for o in s["options"]}
    assert "attack" in ids or "close_in" in ids
    if "close_in" in ids:
        await act(client, tenant_a, "tenant-a", pa, option="close_in")
    await act(client, tenant_a, "tenant-a", pa, option="attack")
    # break away — the fight's total lands as ONE effect when A gets out
    v = None
    for _ in range(20):
        await pool.execute(
            "UPDATE ascent_players SET doc = jsonb_set(doc, '{hp}',"
            " '999'::jsonb) WHERE tenant='tenant-a' AND player=$1", pa)
        s = await act(client, tenant_a, "tenant-a", pa, option="run")
        row = await pool.fetchrow(
            "SELECT value FROM ascent_world WHERE key='warden:1'")
        if row and json.loads(row["value"]).get("strikers"):
            v = json.loads(row["value"])
            break
    assert v, "fleeing must persist the wounds to the world pool"
    assert v["strikers"][0]["name"] == "Aldo" and v["strikers"][0]["dmg"] > 0

    # B sees the SAME wounded warden, with A's name on it
    await act(client, tenant_b, "tenant-b", pb, option="gate")
    await act(client, tenant_b, "tenant-b", pb, option="floor_1")
    s = await act(client, tenant_b, "tenant-b", pb, option="keep")
    assert "Aldo" in " ".join(s["body_lines"])
    assert f"{v['hp']:,}" in s["headline"]

    # test lever: leave it at 1 HP — B lands the killing blow in a fight
    v["hp"] = 1
    await pool.execute(
        "UPDATE ascent_world SET value=$1::jsonb WHERE key='warden:1'",
        json.dumps(v))
    s = await act(client, tenant_b, "tenant-b", pb, option="strike")
    if any(o["id"] == "close_in" for o in s["options"]):
        await act(client, tenant_b, "tenant-b", pb, option="close_in")
    s = await act(client, tenant_b, "tenant-b", pb, option="attack")
    assert "collapses" in s["headline"]

    row = await pool.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    assert int(json.loads(row["value"])) == 2

    # B's next scene: the fall report, with the finisher's loot
    s = await scene(client, tenant_b, "tenant-b", pb)
    assert "has fallen" in s["headline"]
    assert any("killing blow" in l for l in s["body_lines"])
    # A gets the report too — pushed into their doc, no action needed
    s = await scene(client, tenant_a, "tenant-a", pa)
    assert "has fallen" in s["headline"]
    assert any("share of the kill" in l for l in s["body_lines"])
    # and the floor is open for A as well
    await act(client, tenant_a, "tenant-a", pa, option="town")
    s = await act(client, tenant_a, "tenant-a", pa, option="gate")
    assert any("Floor 2" in o["label"] for o in s["options"])
    # the Stone remembers both blades
    row = await pool.fetchrow(
        "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 1")
    assert "Aldo" in row["line"] and "Brai" in row["line"]


async def test_below_frontier_keep_is_solo_echo(client, tenant_a,
                                                clean_world):
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_world SET value='3'::jsonb WHERE key='frontier'")
    pa = await create_player(client, tenant_a, "tenant-a", "Echo")
    await act(client, tenant_a, "tenant-a", pa, option="gate")
    await act(client, tenant_a, "tenant-a", pa, option="floor_1")
    s = await act(client, tenant_a, "tenant-a", pa, option="keep")
    # solo per-player fight — attack/close_in (017: melee opens at
    # range, so the first beat is crossing), never the shared strike
    ids = {o["id"] for o in s["options"]}
    assert ("attack" in ids or "close_in" in ids) and "strike" not in ids


async def test_morning_crier_once_per_day(client, tenant_a, clean_world):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Криер")
    await pool.execute(
        "UPDATE ascent_players SET doc = jsonb_set(doc, '{news_day}',"
        " '-1'::jsonb) WHERE tenant='tenant-a' AND player=$1", pa)
    s = await scene(client, tenant_a, "tenant-a", pa)
    assert "MORNING CRIER" in s["eyebrow"]
    assert s["event_kind"] == "news"
    assert any("at the frontier" in l for l in s["body_lines"])
    assert s["shard_note"]                     # the advice line
    s = await scene(client, tenant_a, "tenant-a", pa)
    assert "MORNING CRIER" not in s["eyebrow"]


async def test_import_lands_once_and_world_wins(client, tenant_a):
    from plugin_linear_ascent.engine import state as pstate

    player = f"p-{uuid.uuid4().hex[:8]}"
    doc = pstate.new_player(f"local:{player}")
    doc.update(stage="playing", name="Migrant", race="elf", clazz="archer",
               gold=777, level=4)

    body, headers = signed(tenant_a, "tenant-a",
                           {"player": player, "doc": doc})
    r = await client.post("/v1/import", content=body, headers=headers)
    assert r.status_code == 200 and r.json()["imported"], r.text

    body, headers = signed(tenant_a, "tenant-a", {"player": player})
    r = await client.post("/v1/character", content=body, headers=headers)
    sheet = r.json()
    assert sheet.get("race") == "elf"

    # second import: the world character exists now — world wins
    doc["name"] = "Usurper"
    body, headers = signed(tenant_a, "tenant-a",
                           {"player": player, "doc": doc})
    r = await client.post("/v1/import", content=body, headers=headers)
    assert r.status_code == 200 and not r.json()["imported"]


async def test_import_rejects_garbage(client, tenant_a):
    player = f"p-{uuid.uuid4().hex[:8]}"
    body, headers = signed(tenant_a, "tenant-a",
                           {"player": player, "doc": {"stage": "wizard"}})
    r = await client.post("/v1/import", content=body, headers=headers)
    assert r.status_code == 200 and not r.json()["imported"]
