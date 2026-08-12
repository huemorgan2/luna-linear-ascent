"""The admin desk — /admin console, player list/search/edit, grants,
and the feedback tab, all behind X-Admin-Key."""

from __future__ import annotations

import json
import uuid

import pytest

from app import db
from app.config import get_config
from tests.test_051_feedback import fb
from tests.test_social_api import create, get_doc
from tests.test_world_api import make_tenant

ADMIN = {"X-Admin-Key": "test-admin-key"}


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


def _p(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def test_admin_session_walks_in_without_the_key(client):
    """huemorgan3's site session IS the key; a stranger's is not."""
    pool = await db.get_pool()
    for name in ("huemorgan3", "stranger77"):
        await pool.execute(
            "DELETE FROM ascent_names WHERE name_lower=$1", name)
        await pool.execute(
            "DELETE FROM ascent_accounts WHERE lower(username)=$1", name)
        await pool.execute(
            "DELETE FROM ascent_players WHERE tenant='web' AND player=$1",
            name)
    from tests.test_web_play import _signup

    await _signup(client, "stranger77")
    r = await client.get("/admin/api/players")
    assert r.status_code == 401
    client.cookies.clear()

    await _signup(client, "huemorgan3")
    r = await client.get("/admin/api/players")
    assert r.status_code == 200
    r = await client.get("/admin/api/feedback")
    assert r.status_code == 200
    client.cookies.clear()


async def test_page_and_key_gate(client):
    r = await client.get("/admin")
    assert r.status_code == 200 and "ADMIN" in r.text
    r = await client.get("/admin/api/players")
    assert r.status_code == 401
    r = await client.get("/admin/api/players",
                         headers={"X-Admin-Key": "wrong"})
    assert r.status_code == 401


async def test_players_list_and_search(client, tenant_a):
    player = _p("desk")
    name = f"Desk{player[-4:]}"
    await create(client, tenant_a, "tenant-a", player, name)

    r = await client.get("/admin/api/players", headers=ADMIN)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1 and len(data["players"]) <= 100
    # leaderboard ordering: level never rises down the list
    levels = [p["level"] for p in data["players"]]
    assert levels == sorted(levels, reverse=True)

    r = await client.get(f"/admin/api/players?q={name[:6]}", headers=ADMIN)
    found = r.json()["players"]
    assert any(p["player"] == player for p in found)
    # a search that matches nobody is an empty list, not an error
    r = await client.get("/admin/api/players?q=zz-nobody-zz", headers=ADMIN)
    assert r.json()["players"] == []


async def test_player_detail_edit_and_grant(client, tenant_a):
    player = _p("edit")
    await create(client, tenant_a, "tenant-a", player, f"Edit{player[-4:]}")

    r = await client.get(
        f"/admin/api/player?tenant=tenant-a&player={player}", headers=ADMIN)
    assert r.status_code == 200
    d = r.json()
    assert d["energy"] is not None and d["energy_cap"] >= d["energy"]
    assert "weapon" in d["gear"]

    r = await client.post("/admin/api/player", headers=ADMIN, json={
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
    r = await client.post("/admin/api/player", headers=ADMIN, json={
        "tenant": "tenant-a", "player": player, "grant": ["padded_jerkin"]})
    assert r.status_code == 400
    r = await client.post("/admin/api/player", headers=ADMIN, json={
        "tenant": "tenant-a", "player": player})
    assert r.status_code == 400
    r = await client.post("/admin/api/player", headers=ADMIN, json={
        "tenant": "tenant-a", "player": "ghost", "gold": 1})
    assert r.status_code == 404


async def test_player_ledger_and_rescue(client, tenant_a):
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

    r = await client.post("/admin/api/player/rescue", headers=ADMIN, json={
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
        f"/admin/api/player/ledger?tenant=tenant-a&player={player}",
        headers=ADMIN)
    entries = r.json()["entries"]
    assert entries and entries[0]["kind"] == "admin"
    assert entries[0]["note"] == "rescue"

    # a ghost stays a 404
    r = await client.post("/admin/api/player/rescue", headers=ADMIN, json={
        "tenant": "tenant-a", "player": "ghost"})
    assert r.status_code == 404


async def test_weapons_catalog(client):
    r = await client.get("/admin/api/weapons", headers=ADMIN)
    assert r.status_code == 200
    ws = r.json()["weapons"]
    slugs = {w["slug"] for w in ws}
    assert "wolfbite" in slugs
    assert all(w["line"] for w in ws)


async def test_feedback_tab(client, tenant_a):
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_feedback")
    player = _p("fb")
    await create(client, tenant_a, "tenant-a", player, f"Fb{player[-4:]}")
    out = await fb(client, tenant_a, "tenant-a", player, "create", {
        "subject": "the desk test", "body": "is anyone up there?"})
    fid = out["id"]

    r = await client.get("/admin/api/feedback", headers=ADMIN)
    threads = r.json()["threads"]
    assert [t["id"] for t in threads] == [fid]
    assert threads[0]["tenant"] == "tenant-a"

    r = await client.post(f"/admin/api/feedback/{fid}/reply",
                          headers=ADMIN, json={"body": "always."})
    assert r.status_code == 200

    r = await client.get(f"/admin/api/feedback/{fid}", headers=ADMIN)
    t = r.json()
    assert t["player"] == player            # the desk sees the keys
    assert t["messages"][-1]["sender"] == "admin"
    assert t["messages"][-1]["body"] == "always."

    # the player sees the reply land
    mine = await fb(client, tenant_a, "tenant-a", player, "thread",
                    {"id": fid})
    assert mine["messages"][-1]["sender"] == "admin"
