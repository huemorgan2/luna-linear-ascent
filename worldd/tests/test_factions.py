"""010 — factions: lifecycle, the store, weekly challenge, board (real DB).

Third + fourth directives: join fees and weekly dues land in the faction
store; the world posts ONE challenge per week and entering it is paid from
the store; the COMMUNITY board is read-only news.
"""

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
        await pool.execute("DELETE FROM ascent_faction_requests")
        await pool.execute("DELETE FROM ascent_faction_members")
        await pool.execute("DELETE FROM ascent_faction_weeks")
        await pool.execute("DELETE FROM ascent_faction_ledger")
        await pool.execute("DELETE FROM ascent_factions")
        await pool.execute("DELETE FROM ascent_attendance")
        await pool.execute(
            "DELETE FROM ascent_world WHERE key='challenge_week'")
        await pool.execute(
            "DELETE FROM ascent_happenings WHERE kind='faction'")
    await wipe()
    yield
    await wipe()


def _name():
    return f"Banner {uuid.uuid4().hex[:6]}"


async def _set_money(pool, tenant, player, gold, bank=0, level=5):
    """Fund a character (and rank them past the 015 founding gate)."""
    await pool.execute(
        "UPDATE ascent_players SET doc = doc "
        "|| jsonb_build_object('gold', $3::bigint, 'bank', $4::bigint,"
        " 'level', $5::int) "
        "WHERE tenant=$1 AND player=$2", tenant, player, gold, bank, level)


async def _money(pool, tenant, player):
    doc = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player))
    return doc.get("gold", 0), doc.get("bank", 0), doc


async def _treasury(pool, name):
    return await pool.fetchval(
        "SELECT treasury FROM ascent_factions WHERE name=$1", name)


async def test_create_join_fee_lands_in_store(client, tenant_a, tenant_b,
                                              clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Stew")
    pb = await create_player(client, tenant_b, "tenant-b", "Hand")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 10, bank=40)
    name = _name()

    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "mecha_dragon",
                    "join_fee": 25, "weekly_dues": 5})
    assert r.status_code == 200, r.text
    gold, _, _ = await _money(pool, "tenant-a", pa)
    assert gold == 2000 - factions.FOUND_FEE   # founder pays no join fee

    # duplicate name refused
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "web_star"})
    assert r.status_code == 409

    # B joins: ◈25 charged gold-first-then-bank, into the store, ledgered
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/join",
                   {"player": pb, "faction": name})
    assert r.status_code == 200
    gold_b, bank_b, _ = await _money(pool, "tenant-b", pb)
    assert (gold_b, bank_b) == (0, 25)         # 10 gold + 15 from the bank
    assert await _treasury(pool, name) == 25
    led = await pool.fetchrow(
        "SELECT kind, amount FROM ascent_faction_ledger WHERE faction=$1",
        name)
    assert led["kind"] == "join_fee" and led["amount"] == 25

    # status shows the purse: store, fee, dues, both members
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                   {"player": pa})
    s = r.json()
    assert s["faction"] == name and s["role"] == "steward"
    assert s["store"] == 25 and s["join_fee"] == 25 and s["dues"] == 5
    assert len(s["members"]) == 2
    assert s["week"]["base_pct"] == 0.15       # under 4 members

    # a broke climber can't buy in
    pc = await create_player(client, tenant_b, "tenant-b", "Broke")
    await _set_money(pool, "tenant-b", pc, 0, bank=0)
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/join",
                   {"player": pc, "faction": name})
    assert r.status_code == 409 and "join fee" in r.json()["detail"]


async def test_donate_and_enter_the_week(client, tenant_a, tenant_b,
                                         clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Coin")
    pb = await create_player(client, tenant_b, "tenant-b", "Purse")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 100)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
               {"player": pa, "name": name, "banner": "gear_sword",
                "join_fee": 0, "weekly_dues": 5})
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
               {"player": pb, "faction": name})

    # non-steward can't sign the entry
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/enter",
                   {"player": pb})
    assert r.status_code == 409 and "steward" in r.json()["detail"]

    # store empty: entry (◈5 × 2) refused with the shortfall shown
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/enter",
                   {"player": pa})
    assert r.status_code == 409 and "short" in r.json()["detail"]

    # pass the hat: a member donates carried gold
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/donate",
                   {"player": pb, "amount": 30})
    assert r.status_code == 200
    gold_b, _, _ = await _money(pool, "tenant-b", pb)
    assert gold_b == 70
    assert await _treasury(pool, name) == 30

    # over-donation refused (carried gold only)
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/donate",
                   {"player": pb, "amount": 999})
    assert r.status_code == 409

    # now the entry lands: kind = week % 3, target frozen, store debited
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/enter",
                   {"player": pa})
    assert r.status_code == 200
    assert await _treasury(pool, name) == 20
    week = factions.world_week()
    row = await pool.fetchrow(
        "SELECT goal_kind, goal_target, entered, entry_paid, resolved "
        "FROM ascent_faction_weeks WHERE faction=$1 AND week=$2",
        name, week)
    assert row["entered"] and not row["resolved"]
    assert row["goal_kind"] == factions.week_kind(week)
    assert row["goal_target"] > 0 and row["entry_paid"] == 10

    # double entry refused
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/enter",
                   {"player": pa})
    assert r.status_code == 409 and "already" in r.json()["detail"]


