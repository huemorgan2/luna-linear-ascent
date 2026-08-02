"""022/006 — the war's face, server half.

Threshold Crier lines fire once per wound; the horn letters exactly the
banner's roster once per wound (and never feeds the silence clock);
first blood and the deepest cut land on the Stone; the injection
carries the countdown the card shows.
"""

import json

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402
from tests.test_multiplayer import create_player  # noqa: E402
from tests.test_world_api import act, enter_floor, make_tenant  # noqa: E402


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def clean_world(client):
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")
    await pool.execute("DELETE FROM ascent_world WHERE key LIKE 'warden:%'")
    yield
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")
    await pool.execute("DELETE FROM ascent_world WHERE key LIKE 'warden:%'")


async def _strike(tenant, player, doc, floor, dmg):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await social._fx_warden_strike(
                conn, tenant, player, doc, {"floor": floor, "damage": dmg})


async def _horn(tenant, player, doc, floor):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await social._fx_horn(conn, tenant, player, doc,
                                  {"floor": floor})


async def _warden_row(pool, floor=1):
    row = await pool.fetchrow(
        "SELECT value FROM ascent_world WHERE key=$1", f"warden:{floor}")
    return json.loads(row["value"]) if row else None


async def _war_lines(pool):
    return await pool.fetchval(
        "SELECT count(*) FROM ascent_happenings WHERE kind='war'")


async def test_thresholds_fire_once_per_wound(client, tenant_a, clean_world):
    pool = await db.get_pool()
    doc = {"name": "Axa", "guild": ""}
    before = await _war_lines(pool)

    await _strike("tenant-a", "p-ax", doc, 1, 1)     # materialize the row
    v = await _warden_row(pool)
    base = int(v["hp_max"])
    assert await _war_lines(pool) == before          # barely a scratch

    # cut through 75%: one line, tower-wide
    await _strike("tenant-a", "p-ax", doc, 1, round(base * 0.30))
    assert await _war_lines(pool) == before + 1
    line = await pool.fetchval(
        "SELECT line FROM ascent_happenings WHERE kind='war' "
        "ORDER BY id DESC LIMIT 1")
    assert "75%" in line and "floor 1" in line

    # a scratch inside the same band: no refire
    await _strike("tenant-a", "p-ax", doc, 1, 1)
    assert await _war_lines(pool) == before + 1

    # one deep blow through 50 AND 25: both fire, once each
    await _strike("tenant-a", "p-ax", doc, 1, round(base * 0.45))
    assert await _war_lines(pool) == before + 3
    v = await _warden_row(pool)
    assert sorted(v["called"], reverse=True) == [75, 50, 25]


async def test_first_blood_lands_on_the_stone(client, tenant_a, clean_world):
    pool = await db.get_pool()
    await _strike("tenant-a", "p-fb", {"name": "Firstblood"}, 1, 1)
    line = await pool.fetchval(
        "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 1")
    assert "Firstblood drew first blood" in line


async def test_striker_rows_carry_ts_and_guild(client, tenant_a,
                                               clean_world):
    pool = await db.get_pool()
    await _strike("tenant-a", "p-g", {"name": "Gilda", "guild": "House Ash"},
                  1, 5)
    v = await _warden_row(pool)
    s = v["strikers"][0]
    assert s["guild"] == "House Ash" and s["ts"]


async def test_horn_letters_the_roster_once_per_wound(client, tenant_a,
                                                      clean_world):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Sounder")
    pb = await create_player(client, tenant_a, "tenant-a", "Hearer")
    for pl in (pa, pb):
        await pool.execute(
            "UPDATE ascent_players SET doc = jsonb_set(doc, '{guild}',"
            " '\"HornHouse\"') WHERE tenant='tenant-a' AND player=$1", pl)
    doc_a = {"name": "Sounder", "guild": "HornHouse"}
    await _strike("tenant-a", pa, doc_a, 1, 10)      # open the wound

    async def letters(pl):
        return await pool.fetchval(
            "SELECT count(*) FROM ascent_letters WHERE to_player=$1 "
            "AND body LIKE 'The horn:%'", pl)

    v_before = await _warden_row(pool)
    await _horn("tenant-a", pa, doc_a, 1)
    assert await letters(pb) == 1                    # the roster, minus you
    assert await letters(pa) == 0
    body = await pool.fetchval(
        "SELECT body FROM ascent_letters WHERE to_player=$1 "
        "AND body LIKE 'The horn:%'", pb)
    assert "floor 1" in body and "closes in" in body

    # once per BANNER per wound — even from another member's hand
    await _horn("tenant-a", pa, doc_a, 1)
    await _horn("tenant-a", pb, {"name": "Hearer", "guild": "HornHouse"}, 1)
    assert await letters(pb) == 1 and await letters(pa) == 0

    # and the horn never fed the silence clock
    v_after = await _warden_row(pool)
    assert v_after["ts"] == v_before["ts"]
    assert v_after["horns"] == ["HornHouse"]


async def test_keep_card_reads_the_countdown(client, tenant_a, clean_world):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Reader")
    await _strike("tenant-a", "p-x", {"name": "Cutter"}, 1, 10)
    await enter_floor(client, tenant_a, "tenant-a", pa, 1)
    s = await act(client, tenant_a, "tenant-a", pa, option="keep")
    body = "\n".join(s["body_lines"])
    # 025 §3: floor 1 is a siege floor — there IS no countdown to read,
    # and the card has to say so instead of leaving the player waiting on
    # a clock that will never run.
    assert "does not heal" in body
    assert "the wound is exactly as you left it" in body
    assert "Cutter" in body
