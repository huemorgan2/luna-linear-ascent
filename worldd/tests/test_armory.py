"""017 phase 007 — the faction armory (real DB).

The EV law: no gold enters or leaves through the armory — deposit moves
(slug, wear) from the doc into a row, take moves the SAME pair back.
Caps: 50 rows per faction, one take per player per world day, members
only both ways, wear never laundered.
"""

import json
import uuid

import pytest

from app import armory, db
from plugin_linear_ascent import economy
from tests.test_factions import _set_money, clean_factions, post  # noqa: F401
from tests.test_factions import tenant_a, tenant_b  # noqa: F401
from tests.test_multiplayer import create_player
from tests.test_world_api import act


@pytest.fixture
async def clean_armory(client, clean_factions):  # noqa: F811
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_armory")
    await pool.execute("DELETE FROM ascent_armory_takes")
    yield
    await pool.execute("DELETE FROM ascent_armory")
    await pool.execute("DELETE FROM ascent_armory_takes")


def _name():
    return f"Armory {uuid.uuid4().hex[:6]}"


async def _doc(pool, tenant, player):
    return json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player))


async def _patch_doc(pool, tenant, player, **fields):
    doc = await _doc(pool, tenant, player)
    doc.update(fields)
    await pool.execute(
        "UPDATE ascent_players SET doc=$3 WHERE tenant=$1 AND player=$2",
        tenant, player, json.dumps(doc))
    return doc