async def test_attendance_recorded_on_act(client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Showup")
    await act(client, tenant_a, "tenant-a", pa, option="gate")
    days = await pool.fetch(
        "SELECT world_day FROM ascent_attendance WHERE tenant='tenant-a' "
        "AND player=$1", pa)
    assert len(days) == 1 and days[0]["world_day"] == pstate.world_day()


async def _seed_last_week(pool, name, members, goal_kind, goal_target,
                          attendance_days, kill_gold=0, kills=0, xp=0,
                          entered=True):
    """Rewind the faction to last week: the week row says it ENTERED the
    world challenge; attendance + ledger rows carry the progress."""
    week = factions.world_week() - 1
    lo, _hi = factions.week_bounds_ts(week)
    mid = lo.replace(tzinfo=lo.tzinfo)          # inside the window
    await pool.execute(
        "UPDATE ascent_factions SET created_week=$2 WHERE name=$1",
        name, week - 1)
    await pool.execute(
        "UPDATE ascent_faction_members SET joined_day=$2 WHERE faction=$1",
        name, (week - 1) * 7)
    if entered:
        await pool.execute(
            "INSERT INTO ascent_faction_weeks (faction, week, goal_kind,"
            " goal_target, entered, entry_paid, resolved) "
            "VALUES ($1,$2,$3,$4,true,0,false)",
            name, week, goal_kind, goal_target)
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


async def test_weekly_resolution_pays_prize_and_collects_dues(
        client, tenant_a, tenant_b, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Paya")
    pb = await create_player(client, tenant_b, "tenant-b", "Payb")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 3, bank=100)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
               {"player": pa, "name": name, "banner": "iron_heart",
                "join_fee": 0, "weekly_dues": 5})
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
               {"player": pb, "faction": name})
    # both attended 4 days; hoard goal 100 met with 200 gold of kills
    await _seed_last_week(
        pool, name, [("tenant-a", pa), ("tenant-b", pb)],
        "hoard", 100, [4, 4], kill_gold=100, kills=2)

    r = await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                   {"player": pa})
    assert r.status_code == 200

    row = await pool.fetchrow(
        "SELECT * FROM ascent_faction_weeks WHERE faction=$1", name)
    assert row["resolved"] and row["won"]
    assert row["multiplier"] == pytest.approx(1.0)
    # prize = 15% × 100 × 1.0 = 15, split by days — minted, NOT store gold
    prize_rows = await pool.fetch(
        "SELECT tenant, gold FROM ascent_ledger "
        "WHERE kind='faction_prize' AND player = ANY($1::text[])", [pa, pb])
    assert sum(r2["gold"] for r2 in prize_rows) == 15

    # dues: ◈5 each, gold-first-then-bank, into the store, ledgered
    assert await _treasury(pool, name) == 10
    gold_b, bank_b, _ = await _money(pool, "tenant-b", pb)
    assert (gold_b + bank_b) >= 100 - 5        # paid 5, then won a share
    dues_rows = await pool.fetch(
        "SELECT amount FROM ascent_faction_ledger WHERE faction=$1 AND "
        "kind='dues'", name)
    assert [r2["amount"] for r2 in dues_rows] == [5, 5]

    # second status call: resolved exactly once, no double dues/prize
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
               {"player": pa})
    assert await _treasury(pool, name) == 10
    prize_rows2 = await pool.fetch(
        "SELECT gold FROM ascent_ledger "
        "WHERE kind='faction_prize' AND player = ANY($1::text[])", [pa, pb])
    assert len(prize_rows2) == len(prize_rows)


