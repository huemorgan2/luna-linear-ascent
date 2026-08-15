"""059 — the faction block under the profile.

members_of marks a member online when they acted inside the presence
window while playing, and not otherwise; the member's Guildhall panel
carries members_count and online for the profile block; the browse
ledger lists up to 50 factions.
"""

import json
import uuid

from app import gamepath

gamepath.ensure_game_importable()

from app import db, factions, social  # noqa: E402


def _doc(name: str) -> str:
    return json.dumps({"stage": "playing", "name": name, "level": 3,
                       "gear": {}, "floor": 1, "gold": 0, "xp": 0,
                       "guild": ""})


async def test_members_of_marks_online_inside_the_window(client):
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    fac = f"Block {tag}"
    ten = f"t-blk-{tag}"
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO ascent_tenants (tenant, secret) VALUES ($1,'s') "
            "ON CONFLICT DO NOTHING", ten)
        try:
            await conn.execute(
                "INSERT INTO ascent_factions (name) VALUES ($1) "
                "ON CONFLICT DO NOTHING", fac)
            for who, mins in (("fresh", 0), ("stale", 30)):
                await conn.execute(
                    "INSERT INTO ascent_players (tenant, player, doc,"
                    " updated_at) VALUES ($1,$2,$3::jsonb,"
                    " now() - make_interval(mins => $4))",
                    ten, who, _doc(who), mins)
                await conn.execute(
                    "INSERT INTO ascent_faction_members (tenant, player,"
                    " faction) VALUES ($1,$2,$3)", ten, who, fac)
            members = await factions.members_of(conn, fac)
            by = {m["player"]: m for m in members}
            assert by["fresh"]["online"] is True
            assert by["stale"]["online"] is False

            panel = await social._faction_panel(conn, ten, "fresh", fac)
            assert panel["members_count"] == 2
            assert panel["online"] == 1
            assert {m["name"]: m["online"] for m in panel["members"]} == {
                "fresh": True, "stale": False}
        finally:
            await conn.execute(
                "DELETE FROM ascent_faction_members WHERE tenant=$1", ten)
            await conn.execute(
                "DELETE FROM ascent_players WHERE tenant=$1", ten)
            await conn.execute(
                "DELETE FROM ascent_factions WHERE name=$1", fac)


async def test_browse_lists_fifty(client):
    assert factions.BROWSE_LIMIT == 50
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        d = await factions.browse(conn, "t-none", "nobody", "")
    assert d["total"] >= len(d["factions"])
    assert len(d["factions"]) <= 50
