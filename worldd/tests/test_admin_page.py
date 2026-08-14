"""The admin desk — /admin console, player list/search/edit, grants,
the feedback tab and the ADMINS tab. The only door is a site session
whose username is on the approved-admins list; there is no key."""

from __future__ import annotations

import json
import uuid

import pytest

from app import db
from tests.test_051_feedback import fb
from tests.test_social_api import create, get_doc
from tests.test_world_api import make_tenant


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


def _p(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def _wipe_user(name: str) -> None:
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_names WHERE name_lower=$1", name)
    await pool.execute(
        "DELETE FROM ascent_accounts WHERE lower(username)=$1", name)
    await pool.execute(
        "DELETE FROM ascent_players WHERE tenant='web' AND player=$1", name)


async def _sign_in(client, name: str) -> None:
    """A session for `name` — signup, or login when the account holds."""
    from tests.test_web_play import PW
    r = await client.post("/login", json={
        "username": name, "password": PW, "password2": PW})
    if r.status_code != 200:
        from tests.test_web_play import _signup
        await _signup(client, name)


@pytest.fixture
async def desk(client):
    """The signed-in approved admin — huemorgan3 rides the seed list.
    The table is wiped first so the env seed re-applies clean."""
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_admins")
    await _sign_in(client, "huemorgan3")
    yield client
    client.cookies.clear()


async def test_admin_session_is_the_only_door(client):
    """huemorgan3's site session opens the desk; a stranger's does not."""
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_admins")
    for name in ("huemorgan3", "stranger77"):
        await _wipe_user(name)

    await _sign_in(client, "stranger77")
    r = await client.get("/admin/api/players")
    assert r.status_code == 401
    client.cookies.clear()

    await _sign_in(client, "huemorgan3")
    r = await client.get("/admin/api/players")
    assert r.status_code == 200
    r = await client.get("/admin/api/feedback")
    assert r.status_code == 200
    client.cookies.clear()


async def test_page_serves_and_the_desk_wants_a_session(client):
    r = await client.get("/admin")
    assert r.status_code == 200 and "ADMIN" in r.text
    r = await client.get("/admin/api/players")
    assert r.status_code == 401
    # the retired key convinces nobody
    r = await client.get("/admin/api/players",
                         headers={"X-Admin-Key": "test-admin-key"})
    assert r.status_code == 401


async def test_admins_tab_lists_adds_and_removes(client):
    """The ADMINS tab: the seed list shows, a name added walks in the
    moment it lands, a removed name is out, the last admin stays."""
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_admins")
    for name in ("huemorgan3", "stranger77"):
        await _wipe_user(name)

    await _sign_in(client, "huemorgan3")
    r = await client.get("/admin/api/admins")
    assert r.status_code == 200
    d = r.json()
    assert d["you"] == "huemorgan3"
    assert "huemorgan3" in {a["name"] for a in d["admins"]}

    r = await client.post("/admin/api/admins",
                          json={"name": "Stranger77"})
    assert r.status_code == 200 and r.json()["name"] == "stranger77"
    client.cookies.clear()

    # the fresh admin's own session now opens the desk
    await _sign_in(client, "stranger77")
    r = await client.get("/admin/api/players")
    assert r.status_code == 200
    # ... and can hand the keys back
    r = await client.post("/admin/api/admins/remove",
                          json={"name": "stranger77"})
    assert r.status_code == 200
    r = await client.get("/admin/api/players")
    assert r.status_code == 401
    client.cookies.clear()

    # the desk cannot empty itself
    await _sign_in(client, "huemorgan3")
    for a in (await client.get("/admin/api/admins")).json()["admins"]:
        if a["name"] != "huemorgan3":
            await client.post("/admin/api/admins/remove",
                              json={"name": a["name"]})
    r = await client.post("/admin/api/admins/remove",
                          json={"name": "huemorgan3"})
    assert r.status_code == 409
    client.cookies.clear()


async def test_players_list_and_search(client, desk, tenant_a):
    player = _p("desk")
    name = f"Desk{player[-4:]}"
    await create(client, tenant_a, "tenant-a", player, name)

    r = await client.get("/admin/api/players")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1 and len(data["players"]) <= 100
    # leaderboard ordering: level never rises down the list
    levels = [p["level"] for p in data["players"]]
    assert levels == sorted(levels, reverse=True)

    r = await client.get(f"/admin/api/players?q={name[:6]}")
    found = r.json()["players"]
    assert any(p["player"] == player for p in found)
    # a search that matches nobody is an empty list, not an error
    r = await client.get("/admin/api/players?q=zz-nobody-zz")
    assert r.json()["players"] == []


async def test_player_detail_edit_and_grant(client, desk, tenant_a):
    player = _p("edit")
    await create(client, tenant_a, "tenant-a", player, f"Edit{player[-4:]}")

    r = await client.get(
        f"/admin/api/player?tenant=tenant-a&player={player}")
    assert r.status_code == 200
    d = r.json()
    assert d["energy"] is not None and d["energy_cap"] >= d["energy"]
    assert "weapon" in d["gear"]

    r = await client.post("/admin/api/player", json={
        "tenant": "tenant-a", "player": player,
        "energy": 3, "xp": 777, "gold": 12345, "bank": 9,
        "grant": ["wolfbite"]})
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["player"]["xp"] == 777
    assert out["player"]["gold"] == 12345
    assert out["player"]["bank"] == 9

    doc = await get_doc("tenant-a", player)
    assert doc["xp"] == 777 and doc["gold"] == 12345 and doc["bank"] == 9
    assert doc["energy_val"] == 3.0
    assert doc["inventory"].get("wolfbite") == 1
    assert doc["durability_pack"].get("wolfbite", 0) > 0

    # the edit leaves a ledger trail
    pool = await db.get_pool()
    note = await pool.fetchval(
        "SELECT note FROM ascent_ledger WHERE tenant='tenant-a' "
        "AND player=$1 AND kind='admin' ORDER BY id DESC LIMIT 1", player)
    assert "grant wolfbite" in note and "energy=3" in note

    # guardrails: unknown weapon, no-op edit, no such player
    r = await client.post("/admin/api/player", json={
        "tenant": "tenant-a", "player": player, "grant": ["padded_jerkin"]})
    assert r.status_code == 400
    r = await client.post("/admin/api/player", json={
        "tenant": "tenant-a", "player": player})
    assert r.status_code == 400
    r = await client.post("/admin/api/player", json={
        "tenant": "tenant-a", "player": "ghost", "gold": 1})
    assert r.status_code == 404


async def test_player_ledger_and_rescue(client, desk, tenant_a):
    player = _p("ops")
    await create(client, tenant_a, "tenant-a", player, f"Ops{player[-4:]}")

    # jam the doc the way stuck players arrive: wounded, lodged, and a
    # half-broken encounter in the way
    pool = await db.get_pool()
    doc = await get_doc("tenant-a", player)
    doc["hp"] = 1
    doc["lodged_until_day"] = 10_000_000
    doc["encounter"] = {"kind": "wilds", "id": "gone_creature"}
    doc["location"] = "fight"
    await pool.execute(
        "UPDATE ascent_players SET doc=$3 WHERE tenant=$1 AND player=$2",
        "tenant-a", player, json.dumps(doc))

    r = await client.post("/admin/api/player/rescue", json={
        "tenant": "tenant-a", "player": player})
    assert r.status_code == 200, r.text
    doc = await get_doc("tenant-a", player)
    assert doc["hp"] > 1 and doc["encounter"] is None
    assert doc["location"] == "town" and doc["lodged_until_day"] == -1

    # the proof: the tower serves the doc again
    from tests.test_world_api import scene
    s = await scene(client, tenant_a, "tenant-a", player)
    assert s["options"], "a rescued climber gets a live town menu"

    # the trail: rescue is in the ledger, and the desk can read it
    r = await client.get(
        f"/admin/api/player/ledger?tenant=tenant-a&player={player}")
    entries = r.json()["entries"]
    assert entries and entries[0]["kind"] == "admin"
    assert entries[0]["note"] == "rescue"

    # a ghost stays a 404
    r = await client.post("/admin/api/player/rescue", json={
        "tenant": "tenant-a", "player": "ghost"})
    assert r.status_code == 404


async def test_weapons_catalog(client, desk):
    r = await client.get("/admin/api/weapons")
    assert r.status_code == 200
    ws = r.json()["weapons"]
    slugs = {w["slug"] for w in ws}
    assert "wolfbite" in slugs
    assert all(w["line"] for w in ws)


async def test_feedback_tab(client, desk, tenant_a):
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_feedback")
    player = _p("fb")
    await create(client, tenant_a, "tenant-a", player, f"Fb{player[-4:]}")
    out = await fb(client, tenant_a, "tenant-a", player, "create", {
        "subject": "the desk test", "body": "is anyone up there?"})
    fid = out["id"]

    r = await client.get("/admin/api/feedback")
    threads = r.json()["threads"]
    assert [t["id"] for t in threads] == [fid]
    assert threads[0]["tenant"] == "tenant-a"

    r = await client.post(f"/admin/api/feedback/{fid}/reply", json={"body": "always."})
    assert r.status_code == 200

    r = await client.get(f"/admin/api/feedback/{fid}")
    t = r.json()
    assert t["player"] == player            # the desk sees the keys
    assert t["messages"][-1]["sender"] == "admin"
    assert t["messages"][-1]["body"] == "always."

    # the player sees the reply land
    mine = await fb(client, tenant_a, "tenant-a", player, "thread",
                    {"id": fid})
    assert mine["messages"][-1]["sender"] == "admin"


async def test_feedback_unread_badge(client, desk, tenant_a):
    """The tab badge count: new mail raises it, reading clears it."""
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_feedback")
    r = await client.get("/admin/api/feedback/unread")
    assert r.status_code == 200 and r.json()["unread"] == 0

    player = _p("badge")
    await create(client, tenant_a, "tenant-a", player, f"Bdg{player[-4:]}")
    out = await fb(client, tenant_a, "tenant-a", player, "create", {
        "subject": "badge test", "body": "hello?"})
    fid = out["id"]
    await fb(client, tenant_a, "tenant-a", player, "reply", {
        "id": fid, "body": "still there?"})

    r = await client.get("/admin/api/feedback/unread")
    assert r.json()["unread"] == 2

    # opening the thread marks it read; the badge drops to zero
    await client.get(f"/admin/api/feedback/{fid}")
    r = await client.get("/admin/api/feedback/unread")
    assert r.json()["unread"] == 0

    # and the badge is behind the door like everything else
    client.cookies.clear()
    r = await client.get("/admin/api/feedback/unread")
    assert r.status_code == 401


async def test_world_overview(client, desk, tenant_a):
    """The WORLD tab: census, population, frontier, postbox, ledger."""
    player = _p("world")
    await create(client, tenant_a, "tenant-a", player, f"Wld{player[-4:]}")

    r = await client.get("/admin/api/world")
    assert r.status_code == 200
    w = r.json()
    assert w["frontier"] >= 1
    pop = w["population"]
    assert pop["total"] >= 1
    assert pop["playing"] <= pop["total"]
    assert pop["seen_today"] >= 1          # we just made a climber
    # a fresh climber is playing and was seen now — the census sees them
    assert w["census"]["total"] >= 1
    assert sum(w["census"]["by_floor"].values()) == w["census"]["total"]
    assert w["feedback"]["threads"] >= 0
    assert w["ledger"]["rows"] >= 0
    assert "warden" in w                    # present, may be null

    client.cookies.clear()
    r = await client.get("/admin/api/world")
    assert r.status_code == 401


async def test_raw_doc_and_luna_user_search(client, desk, tenant_a):
    """Support tooling: the raw doc opens read-only, and a climber can
    be found by the luna user on their doc."""
    player = _p("raw")
    await create(client, tenant_a, "tenant-a", player, f"Raw{player[-4:]}")

    pool = await db.get_pool()
    doc = await get_doc("tenant-a", player)
    doc["luna_user"] = "discord:roygbiv#1234"
    await pool.execute(
        "UPDATE ascent_players SET doc=$3 WHERE tenant=$1 AND player=$2",
        "tenant-a", player, json.dumps(doc))

    r = await client.get(
        f"/admin/api/player/doc?tenant=tenant-a&player={player}")
    assert r.status_code == 200
    d = r.json()["doc"]
    assert d["name"] == doc["name"] and d["luna_user"] == doc["luna_user"]

    r = await client.get("/admin/api/players?q=roygbiv")
    assert any(p["player"] == player for p in r.json()["players"])

    r = await client.get(
        "/admin/api/player/doc?tenant=tenant-a&player=ghost")
    assert r.status_code == 404
    client.cookies.clear()
    r = await client.get(
        f"/admin/api/player/doc?tenant=tenant-a&player={player}")
    assert r.status_code == 401

