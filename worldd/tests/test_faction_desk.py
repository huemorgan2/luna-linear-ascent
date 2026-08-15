"""015 — the faction desk: requests, rename, promote, gates (real DB).

Joining is a REQUEST an admin accepts (fee charged at accept) or rejects.
Founding takes level 4+. Admins (multiple stewards) run the desk; the
founder is a permanent badge and the only one who can unseat an admin.
"""

import uuid

import pytest

from app import db, factions
from tests.test_factions import _money, _set_money, post
from tests.test_factions import clean_factions, tenant_a, tenant_b  # noqa: F401
from tests.test_multiplayer import create_player


def _name():
    return f"Desk {uuid.uuid4().hex[:6]}"


async def _found(client, secret, tenant, player, name, join_fee=25):
    r = await post(client, secret, tenant, "/v1/faction/create",
                   {"player": player, "name": name, "banner": "wolf_howl",
                    "join_fee": join_fee, "weekly_dues": 5})
    assert r.status_code == 200, r.text
    return name


async def test_create_needs_level_four(client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Green")
    await _set_money(pool, "tenant-a", pa, 2000, level=3)
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": _name(), "banner": "wolf_howl"})
    assert r.status_code == 403 and "level 4" in r.json()["detail"]
    # rank up → the charter opens
    await _set_money(pool, "tenant-a", pa, 2000, level=4)
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": _name(), "banner": "wolf_howl"})
    assert r.status_code == 200


async def test_request_approve_charges_fee_once(client, tenant_a, tenant_b,
                                                clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Deska")
    pb = await create_player(client, tenant_b, "tenant-b", "Askin")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 10, bank=40)
    name = await _found(client, tenant_a, "tenant-a", pa, _name())

    # the ask: no gold moves, no membership yet
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/request",
                   {"player": pb, "name": name})
    assert r.status_code == 200
    gold_b, bank_b, _ = await _money(pool, "tenant-b", pb)
    assert (gold_b, bank_b) == (10, 40)
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_members WHERE player=$1",
        pb) == 0

    # the admin sees the queue on the faction page
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/detail",
                   {"player": pa, "name": name})
    d = r.json()
    assert d["viewer"]["admin"] and d["viewer"]["founder"]
    assert [q["player"] for q in d["requests"]] == [pb]

    # accept: fee ◈25 charged gold-first-then-bank, member seated
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/approve",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 200
    gold_b, bank_b, _ = await _money(pool, "tenant-b", pb)
    assert (gold_b, bank_b) == (0, 25)
    tre = await pool.fetchval(
        "SELECT treasury FROM ascent_factions WHERE name=$1", name)
    assert tre == 25
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/detail",
                   {"player": pa, "name": name})
    d = r.json()
    assert d["requests"] == []
    assert sorted(m["player"] for m in d["members"]) == sorted([pa, pb])

    # double approve: the request is gone
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/approve",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code in (403, 409)


async def test_approve_broke_requester_keeps_request(
        client, tenant_a, tenant_b, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Deskb")
    pb = await create_player(client, tenant_b, "tenant-b", "Skint")
    await _set_money(pool, "tenant-a", pa, 2000)
    name = await _found(client, tenant_a, "tenant-a", pa, _name(),
                        join_fee=100)
    await _set_money(pool, "tenant-b", pb, 5, bank=0, level=1)
    await post(client, tenant_b, "tenant-b", "/v1/faction/request",
               {"player": pb, "name": name})
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/approve",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 409 and "join fee" in r.json()["detail"]
    # the request stays for when they can pay
    n = await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_requests WHERE player=$1", pb)
    assert n == 1


async def test_reject_and_withdraw(client, tenant_a, tenant_b,
                                   clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Deskc")
    pb = await create_player(client, tenant_b, "tenant-b", "Nope")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 500, level=1)
    name = await _found(client, tenant_a, "tenant-a", pa, _name())

    await post(client, tenant_b, "tenant-b", "/v1/faction/request",
               {"player": pb, "name": name})
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/reject",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 200
    n = await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_requests WHERE player=$1", pb)
    assert n == 0
    gold_b, _, _ = await _money(pool, "tenant-b", pb)
    assert gold_b == 500                        # no gold ever moved

    # ask again, change your mind
    await post(client, tenant_b, "tenant-b", "/v1/faction/request",
               {"player": pb, "name": name})
    r = await post(client, tenant_b, "tenant-b",
                   "/v1/faction/cancel_request", {"player": pb})
    assert r.status_code == 200
    n = await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_requests WHERE player=$1", pb)
    assert n == 0

    # a non-admin can't work the desk
    pc = await create_player(client, tenant_b, "tenant-b", "Peon")
    await post(client, tenant_b, "tenant-b", "/v1/faction/request",
               {"player": pc, "name": name})
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/approve",
                   {"player": pb, "target_tenant": "tenant-b",
                    "target_player": pc})
    assert r.status_code == 403


