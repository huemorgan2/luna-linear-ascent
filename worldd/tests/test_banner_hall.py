"""032 — the banner hall (real DB): the coffer's brim, the works, the
bunks, the bulletin board, the chest's bought slots.

The laws under test: every coffer inflow clips to the cap (nothing is
ever burned out of a member's pocket by a full coffer); the works are
steward-only, coffer-paid, one tier at a time; a bed claim is a free
safe night setting the SAME lodged_until_day flag the Lodge sells; one
note per member per world-day (same day replaces).
"""

import json
import uuid

import pytest

from app import armory, db, factions
from plugin_linear_ascent.engine import state as pstate
from tests.test_factions import (_money, _set_money,  # noqa: F401
                                 _treasury, clean_factions, post,
                                 tenant_a, tenant_b)
from tests.test_multiplayer import create_player


@pytest.fixture
async def clean_hall(client, clean_factions):  # noqa: F811
    pool = await db.get_pool()

    async def wipe():
        await pool.execute("DELETE FROM ascent_faction_bed_claims")
        await pool.execute("DELETE FROM ascent_faction_notes")
        await pool.execute("DELETE FROM ascent_armory")
        await pool.execute("DELETE FROM ascent_armory_takes")
    await wipe()
    yield
    await wipe()


def _name():
    return f"Hall {uuid.uuid4().hex[:6]}"


async def _crew(client, pool, sa, sb, join_fee=0):
    """A two-member banner: steward pa (tenant-a), member pb (tenant-b)."""
    pa = await create_player(client, sa, "tenant-a", "Stew")
    pb = await create_player(client, sb, "tenant-b", "Hand")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 2000)
    name = _name()
    r = await post(client, sa, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl",
                    "join_fee": join_fee, "weekly_dues": 5})
    assert r.status_code == 200, r.text
    r = await post(client, sb, "tenant-b", "/v1/faction/join",
                   {"player": pb, "faction": name})
    assert r.status_code == 200, r.text
    return pa, pb, name


async def _doc(pool, tenant, player):
    return json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player))


def test_tier_to_fit_is_the_grandfathering_rule():
    """Migration 011 sets coffer/chest tiers to the smallest tier whose
    cap covers what the faction already holds — this helper IS that rule."""
    caps = factions.COFFER_CAPS
    assert factions.tier_to_fit(0, caps) == 1
    assert factions.tier_to_fit(200, caps) == 1     # at the brim still fits
    assert factions.tier_to_fit(201, caps) == 2
    assert factions.tier_to_fit(600, caps) == 2
    assert factions.tier_to_fit(2500, caps) == 3
    assert factions.tier_to_fit(8000, caps) == 4
    # over the top cap: grandfathered onto the top tier, never truncated
    assert factions.tier_to_fit(12000, caps) == 4
    slots = factions.CHEST_SLOTS
    assert factions.tier_to_fit(4, slots) == 1
    assert factions.tier_to_fit(5, slots) == 2
    assert factions.tier_to_fit(50, slots) == 4     # the old flat roof


async def test_donation_clips_at_the_brim(client, tenant_a, tenant_b,
                                          clean_hall):
    """A tier-1 coffer holds ◈200: a donation over the brim is taken
    only up to it — the rest never leaves the donor's pocket — and a
    full coffer refuses outright."""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    await pool.execute(
        "UPDATE ascent_factions SET treasury=163 WHERE name=$1", name)
    await _set_money(pool, "tenant-b", pb, 100)

    r = await post(client, tenant_b, "tenant-b", "/v1/faction/donate",
                   {"player": pb, "amount": 100})
    assert r.status_code == 200
    assert await _treasury(pool, name) == factions.COFFER_CAPS[1]  # 200
    gold_b, _, _ = await _money(pool, "tenant-b", pb)
    assert gold_b == 100 - 37                      # only ◈37 fit, only ◈37 left
    led = await pool.fetchval(
        "SELECT gold FROM ascent_ledger WHERE kind='faction_donation' "
        "AND player=$1", pb)
    assert led == -37                              # the row says what moved
    store = await pool.fetchval(
        "SELECT amount FROM ascent_faction_ledger WHERE faction=$1 "
        "AND kind='donation'", name)
    assert store == 37

    # brim-full: the donation is refused, nothing moves
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/donate",
                   {"player": pb, "amount": 10})
    assert r.status_code == 409 and "full" in r.json()["detail"]
    gold_b, _, _ = await _money(pool, "tenant-b", pb)
    assert gold_b == 63
    assert await _treasury(pool, name) == 200