async def test_broke_member_goes_into_arrears_and_misses_the_split(
        client, tenant_a, tenant_b, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Solva")
    pb = await create_player(client, tenant_b, "tenant-b", "Skint")
    await _set_money(pool, "tenant-a", pa, 2000)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
               {"player": pa, "name": name, "banner": "watch_owl",
                "join_fee": 0, "weekly_dues": 5})
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
               {"player": pb, "faction": name})
    await _set_money(pool, "tenant-b", pb, 0, bank=0)   # flat broke
    await _seed_last_week(
        pool, name, [("tenant-a", pa), ("tenant-b", pb)],
        "hoard", 100, [4, 4], kill_gold=100, kills=2)

    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
               {"player": pa})
    # B is flagged, skipped from the split — A takes the whole pool
    arrears = await pool.fetchval(
        "SELECT arrears FROM ascent_faction_members WHERE tenant='tenant-b'"
        " AND player=$1", pb)
    assert arrears is True
    assert await _treasury(pool, name) == 5     # only A's dues landed
    prize_b = await pool.fetchval(
        "SELECT count(*) FROM ascent_ledger WHERE kind='faction_prize' "
        "AND player=$1", pb)
    assert prize_b == 0
    prize_a = await pool.fetchval(
        "SELECT sum(gold) FROM ascent_ledger WHERE kind='faction_prize' "
        "AND player=$1", pa)
    assert prize_a == 15

    # solvent again → arrears clears at the next week turn
    await _set_money(pool, "tenant-b", pb, 500)
    await pool.execute(
        "UPDATE ascent_faction_weeks SET week = week - 1 WHERE faction=$1",
        name)
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
               {"player": pa})
    arrears = await pool.fetchval(
        "SELECT arrears FROM ascent_faction_members WHERE tenant='tenant-b'"
        " AND player=$1", pb)
    assert arrears is False


async def test_not_entered_week_collects_dues_but_pays_nothing(
        client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Sitout")
    await _set_money(pool, "tenant-a", pa, 2000)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
               {"player": pa, "name": name, "banner": "wolf_howl",
                "join_fee": 0, "weekly_dues": 5})
    # attended plenty, earned plenty — but never entered the challenge
    await _seed_last_week(pool, name, [("tenant-a", pa)],
                          "hoard", 50, [7], kill_gold=100, kills=1,
                          entered=False)
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
               {"player": pa})
    row = await pool.fetchrow(
        "SELECT resolved, entered, won, prize_note "
        "FROM ascent_faction_weeks WHERE faction=$1", name)
    assert row["resolved"] and not row["entered"] and not row["won"]
    assert "no entry" in row["prize_note"]
    assert await _treasury(pool, name) == 5     # dues still collect
    prizes = await pool.fetchval(
        "SELECT count(*) FROM ascent_ledger "
        "WHERE kind='faction_prize' AND player=$1", pa)
    assert prizes == 0


async def test_weekly_resolution_cull_blesses_hp(
        client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Bless")
    await _set_money(pool, "tenant-a", pa, 2000)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
               {"player": pa, "name": name, "banner": "wolf_howl",
                "join_fee": 0, "weekly_dues": 1})
    # solo, 7 of 7 days (7/4 = 1.75 cap), cull goal met
    await _seed_last_week(pool, name, [("tenant-a", pa)],
                          "cull", 2, [7], kill_gold=20, kills=3)
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
               {"player": pa})
    row = await pool.fetchrow(
        "SELECT multiplier, won FROM ascent_faction_weeks WHERE faction=$1",
        name)
    assert row["won"] and row["multiplier"] == pytest.approx(1.75)
    _, _, doc = await _money(pool, "tenant-a", pa)
    buff = doc.get("faction_buff")
    assert buff and buff["kind"] == "hp"
    assert buff["pct"] == round(0.15 * 1.75 * 100)   # 26%
    assert buff["week"] == factions.world_week()      # live THIS week


async def test_board_shows_winners_and_rankings(client, tenant_a, tenant_b,
                                                clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Boarda")
    pb = await create_player(client, tenant_b, "tenant-b", "Boardb")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 200)
    name = _name()
    await post(client, tenant_a, "tenant-a", "/v1/faction/create",
               {"player": pa, "name": name, "banner": "iron_heart",
                "join_fee": 0, "weekly_dues": 5})
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
               {"player": pb, "faction": name})
    await _seed_last_week(
        pool, name, [("tenant-a", pa), ("tenant-b", pb)],
        "hoard", 100, [4, 4], kill_gold=100, kills=2)

    # the board resolves pending weeks itself — no status call needed
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/board",
                   {"player": pb})
    assert r.status_code == 200
    b = r.json()
    week = factions.world_week()
    assert b["week"] == week
    assert b["challenge"]["kind"] == factions.week_kind(week)
    last = [w for w in b["last_week"] if w["faction"] == name]
    assert last and last[0]["won"]
    assert b["wins"] and b["wins"][0]["faction"] == name
    assert any(f["name"] == name for f in b["most_members"])
    assert any(f["name"] == name for f in b["richest"])
    assert any(f["name"] == name for f in b["highest"])
    assert b["banners"][name] == "iron_heart"
    assert any("won the week" in t for t in b["ticker"])


async def test_board_renders_sane_with_zero_factions(client, tenant_a,
                                                     clean_factions):
    pa = await create_player(client, tenant_a, "tenant-a", "Lonely")
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/board",
                   {"player": pa})
    assert r.status_code == 200
    b = r.json()
    assert b["last_week"] == [] and b["wins"] == []
    assert b["most_members"] == [] and b["banners"] == {}
    assert b["challenge"]["kind"] in factions.GOAL_KINDS
