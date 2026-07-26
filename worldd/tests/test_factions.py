"""010 — factions: lifecycle, attendance, weekly resolution (real DB)."""

import json
import uuid

import pytest

from app import db, factions
from plugin_linear_ascent.engine import state as pstate
from tests.test_multiplayer import create_player
from tests.test_world_api import act, make_tenant, signed


async def post(client, secret, tenant, path, payload):
    body, headers = signed(secret, tenant, payload)
    return await client.post(path, content=body, headers=headers)


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def tenant_b(client):
    return await make_tenant(client, "tenant-b")


@pytest.fixture
async def clean_factions(client):
    pool = await db.get_pool()

    async def wipe():
        await pool.execute("DELETE FROM ascent_faction_members")
        await pool.execute("DELETE FROM ascent_faction_weeks")
        await pool.execute("DELETE FROM ascent_factions")
        await pool.execute("DELETE FROM ascent_attendance")
    await wipe()
    yield
    await wipe()


def _name():
    return f"Banner {uuid.uuid4().hex[:6]}"


async def _rich(pool, tenant, player, gold=2000):
    await pool.execute(
        "UPDATE ascent_players SET doc = jsonb_set(doc, '{gold}', "
        "to_jsonb($3::bigint)) WHERE tenant=$1 AND player=$2",
        tenant, player, gold)


async def test_create_join_kick_leave_lifecycle(
        client, tenant_a, tenant_b, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Stew")
    pb = await create_player(client, tenant_b, "tenant-b", "Hand")
    await _rich(pool, "tenant-a", pa)
    name = _name()

    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                     {"player": pa, "name": name, "banner": "mecha_dragon"})
    assert r.status_code == 200, r.text

    # fee charged exactly once, ledgered
    doc = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='tenant-a' AND "
        "player=$1", pa))
    assert doc["gold"] == 2000 - factions.FOUND_FEE
    fee_rows = await pool.fetchval(
        "SELECT count(*) FROM ascent_ledger WHERE tenant='tenant-a' AND "
        "player=$1 AND kind='faction_found'", pa)
    assert fee_rows == 1

    # duplicate name refused
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                     {"player": pa, "name": name, "banner": "web_star"})
    assert r.status_code == 409

    # B joins; status shows both, steward is A
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/join",
                     {"player": pb, "faction": name})
    assert r.status_code == 200
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                     {"player": pa})
    s = r.json()
    assert s["faction"] == name and s["role"] == "steward"
    assert len(s["members"]) == 2
    assert s["base_pct"] == 0.15          # under 4 members
    assert s["banner"] == "mecha_dragon"

    # B's doc picks up the faction as its guild on the next scene
    r = await post(client, tenant_b, "tenant-b", "/v1/scene",
                     {"player": pb})
    doc_b = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='tenant-b' AND "
        "player=$1", pb))
    assert doc_b.get("guild") == name

    # non-steward cannot kick
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/kick",
                     {"player": pb, "target_tenant": "tenant-a",
                      "target_player": pa})
    assert r.status_code == 403

    # steward kicks B; B's doc loses the guild on next load
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/kick",
                     {"player": pa, "target_tenant": "tenant-b",
                      "target_player": pb})
    assert r.status_code == 200
    await post(client, tenant_b, "tenant-b", "/v1/scene", {"player": pb})
    doc_b = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='tenant-b' AND "
        "player=$1", pb))
    assert "guild" not in doc_b

    # steward leaves — empty faction dissolves
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/leave",
                     {"player": pa})
    assert r.status_code == 200
    left = await pool.fetchval(
        "SELECT count(*) FROM ascent_factions WHERE name=$1", name)
    assert left == 0


async def test_goal_setting_steward_only(client, tenant_a, tenant_b,
                                          clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Goala")
    pb = await create_player(client, tenant_b, "tenant-b", "Goalb")
    await _rich(pool, "tenant-a", pa)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                 {"player": pa, "name": name, "banner": "gear_sword"})
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
                 {"player": pb, "faction": name})

    r = await post(client, tenant_b, "tenant-b", "/v1/faction/goal",
                     {"player": pb, "kind": "cull", "target": 10})
    assert r.status_code == 403
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/goal",
                     {"player": pa, "kind": "bogus", "target": 10})
    assert r.status_code == 422
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/goal",
                     {"player": pa, "kind": "hoard", "target": 100})
    assert r.status_code == 200
    row = await pool.fetchrow(
        "SELECT goal_kind, goal_target FROM ascent_factions WHERE name=$1",
        name)
    assert row["goal_kind"] == "hoard" and row["goal_target"] == 100