async def test_join_fee_clips_at_the_brim(client, tenant_a, tenant_b,
                                          clean_hall):
    """The join fee is an inflow like any other — a nearly-full coffer
    charges the joiner only what fits."""
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Stew")
    await _set_money(pool, "tenant-a", pa, 2000)
    name = _name()
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl",
                    "join_fee": 50, "weekly_dues": 5})
    assert r.status_code == 200, r.text
    await pool.execute(
        "UPDATE ascent_factions SET treasury=190 WHERE name=$1", name)
    pb = await create_player(client, tenant_b, "tenant-b", "Joiner")
    await _set_money(pool, "tenant-b", pb, 60)
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/join",
                   {"player": pb, "faction": name})
    assert r.status_code == 200, r.text
    assert await _treasury(pool, name) == 200      # +10, the space left
    gold_b, bank_b, _ = await _money(pool, "tenant-b", pb)
    assert (gold_b, bank_b) == (50, 0)             # charged ◈10, not ◈50


async def test_dues_clip_at_the_brim_without_arrears(
        client, tenant_a, tenant_b, clean_hall):
    """Dues that don't fit are simply not charged — a full coffer is
    never the member's debt, so no arrears either."""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    from tests.test_factions import _seed_last_week
    await _seed_last_week(
        pool, name, [("tenant-a", pa), ("tenant-b", pb)],
        "hoard", 100, [4, 4], kill_gold=100, kills=2)
    # dues are ◈5 × 2 members but only ◈7 of space remains under the cap
    await pool.execute(
        "UPDATE ascent_factions SET treasury=193 WHERE name=$1", name)
    await post(client, tenant_a, "tenant-a", "/v1/faction/status",
               {"player": pa})
    assert await _treasury(pool, name) == 200      # 5 + 2, clipped at the brim
    dues = await pool.fetch(
        "SELECT amount FROM ascent_faction_ledger WHERE faction=$1 AND "
        "kind='dues' ORDER BY id", name)
    # rows say what moved: one full ◈5, then only the ◈2 that fit
    assert sorted(r["amount"] for r in dues) == [2, 5]
    arrears = await pool.fetch(
        "SELECT arrears FROM ascent_faction_members WHERE faction=$1", name)
    assert not any(r["arrears"] for r in arrears)


async def test_room_buy_steward_only_short_and_skipped(
        client, tenant_a, tenant_b, clean_hall):
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    async with pool.acquire() as conn:
        # a member is not the steward
        err = await factions.buy_room(conn, "tenant-b", pb)
        assert err and "steward" in err
        # coffer short: refused with the shortfall shown
        err = await factions.buy_room(conn, "tenant-a", pa)
        assert err and "short" in err
        # tier skipped: one at a time, never conjured
        await pool.execute(
            "UPDATE ascent_factions SET treasury=6000 WHERE name=$1", name)
        err = await factions.buy_room(conn, "tenant-a", pa, tier=3)
        assert err and "one tier at a time" in err
        # the honest buy lands: tier up, coffer down, works_* ledgered
        err = await factions.buy_room(conn, "tenant-a", pa, tier=2)
        assert err is None
    row = await pool.fetchrow(
        "SELECT room_tier, treasury FROM ascent_factions WHERE name=$1",
        name)
    assert row["room_tier"] == 2
    assert row["treasury"] == 6000 - factions.ROOM_PRICES[2]
    led = await pool.fetchrow(
        "SELECT kind, amount FROM ascent_faction_ledger WHERE faction=$1 "
        "AND kind='works_room'", name)
    assert led["amount"] == -factions.ROOM_PRICES[2]
    # never downgraded, never re-bought
    async with pool.acquire() as conn:
        err = await factions.buy_room(conn, "tenant-a", pa, tier=2)
        assert err and "one tier at a time" in err


