"""007 — one shared Warden per floor, world news, character import."""

import json
import uuid

import pytest

from app import db
from tests.test_world_api import act, enter_floor, make_tenant, scene, signed


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
    await act(client, secret, tenant, player, text=name)
    return player


async def test_shared_warden_one_hp_pool_kill_opens_for_all(
        client, tenant_a, tenant_b, clean_world):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")

    # A walks to the floor-1 keep: the SHARED warden, one pool for all
    await enter_floor(client, tenant_a, "tenant-a", pa, 1)
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
    # break away — the fight's total lands as ONE effect when A gets out.
    # 048: rank-2 hands can miss, so a fled swing may carry no wound —
    # walk back in and swing again until one lands.
    v = None
    for _ in range(20):
        await pool.execute(
            "UPDATE ascent_players SET doc = jsonb_set(jsonb_set(doc,"
            " '{hp}', '999'::jsonb), '{energy}', '999'::jsonb)"
            " WHERE tenant='tenant-a' AND player=$1", pa)
        s = await act(client, tenant_a, "tenant-a", pa, option="run")
        row = await pool.fetchrow(
            "SELECT value FROM ascent_world WHERE key='warden:1'")
        if row and json.loads(row["value"]).get("strikers"):
            v = json.loads(row["value"])
            break
        s = await act(client, tenant_a, "tenant-a", pa, option="keep")
        if any(o["id"] == "strike" for o in s["options"]):
            s = await act(client, tenant_a, "tenant-a", pa, option="strike")
        if any(o["id"] == "close_in" for o in s["options"]):
            await act(client, tenant_a, "tenant-a", pa, option="close_in")
        await act(client, tenant_a, "tenant-a", pa, option="attack")
    assert v, "fleeing must persist the wounds to the world pool"
    assert v["strikers"][0]["name"] == "Aldo" and v["strikers"][0]["dmg"] > 0

    # B sees the SAME wounded warden, with A's name on it
    await enter_floor(client, tenant_b, "tenant-b", pb, 1)
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
    # 048: a swing can miss — the warden holds at 1 HP either way, so
    # keep B topped up and swinging until the blow lands.
    for _ in range(20):
        s = await act(client, tenant_b, "tenant-b", pb, option="attack")
        if "falls" in s["headline"]:
            break
        await pool.execute(
            "UPDATE ascent_players SET doc = jsonb_set(jsonb_set(doc,"
            " '{hp}', '999'::jsonb), '{energy}', '999'::jsonb)"
            " WHERE tenant='tenant-b' AND player=$1", pb)
        if any(o["id"] == "close_in" for o in s["options"]):
            await act(client, tenant_b, "tenant-b", pb, option="close_in")
    # 033: the kill card IS the fall reel, and it pays on the spot —
    # worldd lands the settled split on the outgoing card.
    assert "falls" in s["headline"]
    assert any("killing blow" in l for l in s["body_lines"])
    assert any("share of the kill" in l for l in s["body_lines"])
    assert "Struck down by" in s["support"]
    assert "Brai" in s["support"]

    row = await pool.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    assert int(json.loads(row["value"])) == 2

    # B's next scene: a refresh mid-reel replays the fall, receipt intact
    s = await scene(client, tenant_b, "tenant-b", pb)
    assert "falls" in s["headline"]
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


async def test_below_frontier_keep_is_a_memorial(client, tenant_a,
                                                 clean_world):
    """034 §3: the echo bout is retired end to end — through the real
    HTTP act, a keep below the frontier opens a monument with no fight
    in it and no shared strike either."""
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_world SET value='3'::jsonb WHERE key='frontier'")
    pa = await create_player(client, tenant_a, "tenant-a", "Echo")
    await enter_floor(client, tenant_a, "tenant-a", pa, 1)
    s = await act(client, tenant_a, "tenant-a", pa, option="keep")
    ids = {o["id"] for o in s["options"]}
    assert ids == {"back"}
    assert "fell here" in s["headline"]


async def test_morning_crier_once_per_day(client, tenant_a, clean_world):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Криер")
    await pool.execute(
        "UPDATE ascent_players SET doc = jsonb_set(doc, '{news_day}',"
        " '-1'::jsonb) WHERE tenant='tenant-a' AND player=$1", pa)
    # 030 Phase 5: the Crier is a PAPER riding the town card, not an
    # interstitial — it stays pinned until its ✕ stamps news_day.
    s = await scene(client, tenant_a, "tenant-a", pa)
    assert s["paper"]
    assert any("at the frontier" in l for l in s["paper"]["items"])
    s = await scene(client, tenant_a, "tenant-a", pa)
    assert s["paper"]                          # unread stays pinned
    s = await act(client, tenant_a, "tenant-a", pa, option="news_close")
    assert not s.get("paper")                  # closed stays closed


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