async def test_attendance_recorded_on_act(client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Showup")
    await act(client, tenant_a, "tenant-a", pa, option="gate")
    days = await pool.fetch(
        "SELECT world_day FROM ascent_attendance WHERE tenant='tenant-a' "
        "AND player=$1", pa)
    assert len(days) == 1 and days[0]["world_day"] == pstate.world_day()


async def _seed_last_week(pool, name, members, goal_kind, goal_target,
                          attendance_days, kill_gold=0, kills=0, xp=0):
    """Rewind the faction to last week and plant ledger + attendance."""
    week = factions.world_week() - 1
    lo, _hi = factions.week_bounds_ts(week)
    mid = lo.replace(tzinfo=lo.tzinfo)          # inside the window
    await pool.execute(
        "UPDATE ascent_factions SET created_week=$2, goal_kind=$3, "
        "goal_target=$4 WHERE name=$1", name, week - 1, goal_kind,
        goal_target)
    await pool.execute(
        "UPDATE ascent_faction_members SET joined_day=$2 WHERE faction=$1",
        name, (week - 1) * 7)
    for (tenant, player), days in zip(members, attendance_days):
        for d in range(days):
            await pool.execute(
                "INSERT INTO ascent_attendance (tenant, player, world_day) "
                "VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
                tenant, player, week * 7 + d)
        if kill_gold or kills or xp:
            for _ in range(max(kills, 1)):
                await pool.execute(
                    "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                    " xp, note, created_at) VALUES ($1,$2,'kill',$3,$4,"
                    "'seed',$5)", tenant, player,
                    kill_gold // max(kills, 1), xp // max(kills, 1), mid)


async def test_weekly_resolution_full_attendance_pays_once(
        client, tenant_a, tenant_b, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Paya")
    pb = await create_player(client, tenant_b, "tenant-b", "Payb")
    await _rich(pool, "tenant-a", pa)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                 {"player": pa, "name": name, "banner": "iron_heart"})
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
                 {"player": pb, "faction": name})
    # both attended 4 days; hoard goal 100 met with 200 gold of kills
    await _seed_last_week(
        pool, name, [("tenant-a", pa), ("tenant-b", pb)],
        "hoard", 100, [4, 4], kill_gold=100, kills=2)

    gold_before = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='tenant-a' AND "
        "player=$1", pa))["gold"]

    r = await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                     {"player": pa})
    assert r.status_code == 200

    row = await pool.fetchrow(
        "SELECT * FROM ascent_faction_weeks WHERE faction=$1", name)
    assert row is not None
    assert row["multiplier"] == pytest.approx(1.0)
    # prize = 15% × 100 × 1.0 = 15, split evenly by days (4/4)
    prize_rows = await pool.fetch(
        "SELECT tenant, gold FROM ascent_ledger "
        "WHERE kind='faction_prize' AND player = ANY($1::text[])", [pa, pb])
    assert sum(r2["gold"] for r2 in prize_rows) == 15
    gold_after = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='tenant-a' AND "
        "player=$1", pa))["gold"]
    assert gold_after > gold_before

    # second status call: resolved exactly once
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                 {"player": pa})
    n = await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_weeks WHERE faction=$1", name)
    assert n == 1
    prize_rows2 = await pool.fetch(
        "SELECT gold FROM ascent_ledger "
        "WHERE kind='faction_prize' AND player = ANY($1::text[])", [pa, pb])
    assert len(prize_rows2) == len(prize_rows)


async def test_weekly_resolution_low_attendance_pays_nothing(
        client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Ghost")
    await _rich(pool, "tenant-a", pa)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                 {"player": pa, "name": name, "banner": "watch_owl"})
    # 1 day of 4 required (25% < 50%) — goal met but nobody showed
    await _seed_last_week(pool, name, [("tenant-a", pa)],
                          "hoard", 50, [1], kill_gold=100, kills=1)
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                 {"player": pa})
    row = await pool.fetchrow(
        "SELECT multiplier, prize_note FROM ascent_faction_weeks "
        "WHERE faction=$1", name)
    assert row["multiplier"] == 0
    prizes = await pool.fetchval(
        "SELECT count(*) FROM ascent_ledger "
        "WHERE kind='faction_prize' AND player=$1", pa)
    assert prizes == 0


async def test_weekly_resolution_cull_blesses_hp(
        client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Bless")
    await _rich(pool, "tenant-a", pa)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                 {"player": pa, "name": name, "banner": "wolf_howl"})
    # solo, 7 of 7 days (7/4 = 1.75 cap), cull goal met
    await _seed_last_week(pool, name, [("tenant-a", pa)],
                          "cull", 2, [7], kill_gold=20, kills=3)
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                 {"player": pa})
    row = await pool.fetchrow(
        "SELECT multiplier FROM ascent_faction_weeks WHERE faction=$1",
        name)
    assert row["multiplier"] == pytest.approx(1.75)
    doc = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='tenant-a' AND "
        "player=$1", pa))
    buff = doc.get("faction_buff")
    assert buff and buff["kind"] == "hp"
    assert buff["pct"] == round(0.15 * 1.75 * 100)   # 26%
    assert buff["week"] == factions.world_week()      # live THIS week