async def test_rename_carries_members_wins_and_ledger(
        client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Namer")
    await _set_money(pool, "tenant-a", pa, 2000)
    old = await _found(client, tenant_a, "tenant-a", pa, _name())
    await pool.execute(
        "INSERT INTO ascent_faction_weeks (faction, week, goal_kind,"
        " goal_target, entered, resolved, won) "
        "VALUES ($1, $2, 'hoard', 10, true, true, true)",
        old, factions.world_week() - 1)

    new = _name()
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/rename",
                   {"player": pa, "name": new})
    assert r.status_code == 200
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_factions WHERE name=$1", new) == 1
    assert await pool.fetchval(
        "SELECT faction FROM ascent_faction_members WHERE player=$1",
        pa) == new
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_faction_weeks WHERE faction=$1 "
        "AND won", new) == 1

    # invalid names refused inline (NAME_RE: 3–24, sane charset)
    for bad in ("x", "!!bad!!"):
        r = await post(client, tenant_a, "tenant-a", "/v1/faction/rename",
                       {"player": pa, "name": bad})
        assert r.status_code == 409, bad


async def test_promote_and_founder_kick_rules(client, tenant_a, tenant_b,
                                              clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Frst")
    pb = await create_player(client, tenant_b, "tenant-b", "Scnd")
    pc = await create_player(client, tenant_b, "tenant-b", "Thrd")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 500, level=1)
    await _set_money(pool, "tenant-b", pc, 500, level=1)
    name = await _found(client, tenant_a, "tenant-a", pa, _name(),
                        join_fee=0)
    for p in (pb, pc):
        await post(client, tenant_b, "tenant-b", "/v1/faction/request",
                   {"player": p, "name": name})
        await post(client, tenant_a, "tenant-a", "/v1/faction/approve",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": p})

    # founder promotes B to admin
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/promote",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 200
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/detail",
                   {"player": pb, "name": name})
    d = r.json()
    assert d["viewer"]["admin"] and not d["viewer"]["founder"]
    roles = {m["player"]: (m["role"], m["founder"]) for m in d["members"]}
    assert roles[pa] == ("steward", True)      # founder badge stays put
    assert roles[pb] == ("steward", False)

    # the new admin can kick a member…
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/kick",
                   {"player": pb, "target_tenant": "tenant-b",
                    "target_player": pc})
    assert r.status_code == 200
    # …but not the founder-admin
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/kick",
                   {"player": pb, "target_tenant": "tenant-a",
                    "target_player": pa})
    assert r.status_code == 403 and "founder" in r.json()["detail"]
    # the founder CAN unseat an admin
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/kick",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 200


async def test_list_search_and_top10(client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Lister")
    await _set_money(pool, "tenant-a", pa, 20000)
    # seed 12 factions straight into the table (only one has members)
    mine = await _found(client, tenant_a, "tenant-a", pa,
                        "Wolfpack Prime", join_fee=0)
    for i in range(11):
        await pool.execute(
            "INSERT INTO ascent_factions (name) VALUES ($1)",
            f"Filler {i:02d}")
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/list",
                   {"player": pa})
    d = r.json()
    # 059: the ledger is the "all factions" page — 50 a page, not 10
    assert d["total"] == 12 and len(d["factions"]) == 12
    assert factions.BROWSE_LIMIT == 50
    assert d["factions"][0]["name"] == mine     # most members first
    assert d["found_min_level"] == factions.FOUND_MIN_LEVEL

    r = await post(client, tenant_a, "tenant-a", "/v1/faction/list",
                   {"player": pa, "q": "wolf"})
    d = r.json()
    assert [f["name"] for f in d["factions"]] == [mine]


async def test_status_panel_carries_desk_fields(client, tenant_a, tenant_b,
                                                clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Panel")
    pb = await create_player(client, tenant_b, "tenant-b", "Waits")
    await _set_money(pool, "tenant-a", pa, 2000)
    await _set_money(pool, "tenant-b", pb, 500, level=1)
    name = await _found(client, tenant_a, "tenant-a", pa, _name())
    await post(client, tenant_b, "tenant-b", "/v1/faction/request",
               {"player": pb, "name": name})
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/status",
                   {"player": pa})
    s = r.json()
    assert s["pending_requests"] == 1
    assert s["members"][0]["founder"] is True
