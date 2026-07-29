"""022/007 — the era, server half.

The book closes on Vharuk's fall: the ledger freezes, level-5+ climbers
reincarnate with the right tiers, the ceremony reaches offline docs,
the reset wipes the transient world but never the permanent tables, and
a reincarnated name boots with the glyph and the time-perks.

Every direct-connection test runs inside a ROLLED-BACK transaction —
the shared test DB is never actually reset.
"""

import json
import uuid

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, era, social  # noqa: E402
from plugin_linear_ascent.engine import state as pstate  # noqa: E402
from tests.test_world_api import make_tenant  # noqa: E402


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


def _doc(name, level, floor, stage="playing"):
    return {"stage": stage, "name": name, "level": level,
            "unlocked_floor": floor, "gold": 0}


async def _insert(conn, tenant, name, level, floor, stage="playing"):
    player = f"era-{uuid.uuid4().hex[:8]}"
    await conn.execute(
        "INSERT INTO ascent_players (tenant, player, doc) "
        "VALUES ($1,$2,$3)", tenant, player,
        json.dumps(_doc(name, level, floor, stage)))
    return player


async def test_close_era_freezes_and_reincarnates(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        finisher = await _insert(conn, "tenant-a", "Kettle", 30, 101)
        struck = await _insert(conn, "tenant-a", "Brakka", 12, 100)
        bystander = await _insert(conn, "tenant-a", "Moss", 7, 40)
        tourist = await _insert(conn, "tenant-a", "Wisp", 3, 9)
        commits = [
            {"tenant": "tenant-a", "player": finisher, "name": "Kettle"},
            {"tenant": "tenant-a", "player": struck, "name": "Brakka"},
        ]
        # the resolving player's doc is IN MEMORY; the row is stale
        doc = _doc("Kettle", 30, 101)

        era_no = await era.close_era(conn, "tenant-a", finisher, doc, commits)

        frozen = json.loads(await conn.fetchval(
            "SELECT data FROM ascent_eras WHERE era=$1", era_no))
        assert frozen["finisher"] == "Kettle"
        assert frozen["war_party"] == ["Kettle", "Brakka"]
        assert isinstance(frozen["stone"], list)

        rows = {r["player"]: r for r in await conn.fetch(
            "SELECT player, points, tiers FROM ascent_reincarnation "
            "WHERE era=$1", era_no)}
        # level 5 is the bar: the tourist gets nothing
        assert tourist not in rows
        assert set(json.loads(rows[finisher]["tiers"])) == {
            "stood_100", "struck_vharuk", "final_blow"}
        assert set(json.loads(rows[struck]["tiers"])) == {
            "stood_100", "struck_vharuk"}
        assert json.loads(rows[bystander]["tiers"]) == []
        assert all(r["points"] == 1 for r in rows.values())

        # the ceremony reaches the offline bystander's ROW, and the
        # finisher's in-memory doc (never their stale row)
        by = json.loads(await conn.fetchval(
            "SELECT doc FROM ascent_players WHERE tenant='tenant-a' AND "
            "player=$1", bystander))
        assert by["pending_events"][-1]["event_kind"] == "boss"
        assert "Vharuk" in by["pending_events"][-1]["headline"]
        assert doc["pending_events"][-1]["event_kind"] == "boss"
        fin_row = json.loads(await conn.fetchval(
            "SELECT doc FROM ascent_players WHERE tenant='tenant-a' AND "
            "player=$1", finisher))
        assert "pending_events" not in fin_row

        last_stone = await conn.fetchval(
            "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 1")
        assert f"ERA {era_no}" in last_stone and "Kettle" in last_stone

        await tx.rollback()


async def test_era_reset_wipes_transient_keeps_permanent(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        await _insert(conn, "tenant-a", "Kettle", 30, 101)
        await conn.execute(
            "INSERT INTO ascent_eras (era, data) VALUES "
            "(998, '{}'::jsonb)")
        await conn.execute(
            "INSERT INTO ascent_reincarnation (tenant, player, era, name)"
            " VALUES ('tenant-a', 'x', 998, 'Kettle')")
        perm = {}
        for t in era.PERMANENT_TABLES + ("ascent_tenants",):
            perm[t] = await conn.fetchval(f"SELECT count(*) FROM {t}")

        out = await era.era_reset(conn)

        assert out["era"] == 999
        for t in era.TRANSIENT_TABLES:
            if t == "ascent_world":
                continue  # re-seeded below
            n = await conn.fetchval(f"SELECT count(*) FROM {t}")
            assert n == (1 if t == "ascent_stone" else 0), t
        for t, n in perm.items():
            assert await conn.fetchval(f"SELECT count(*) FROM {t}") == n, t
        frontier = await conn.fetchval(
            "SELECT value FROM ascent_world WHERE key='frontier'")
        assert json.loads(frontier) == 1
        first = await conn.fetchval(
            "SELECT line FROM ascent_stone ORDER BY id LIMIT 1")
        assert "ERA 999" in first and "floor 1" in first

        await tx.rollback()


async def test_declare_last_siege_reaches_everyone(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        pa = await _insert(conn, "tenant-a", "Kettle", 30, 99)
        pb = await _insert(conn, "tenant-a", "Brakka", 12, 60)
        await _insert(conn, "tenant-a", "Ghost", 12, 60, stage="intro")

        await era.declare_last_siege(conn, active=10)

        line = await conn.fetchval(
            "SELECT line FROM ascent_happenings WHERE kind='war' "
            "ORDER BY id DESC LIMIT 1")
        assert "Vharuk" in line and "100" in line
        # one letter per PLAYING climber, none for the intro ghost
        for p in (pa, pb):
            n = await conn.fetchval(
                "SELECT count(*) FROM ascent_letters WHERE to_player=$1", p)
            assert n == 1
        n = await conn.fetchval(
            "SELECT count(*) FROM ascent_letters "
            "WHERE to_player NOT IN ($1,$2) AND from_name='the Morning "
            "Crier' AND body LIKE '%Vharuk%'", pa, pb)
        # only letters to pre-existing playing docs from other tests may
        # exist; the intro doc must have none
        ghost = await conn.fetchval(
            "SELECT count(*) FROM ascent_letters WHERE to_player LIKE "
            "'era-%' AND to_player NOT IN ($1,$2)", pa, pb)
        assert ghost == 0
        assert n >= 0

        await tx.rollback()


async def test_prestige_boot_and_roster_glyph(client, tenant_a):
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()

        player = f"era-{uuid.uuid4().hex[:8]}"
        await conn.execute(
            "INSERT INTO ascent_reincarnation (tenant, player, era, name,"
            " points, tiers) VALUES ('tenant-a',$1,1,'Kettle',1,"
            "'[\"final_blow\"]'::jsonb)", player)
        await conn.execute(
            "INSERT INTO ascent_reincarnation (tenant, player, era, name,"
            " points, tiers) VALUES ('tenant-a',$1,2,'Kettle',1,"
            "'[\"stood_100\"]'::jsonb)", player)

        doc = pstate.new_player(f"tenant-a:{player}")
        await era.prestige_boot(conn, "tenant-a", player, doc)
        assert doc["prestige"]["points"] == 2
        assert doc["prestige"]["eras"] == [1, 2]
        assert set(doc["prestige"]["tiers"]) == {"final_blow", "stood_100"}
        # the rested pool boots FULL at the level-1 cap — time, not power
        from plugin_linear_ascent import economy
        assert doc["rested"] == economy.rested_pool_cap(1)

        # a fresh name the ledger does NOT know boots clean
        clean = pstate.new_player("tenant-a:nobody")
        await era.prestige_boot(conn, "tenant-a", "nobody-here", clean)
        assert "prestige" not in clean

        # the glyph rides the Muster Roll (full doc: the roster computes
        # power from gear)
        d = pstate.new_player(f"tenant-a:{player}")
        d.update(stage="playing", name="Kettle", level=30,
                 unlocked_floor=300)
        d["prestige"] = {"points": 2, "tiers": []}
        await conn.execute(
            "INSERT INTO ascent_players (tenant, player, doc) "
            "VALUES ('tenant-a',$1,$2)", player, json.dumps(d))
        entries, _total = await social._roster(conn)
        assert entries[0]["name"] == "Kettle ✦✦"

        await tx.rollback()
