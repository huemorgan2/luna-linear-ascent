"""Cross-player drama over HTTP: PvP, letters, grants, boss quorum."""

import json
import uuid

import pytest

from app import db
from tests.test_world_api import act, make_tenant, scene, signed


@pytest.fixture
async def tenants(client):
    a = await make_tenant(client, "tenant-a")
    b = await make_tenant(client, "tenant-b")
    return a, b


async def create(client, secret, tenant, player, name,
                 race="human", clazz="warrior"):
    await scene(client, secret, tenant, player)
    for _ in range(9):                                # 016: through the movie
        await act(client, secret, tenant, player, option="next")
    await act(client, secret, tenant, player, option="begin")
    await act(client, secret, tenant, player, option=race)
    await act(client, secret, tenant, player, option=clazz)
    return await act(client, secret, tenant, player, text=name)


async def get_doc(tenant, player):
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player)
    return json.loads(row["doc"])


async def set_doc(tenant, player, doc):
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_players SET doc=$3 WHERE tenant=$1 AND player=$2",
        tenant, player, json.dumps(doc))


async def test_full_drama_loop(client, tenants):
    a, b = tenants
    pa, pb = f"a-{uuid.uuid4().hex[:6]}", f"b-{uuid.uuid4().hex[:6]}"
    na, nb = f"Ash{pa[-4:]}", f"Brook{pb[-4:]}"
    await create(client, a, "tenant-a", pa, na)
    await create(client, b, "tenant-b", pb, nb)

    # B is unlodged, above beginner protection, carrying gold
    docb = await get_doc("tenant-b", pb)
    docb.update({"level": 8, "gold": 400, "hp": 60})
    await set_doc("tenant-b", pb, docb)
    # A is strong enough to win
    doca = await get_doc("tenant-a", pa)
    doca.update({"level": 12, "hp": 200})
    doca["gear"]["weapon"] = "wolfbite"
    await set_doc("tenant-a", pa, doca)

    # A attacks B from the fields
    s = await act(client, a, "tenant-a", pa, option="fields")
    labels = [o["id"] for o in s["options"]]
    target = next(l for l in labels if l.startswith("attack_"))
    assert nb in target
    await act(client, a, "tenant-a", pa, option=target)

    # attacker sees the outcome as a pending event on next scene
    s = await scene(client, a, "tenant-a", pa)
    assert "took them in their sleep" in s["headline"] \
        or "waiting for you" in s["headline"]

    # victim's next scene is the death report (attacker won given stats)
    s = await scene(client, b, "tenant-b", pb)
    assert na in s["headline"] or "fields" in s["support"]

    # happenings carry the news
    s = await act(client, b, "tenant-b", pb, option="town")
    s = await scene(client, b, "tenant-b", pb)
    assert any(na in l for l in s["body_lines"])


async def test_letter_and_grant_flow(client, tenants):
    a, b = tenants
    pa, pb = f"a-{uuid.uuid4().hex[:6]}", f"b-{uuid.uuid4().hex[:6]}"
    na, nb = f"Cole{pa[-4:]}", f"Dara{pb[-4:]}"
    await create(client, a, "tenant-a", pa, na)
    await create(client, b, "tenant-b", pb, nb)

    doca = await get_doc("tenant-a", pa)
    doca.update({"gold": 1000, "level": 6})
    await set_doc("tenant-a", pa, doca)
    docb = await get_doc("tenant-b", pb)
    docb.update({"level": 6})
    await set_doc("tenant-b", pb, docb)

    # letter A → B
    await act(client, a, "tenant-a", pa, option="relay")
    await act(client, a, "tenant-a", pa, option=f"write_{nb}")
    await act(client, a, "tenant-a", pa, text="The wolves know your name.")
    # B reads it at the relay
    s = await act(client, b, "tenant-b", pb, option="relay")
    assert any(na in l for l in s["body_lines"])
    assert any("wolves know your name" in l for l in s["body_lines"])

    # grant A → B (100 gross, 90 net via letter)
    await act(client, a, "tenant-a", pa, option="town")
    await act(client, a, "tenant-a", pa, option="vault")
    await act(client, a, "tenant-a", pa, option="grants")
    await act(client, a, "tenant-a", pa, option=f"grantto_{nb}")
    await act(client, a, "tenant-a", pa, option="grantamt_100")
    gold_before = (await get_doc("tenant-b", pb))["gold"]
    await act(client, b, "tenant-b", pb, option="town")
    s = await act(client, b, "tenant-b", pb, option="relay")
    s = await act(client, b, "tenant-b", pb, option="collect")
    gold_after = (await get_doc("tenant-b", pb))["gold"]
    assert gold_after - gold_before == 90