async def test_top_tiers_refuse_politely(client, tenant_a, tenant_b,
                                         clean_hall):
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    await pool.execute(
        "UPDATE ascent_factions SET room_tier=4, coffer_tier=4,"
        " chest_tier=4, treasury=8000 WHERE name=$1", name)
    async with pool.acquire() as conn:
        assert "grander" in await factions.buy_room(conn, "tenant-a", pa)
        assert "deep" in await factions.buy_coffer(conn, "tenant-a", pa)
        assert "big" in await factions.buy_chest(conn, "tenant-a", pa)


async def test_bed_claims_capacity_one_per_night_and_lodging(
        client, tenant_a, tenant_b, clean_hall):
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    day = pstate.world_day()
    async with pool.acquire() as conn:
        # no beds in a back room — and none bought yet
        doc_a = await _doc(pool, "tenant-a", pa)
        err = await factions.claim_bed(conn, "tenant-a", pa, doc_a)
        assert err and "no bunks" in err
        err = await factions.buy_bed(conn, "tenant-a", pa)
        assert err and "fits no beds" in err
        # room 2 fits 2: buy one bed (◈250 from the coffer), refuse a 3rd
        await pool.execute(
            "UPDATE ascent_factions SET room_tier=2, treasury=500 "
            "WHERE name=$1", name)
        assert await factions.buy_bed(conn, "tenant-a", pa) is None
        assert await factions.buy_bed(conn, "tenant-a", pa) is None
        err = await factions.buy_bed(conn, "tenant-a", pa)
        assert err and "fits 2 beds" in err
    assert await _treasury(pool, name) == 0        # 2 × ◈250, burned
    bed_led = await pool.fetch(
        "SELECT amount FROM ascent_faction_ledger WHERE faction=$1 AND "
        "kind='works_bed'", name)
    assert [r["amount"] for r in bed_led] == [-250, -250]

    # a third member so the second bed can be contested
    pc = await create_player(client, tenant_b, "tenant-b", "Third")
    await post(client, tenant_b, "tenant-b", "/v1/faction/join",
               {"player": pc, "faction": name})
    async with pool.acquire() as conn:
        doc_a = await _doc(pool, "tenant-a", pa)
        assert await factions.claim_bed(conn, "tenant-a", pa, doc_a) is None
        # the claim IS the Lodge's flag — free
        assert doc_a["lodged_until_day"] == day + 1
        # one bunk per member per night
        err = await factions.claim_bed(conn, "tenant-a", pa, doc_a)
        assert err and "already" in err
        doc_b = await _doc(pool, "tenant-b", pb)
        assert await factions.claim_bed(conn, "tenant-b", pb, doc_b) is None
        # both bunks taken: the third member bounces, flag untouched
        doc_c = await _doc(pool, "tenant-b", pc)
        lodged_before = doc_c.get("lodged_until_day")
        err = await factions.claim_bed(conn, "tenant-b", pc, doc_c)
        assert err and "every bunk is claimed" in err
        assert doc_c.get("lodged_until_day") == lodged_before
    claims = await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_bed_claims "
        "WHERE faction=$1 AND world_day=$2", name, day)
    assert claims == 2


async def test_note_upserts_on_the_day_key(client, tenant_a, tenant_b,
                                           clean_hall):
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    async with pool.acquire() as conn:
        # a member writes; writing again the same day replaces the line
        assert await factions.write_note(
            conn, "tenant-b", pb, "dues land tonight, pay up") is None
        assert await factions.write_note(
            conn, "tenant-b", pb, "the hat is passed — ◈30 to go") is None
        # a long line is clipped to the board's 64 characters
        assert await factions.write_note(
            conn, "tenant-a", pa, "x" * 100) is None
        # an empty line is not a note
        err = await factions.write_note(conn, "tenant-a", pa, "   ")
        assert err and "one line" in err
        # no banner, no board
        loner = await create_player(client, tenant_b, "tenant-b", "Loner")
        err = await factions.write_note(conn, "tenant-b", loner, "hello")
        assert err and "no faction" in err
    rows = await pool.fetch(
        "SELECT player, line, world_day FROM ascent_faction_notes "
        "WHERE faction=$1 ORDER BY id", name)
    assert len(rows) == 2                          # one row per member per day
    by_player = {r["player"]: r for r in rows}
    assert by_player[pb]["line"] == "the hat is passed — ◈30 to go"
    assert len(by_player[pa]["line"]) == factions.NOTE_MAX_CHARS
    assert all(r["world_day"] == pstate.world_day() for r in rows)