async def _crew(client, pool, sa, sb):
    """A two-member banner: founder pa (tenant-a), member pb (tenant-b)."""
    pa = await create_player(client, sa, "tenant-a", "Giver")
    pb = await create_player(client, sb, "tenant-b", "Taker")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 2000)
    name = _name()
    r = await post(client, sa, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl",
                    "join_fee": 0, "weekly_dues": 5})
    assert r.status_code == 200, r.text
    r = await post(client, sb, "tenant-b", "/v1/faction/request",
                   {"player": pb, "name": name})
    assert r.status_code == 200, r.text
    r = await post(client, sa, "tenant-a", "/v1/faction/approve",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 200, r.text
    return pa, pb, name


async def test_donate_take_round_trip_moves_no_gold(
        client, tenant_a, tenant_b, clean_armory):  # noqa: F811
    """The whole loop: pawn donate → rack row → desk take. Gold is
    untouched on both ends and the wear rides through exactly."""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    g = economy.FORGE["pigsticker"]
    pool_size = economy.item_pool(g)
    worn_left = pool_size // 3
    await _patch_doc(pool, "tenant-a", pa,
                     inventory={"pigsticker": 1},
                     durability_pack={"pigsticker": worn_left})
    gold_a0 = (await _doc(pool, "tenant-a", pa))["gold"]

    # the pawn scene offers the donate to a member
    await act(client, tenant_a, "tenant-a", pa, option="pawn")
    s = await act(client, tenant_a, "tenant-a", pa,
                  option="donate_pigsticker")
    assert "goes to the" in " ".join(s["body_lines"])
    row = await pool.fetchrow("SELECT * FROM ascent_armory")
    assert row["slug"] == "pigsticker" and row["faction"] == name
    assert row["uses_left"] == worn_left
    assert row["donor_name"] == "Giver"
    da = await _doc(pool, "tenant-a", pa)
    assert "pigsticker" not in (da.get("inventory") or {})
    assert "pigsticker" not in (da.get("durability_pack") or {})
    assert da["gold"] == gold_a0                       # EV law, donor side

    # the desk lists it for the other member, take moves it over
    gold_b0 = (await _doc(pool, "tenant-b", pb))["gold"]
    s = await act(client, tenant_b, "tenant-b", pb, option="guildhall")
    joined = " ".join(s["body_lines"])
    assert "ARMORY 1/" in joined and "Pigsticker" in joined
    take = next(o["id"] for o in s["options"]
                if o["id"].startswith("take_arm_"))
    s = await act(client, tenant_b, "tenant-b", pb, option=take)
    assert "comes off the rack" in " ".join(s["body_lines"])
    db_doc = await _doc(pool, "tenant-b", pb)
    assert db_doc["inventory"].get("pigsticker") == 1
    assert db_doc["durability_pack"]["pigsticker"] == worn_left  # no launder
    assert db_doc["gold"] == gold_b0                   # EV law, taker side
    assert await pool.fetchval("SELECT count(*) FROM ascent_armory") == 0


async def test_one_take_a_day(client, tenant_a, tenant_b,
                               clean_armory):  # noqa: F811
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    for slug in ("pigsticker", "wolfbite"):
        await armory_seed(pool, name, slug)
    s = await act(client, tenant_b, "tenant-b", pb, option="guildhall")
    takes = [o["id"] for o in s["options"] if o["id"].startswith("take_arm_")]
    assert len(takes) == 2
    await act(client, tenant_b, "tenant-b", pb, option=takes[0])
    # the second take the same day: no options offered, refusal on click
    s = await act(client, tenant_b, "tenant-b", pb, option="guildhall")
    assert not any(o["id"].startswith("take_arm_") for o in s["options"])
    assert "already took" in " ".join(s["body_lines"])


async def armory_seed(pool, faction, slug, uses=None, tenant="tenant-x",
                      player="seed", donor="Seeder"):
    await pool.execute(
        "INSERT INTO ascent_armory (faction, tenant, player, donor_name,"
        " slug, uses_left) VALUES ($1,$2,$3,$4,$5,$6)",
        faction, tenant, player, donor, slug, uses)


async def test_cap_bounces_the_deposit_with_a_letter(
        client, tenant_a, tenant_b, clean_armory):  # noqa: F811
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    for _ in range(armory.ARMORY_CAP):
        await armory_seed(pool, name, "pigsticker")
    await _patch_doc(pool, "tenant-a", pa, inventory={"wolfbite": 1})
    await act(client, tenant_a, "tenant-a", pa, option="pawn")
    s = await act(client, tenant_a, "tenant-a", pa, option="donate_wolfbite")
    # the engine sees the full rack in the injection and refuses on the
    # spot — the piece never moves, no effect fires
    assert "full" in s["shard_note"]
    da = await _doc(pool, "tenant-a", pa)
    assert da["inventory"].get("wolfbite") == 1
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_armory") == armory.ARMORY_CAP
    # the worldd guard holds on its own too (the race path → letter)
    async with pool.acquire() as conn:
        err = await armory.deposit(conn, "tenant-a", pa, da,
                                   "wolfbite", None)
    assert err and "racks are full" in err


async def test_members_only_both_ways(client, tenant_a, tenant_b,
                                       clean_armory):  # noqa: F811
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    loner = await create_player(client, tenant_b, "tenant-b", "Loner")
    await _patch_doc(pool, "tenant-b", loner, inventory={"pigsticker": 1})
    # no faction → the pawn scene never offers the donate
    s = await act(client, tenant_b, "tenant-b", loner, option="pawn")
    assert not any(o["id"].startswith("donate_") for o in s["options"])
    # and the deposit function itself refuses a non-member
    await armory_seed(pool, name, "wolfbite")
    doc = await _doc(pool, "tenant-b", loner)
    async with pool.acquire() as conn:
        err = await armory.deposit(conn, "tenant-b", loner, doc,
                                   "pigsticker", None)
        assert err and "member" in err
        err = await armory.take(conn, "tenant-b", loner, doc, 1)
        assert err and "member" in err


async def test_take_keeps_the_worse_wear_never_launders(
        client, tenant_a, tenant_b, clean_armory):  # noqa: F811
    """Owning a worn copy and taking a fresher one must not reset the
    stash — the worse of the two survives."""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    fresh_left = 900
    await armory_seed(pool, name, "pigsticker", uses=fresh_left)
    await _patch_doc(pool, "tenant-b", pb,
                     inventory={"pigsticker": 1},
                     durability_pack={"pigsticker": 10})
    s = await act(client, tenant_b, "tenant-b", pb, option="guildhall")
    take = next(o["id"] for o in s["options"]
                if o["id"].startswith("take_arm_"))
    await act(client, tenant_b, "tenant-b", pb, option=take)
    d = await _doc(pool, "tenant-b", pb)
    assert d["inventory"]["pigsticker"] == 2
    assert d["durability_pack"]["pigsticker"] == 10    # the worse survives