async def test_gnarl_quorum_two_players(client, tenants):
    a, b = tenants
    pa, pb = f"a-{uuid.uuid4().hex[:6]}", f"b-{uuid.uuid4().hex[:6]}"
    na, nb = f"Ryn{pa[-4:]}", f"Sef{pb[-4:]}"
    await create(client, a, "tenant-a", pa, na)
    await create(client, b, "tenant-b", pb, nb)

    for t, p in (("tenant-a", pa), ("tenant-b", pb)):
        d = await get_doc(t, p)
        d.update({"level": 12, "hp": 184, "unlocked_floor": 10})
        d["gear"] = {"weapon": "emberfang", "shield": "dwarven_wall",
                     "armor": "chain_hauberk"}
        await set_doc(t, p, d)

    # both walk to the floor-10 keep; A pledges first
    for secret, t, p in ((a, "tenant-a", pa), (b, "tenant-b", pb)):
        await act(client, secret, t, p, option="gate")
        await act(client, secret, t, p, option="floor_10")
        s = await act(client, secret, t, p, option="keep")
        assert "war party" in " ".join(s["body_lines"])
        await act(client, secret, t, p, option="boss_commit")

    # quorum of 2 met on B's commit → resolution queued for both
    s = await scene(client, a, "tenant-a", pa)
    assert "Gnarl" in s["headline"]
    s2 = await scene(client, b, "tenant-b", pb)
    assert "Gnarl" in s2["headline"]

    # frontier advanced for everyone
    pool = await db.get_pool()
    frontier = await pool.fetchval(
        "SELECT (value)::int FROM ascent_world WHERE key='frontier'")
    assert frontier >= 11
    # names on the Stone
    stone = await pool.fetch("SELECT line FROM ascent_stone")
    assert any("Gnarl" in r["line"] for r in stone)
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")


async def test_muster_roll_lists_all_climbers(client, tenants):
    a, b = tenants
    pa, pb = f"a-{uuid.uuid4().hex[:6]}", f"b-{uuid.uuid4().hex[:6]}"
    na, nb = f"Vex{pa[-4:]}", f"Wren{pb[-4:]}"
    await create(client, a, "tenant-a", pa, na)
    await create(client, b, "tenant-b", pb, nb, race="elf", clazz="archer")

    # the board caps at 12, floor-sorted — put B near the tower's top so
    # leftover climbers from other sessions in the dev DB can't push it off
    docb = await get_doc("tenant-b", pb)
    docb.update({"level": 97, "unlocked_floor": 97, "bank": 5000})
    await set_doc("tenant-b", pb, docb)

    s = await act(client, a, "tenant-a", pa, option="muster")
    assert "climber" in s["headline"]
    # B out-climbs the fresh chars: on the board with class, floor, wealth
    rows = [l for l in s["body_lines"] if l.startswith(nb)]
    assert rows, s["body_lines"]
    assert "elf archer" in rows[0]
    assert "floor 97" in rows[0]
    assert "wealth #" in rows[0]
    # the board is sorted by frontier floor, strongest first
    floors = [int(l.split("floor ")[1].split(" ")[0])
              for l in s["body_lines"] if "floor " in l]
    assert floors == sorted(floors, reverse=True)