async def test_chest_slot_cap_and_bought_slots(client, tenant_a, tenant_b,
                                               clean_hall):
    """A tier-1 chest holds 4; the 5th is refused; a bought tier opens
    slots on the spot. (The full engine round-trip lives in
    test_armory.py — this is the worldd guard.)"""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    from tests.test_armory import armory_seed
    for _ in range(factions.CHEST_SLOTS[1]):
        await armory_seed(pool, name, "pigsticker")
    doc_a = await _doc(pool, "tenant-a", pa)
    doc_a.setdefault("inventory", {})["wolfbite"] = 1
    async with pool.acquire() as conn:
        err = await armory.deposit(conn, "tenant-a", pa, doc_a,
                                   "wolfbite", None)
        assert err and "chest is full" in err
        # the works sell a bigger one — 8 slots now, the piece racks
        await pool.execute(
            "UPDATE ascent_factions SET treasury=200 WHERE name=$1", name)
        assert await factions.buy_chest(conn, "tenant-a", pa) is None
        assert await armory.slot_cap(conn, name) == factions.CHEST_SLOTS[2]
        err = await armory.deposit(conn, "tenant-a", pa, doc_a,
                                   "wolfbite", None)
        assert err is None
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_armory WHERE faction=$1", name) == 5


async def test_status_and_detail_carry_the_hall(client, tenant_a, tenant_b,
                                                clean_hall):
    """The panel's `hall` key (what the scene injection rides) and the
    detail page's member/outsider split."""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    async with pool.acquire() as conn:
        await factions.write_note(conn, "tenant-b", pb, "first words")
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                   {"player": pa})
    hall = r.json()["hall"]
    assert hall["room_tier"] == 1
    assert hall["room_name"] == "the back room"
    assert hall["coffer"] == {"bal": 0, "cap": 200, "tier": 1}
    assert hall["chest"] == {"used": 0, "cap": 4, "tier": 1}
    assert hall["beds"] == {"count": 0, "tonight": []}
    assert hall["notes"][0]["line"] == "first words"
    assert hall["notes"][0]["player"] == "Hand"
    works = {w["kind"]: w for w in hall["works"]}
    assert works["room"]["price"] == 500 and not works["room"]["affordable"]
    assert works["coffer"]["price"] == 120
    assert works["chest"]["price"] == 150
    assert "bed" not in works                      # the back room fits none

    # members see the house; outsiders see the room tier and no board
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/detail",
                   {"player": pb, "name": name})
    d = r.json()
    assert d["room_tier"] == 1 and d["hall"]["notes"]
    loner = await create_player(client, tenant_a, "tenant-a", "Walkin")
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/detail",
                   {"player": loner, "name": name})
    d = r.json()
    assert d["room_tier"] == 1
    assert "notes" not in d["hall"] and "coffer" not in d["hall"]


async def test_hall_board_mirrors_the_wall(client, tenant_a, tenant_b,
                                           clean_hall):
    """The trimmed board scenes carry: this week's standings (entered
    banners, live progress) and the hall of banners sorted by wins."""
    pool = await db.get_pool()
    pa, pb, name = await _crew(client, pool, tenant_a, tenant_b)
    await pool.execute(
        "UPDATE ascent_factions SET treasury=100, room_tier=2 "
        "WHERE name=$1", name)
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/enter",
                   {"player": pa})
    assert r.status_code == 200, r.text
    async with pool.acquire() as conn:
        hb = await factions.hall_board(conn)
    assert hb["week"] == factions.world_week()
    assert hb["kind"] == factions.week_kind(hb["week"])
    stand = [s for s in hb["standings"] if s["name"] == name]
    assert stand and stand[0]["target"] > 0
    assert stand[0]["banner"] == "wolf_howl"
    assert stand[0]["progress"] >= 0
    tile = next(b for b in hb["banners"] if b["name"] == name)
    assert tile == {"name": name, "banner": "wolf_howl", "wins": 0,
                    "members": 2, "room_tier": 2}
