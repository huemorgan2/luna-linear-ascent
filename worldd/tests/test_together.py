"""022/008 — together, server half.

The flare row's one-per-floor law, the first-tap-wins answer (pay,
Stone, exactly once), the kill-log ring the assist window reads, the
long fire's five seats, and the stew letter. All world-row state —
never a write into another player's doc.
"""

import datetime as dt
import json
import uuid

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402
from plugin_linear_ascent import economy  # noqa: E402
from plugin_linear_ascent.engine import state as pstate  # noqa: E402
from tests.test_world_api import make_tenant  # noqa: E402


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


def _doc(name):
    d = pstate.new_player(f"t:{name}")
    d.update(stage="playing", name=name)
    return d


async def _insert(conn, tenant, doc):
    player = f"tog-{uuid.uuid4().hex[:8]}"
    await conn.execute(
        "INSERT INTO ascent_players (tenant, player, doc) "
        "VALUES ($1,$2,$3)", tenant, player, json.dumps(doc))
    return player


async def _row(conn, key):
    v = await conn.fetchval(
        "SELECT value FROM ascent_world WHERE key=$1", key)
    return json.loads(v) if v else None


async def test_one_live_flare_per_floor_first_cry_holds(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        moss, kettle = _doc("Moss"), _doc("Kettle")
        await social._fx_flare(conn, "tenant-a", "p-moss", moss,
                               {"floor": 7, "slug": "gully_rat",
                                "monster": "gully rat"})
        v = await _row(conn, "flare:7")
        assert v["name"] == "Moss" and v["answered_by"] is None
        # a second cry does not clobber a live flare
        await social._fx_flare(conn, "tenant-a", "p-kettle", kettle,
                               {"floor": 7, "slug": "x", "monster": "x"})
        assert (await _row(conn, "flare:7"))["name"] == "Moss"
        # …but a guttered one gives up the sky
        v["ts"] = (pstate.now() - dt.timedelta(
            minutes=economy.FLARE_TTL_MIN + 1)).isoformat()
        await conn.execute(
            "UPDATE ascent_world SET value=$1::jsonb WHERE key='flare:7'",
            json.dumps(v))
        await social._fx_flare(conn, "tenant-a", "p-kettle", kettle,
                               {"floor": 7, "slug": "x", "monster": "x"})
        assert (await _row(conn, "flare:7"))["name"] == "Kettle"

        await tx.rollback()


async def test_first_answer_wins_pay_stone_exactly_once(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        moss = _doc("Moss")
        await social._fx_flare(conn, "tenant-a", "p-moss", moss,
                               {"floor": 7, "slug": "gully_rat",
                                "monster": "gully rat"})
        # the sender cannot answer their own cry
        await social._fx_flare_answer(conn, "tenant-a", "p-moss", moss,
                                      {"floor": 7})
        assert (await _row(conn, "flare:7"))["answered_by"] is None

        brakka = _doc("Brakka")
        gold0, xp0 = brakka["gold"], brakka["xp"]
        await social._fx_flare_answer(conn, "tenant-a", "p-brakka",
                                      brakka, {"floor": 7})
        assert (await _row(conn, "flare:7"))["answered_by"] == "Brakka"
        assert brakka["gold"] - gold0 == economy.flare_answer_gold(7)
        assert brakka["xp"] - xp0 == economy.FLARE_ANSWER_AETHER
        stone = await conn.fetchval(
            "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 1")
        assert "Brakka answered a flare on floor 7" in stone

        # the second tap gets nothing — the plaque is claimed
        kettle = _doc("Kettle")
        gold0 = kettle["gold"]
        await social._fx_flare_answer(conn, "tenant-a", "p-kettle",
                                      kettle, {"floor": 7})
        assert kettle["gold"] == gold0
        n = await conn.fetchval(
            "SELECT count(*) FROM ascent_ledger WHERE kind='flare_answer'"
            " AND note LIKE 'floor 7%'")
        assert n == 1

        await tx.rollback()


async def test_kill_log_ring_prunes_and_caps(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        brakka = _doc("Brakka")
        for _ in range(14):
            await social._fx_kill_note(conn, brakka,
                                       {"floor": 3, "slug": "gully_rat"})
        ring = await _row(conn, "kills:3")
        assert len(ring) == 12                     # capped
        # a stale entry is pruned on the next write
        ring[0]["ts"] = (pstate.now() - dt.timedelta(
            minutes=economy.ASSIST_WINDOW_MIN + 1)).isoformat()
        await conn.execute(
            "UPDATE ascent_world SET value=$1::jsonb WHERE key='kills:3'",
            json.dumps(ring))
        await social._fx_kill_note(conn, brakka,
                                   {"floor": 3, "slug": "gully_rat"})
        assert len(await _row(conn, "kills:3")) == 12
        # the injection read prunes too
        assert len(await social._floor_kills(conn, 3)) == 12

        await tx.rollback()


async def test_injection_carries_flare_kills_and_fire(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        moss = _doc("Moss")
        await _insert(conn, "tenant-a", moss)
        await social._fx_flare(conn, "tenant-a", "p-moss", moss,
                               {"floor": 2, "slug": "gully_rat",
                                "monster": "gully rat"})
        fw = await social._floor_flare(conn, "tenant-a", "p-else", 2)
        assert fw["name"] == "Moss" and fw["own"] is False
        fw = await social._floor_flare(conn, "tenant-a", "p-moss", 2)
        assert fw["own"] is True
        assert await social._floor_flare(conn, "tenant-a", "p-else", 9) \
            is None

        await tx.rollback()


async def test_the_fire_keeps_five_seats_one_per_name(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        for i in range(7):
            await social._fx_fire_word(conn, _doc(f"Climber{i}"),
                                       {"word": economy.FIRE_WORDS[0]})
        fire = await social._long_fire(conn)
        assert len(fire) == 5
        assert fire[0]["name"] == "Climber6"       # latest first
        # saying a second word retakes your seat, no duplicate
        await social._fx_fire_word(conn, _doc("Climber6"),
                                   {"word": economy.FIRE_WORDS[1]})
        fire = await social._long_fire(conn)
        assert len(fire) == 5
        assert [f["name"] for f in fire].count("Climber6") == 1
        assert fire[0]["word"] == economy.FIRE_WORDS[1]

        await tx.rollback()


async def test_the_stew_letter_reaches_the_stranger(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        name = f"Stranger{uuid.uuid4().hex[:6]}"
        target = await _insert(conn, "tenant-a", _doc(name))
        await social._fx_fire_stew(conn, _doc("Testa"), {"to_name": name})
        row = await conn.fetchrow(
            "SELECT from_name, body FROM ascent_letters "
            "WHERE to_player=$1 ORDER BY id DESC LIMIT 1", target)
        assert row["from_name"] == "Testa"
        assert "stood you a stew" in row["body"]
        # an unknown name is a quiet no-op
        await social._fx_fire_stew(conn, _doc("Testa"),
                                   {"to_name": "nobody-of-that-name"})

        await tx.rollback()
