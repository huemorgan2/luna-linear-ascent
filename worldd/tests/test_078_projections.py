"""078 Phase 1 — projection columns and the de-fatted social reads.

The law under test: every value a hot query filters or sorts on is a
GENERATED column Postgres maintains from the doc — the doc itself is
never the thing a scan parses. A raw doc write (no column mention) must
still land the right projections, or every rewritten reader lies.
"""

import json

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402


def _doc(**kw):
    d = {"stage": "playing", "name": "Projo", "race": "human",
         "clazz": "warrior", "level": 7, "floor": 3, "unlocked_floor": 5,
         "gold": 120, "bank": 900, "guild": "Oakline",
         "location": "gate_town", "lodged_until_day": 4, "gear": {},
         "energy_val": 10, "energy_ts": "2026-01-01T00:00:00+00:00"}
    d.update(kw)
    return d


async def _put(pool, player, doc):
    await pool.execute(
        "INSERT INTO ascent_tenants (tenant, secret) VALUES ('t078', 's') "
        "ON CONFLICT (tenant) DO NOTHING")
    await pool.execute(
        "INSERT INTO ascent_players (tenant, player, doc) "
        "VALUES ('t078', $1, $2) ON CONFLICT (tenant, player) "
        "DO UPDATE SET doc = EXCLUDED.doc, updated_at = now()",
        player, json.dumps(doc))


async def _cleanup(pool):
    await pool.execute("DELETE FROM ascent_players WHERE tenant='t078'")


async def test_generated_columns_follow_the_doc(client):
    pool = await db.get_pool()
    await _cleanup(pool)
    await _put(pool, "p1", _doc(sleeping={"where": "lodge"}))
    row = await pool.fetchrow(
        "SELECT stage, name, race, clazz, guild, location, floor,"
        " unlocked_floor, level, gold, bank, lodged_until_day, sleeping "
        "FROM ascent_players WHERE tenant='t078' AND player='p1'")
    assert dict(row) == {
        "stage": "playing", "name": "Projo", "race": "human",
        "clazz": "warrior", "guild": "Oakline", "location": "gate_town",
        "floor": 3, "unlocked_floor": 5, "level": 7, "gold": 120,
        "bank": 900, "lodged_until_day": 4, "sleeping": True}
    # a plain doc UPDATE moves the projections with it
    await _put(pool, "p1", _doc(level=9, floor=0, stage="dead"))
    row = await pool.fetchrow(
        "SELECT stage, level, floor, sleeping FROM ascent_players "
        "WHERE tenant='t078' AND player='p1'")
    # floor 0 projects as 1 (town counts as Roothollow's floor)
    assert dict(row) == {"stage": "dead", "level": 9, "floor": 1,
                         "sleeping": False}
    # absent keys project to their documented defaults
    await _put(pool, "p2", {"stage": "playing"})
    row = await pool.fetchrow(
        "SELECT name, floor, unlocked_floor, level, gold, bank,"
        " lodged_until_day, sleeping FROM ascent_players "
        "WHERE tenant='t078' AND player='p2'")
    assert dict(row) == {"name": None, "floor": 1, "unlocked_floor": 1,
                         "level": 1, "gold": 0, "bank": 0,
                         "lodged_until_day": -1, "sleeping": False}
    await _cleanup(pool)


async def test_phase1_indexes_exist(client):
    pool = await db.get_pool()
    names = {r["indexname"] for r in await pool.fetch(
        "SELECT indexname FROM pg_indexes "
        "WHERE tablename IN ('ascent_players', 'ascent_faction_ledger',"
        " 'ascent_warden_damage', 'ascent_armory')")}
    for want in ("ix_players_playing_updated", "ix_players_playing_floor",
                 "ix_players_playing_name", "ix_players_playing_roster",
                 "ix_faction_ledger_giver", "ix_warden_damage_giver",
                 "ix_armory_donor"):
        assert want in names, f"missing index {want}"


async def test_roster_ranks_bank_over_the_whole_roll(client):
    pool = await db.get_pool()
    await _cleanup(pool)
    # 14 climbers: floors 1..14, bank inversely — the top-floor board
    # entry must still carry its bank rank computed over ALL 14.
    for i in range(1, 15):
        await _put(pool, f"r{i}", _doc(
            name=f"Roster{i}", unlocked_floor=i, level=i, bank=1000 - i))
    async with pool.acquire() as conn:
        entries, total = await social._roster(conn)
    assert total >= 14
    assert len(entries) == 12
    mine = [e for e in entries if e["name"].startswith("Roster")]
    top = mine[0]
    assert top["name"] == "Roster14"
    assert top["floor"] == 14
    # Roster14 has the LOWEST bank of the fourteen → worst rank among them
    r1 = next(e for e in entries if e["name"] == "Roster13")
    assert top["bank_rank"] > r1["bank_rank"]
    assert "bank" not in top          # rank is public, balance is not
    assert top["power"] > 0
    await _cleanup(pool)


async def test_pvp_targets_filter_in_sql(client):
    pool = await db.get_pool()
    await _cleanup(pool)
    from plugin_linear_ascent import economy
    day = 10_000  # far future — nobody's lodge reaches it
    lv = economy.BEGINNER_PROTECTION_MAX_LEVEL
    await _put(pool, "open1", _doc(name="Open1", level=lv + 1,
                                   lodged_until_day=-1))
    await _put(pool, "lodged", _doc(name="Lodged", level=lv + 1,
                                    lodged_until_day=day + 5))
    await _put(pool, "green", _doc(name="Green", level=lv,
                                   lodged_until_day=-1))
    async with pool.acquire() as conn:
        out = await social._pvp_targets(conn, "t078", "viewer", {}, day)
    names = [o["name"] for o in out]
    assert "Open1" in names
    assert "Lodged" not in names and "Green" not in names
    await _cleanup(pool)


async def test_leaderboard_is_projected_and_ordered(client):
    pool = await db.get_pool()
    await _cleanup(pool)
    await _put(pool, "lb1", _doc(name="Rich", level=9, gold=5, bank=5000))
    await _put(pool, "lb2", _doc(name="Poor", level=9, gold=1, bank=0))
    await _put(pool, "lb3", _doc(name="High", level=20, gold=0, bank=0))
    async with pool.acquire() as conn:
        board = await social.leaderboard(conn, "t078", "lb2")
    rows = [p for p in board["players"]
            if p["name"] in ("Rich", "Poor", "High")]
    assert [p["name"] for p in rows] == ["High", "Rich", "Poor"]
    me = next(p for p in rows if p["name"] == "Poor")
    assert me["you"] is True
    assert board["total"] >= 3
    await _cleanup(pool)


async def test_rooms_ride_the_narrow_doc(client):
    pool = await db.get_pool()
    await _cleanup(pool)
    await _put(pool, "rm1", _doc(name="Roomer", location="gate_town",
                                 floor=2))
    async with pool.acquire() as conn:
        rooms, counts = await social._rooms(conn)
    tiles = rooms.get("gate_town:2") or []
    tile = next(t for t in tiles if t["name"] == "Roomer")
    assert tile["opt"] == "pv:Roomer"
    assert tile["level"] == 7 and tile["race"] == "human"
    assert tile["energy"] >= 0 and tile["sleeping"] is False
    assert counts["gate_town:2"] >= 1
    await _cleanup(pool)
