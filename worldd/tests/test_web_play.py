"""005 web play — the door opens into the game.

A web account climbs as (tenant='web', player=lower(username)) through
cookie-authed /play/api routes. HMAC auth for tenant 'web' is refused,
the funnel's non-JSON door posts land on /play, and the doc boots named
so the in-game registrar never asks.
"""

from __future__ import annotations

import hashlib
import hmac as hmaclib
import json
import re
import time
import uuid

PW = "probeprobe"


def _uname(prefix: str = "Webp") -> str:
    return f"{prefix}{uuid.uuid4().hex[:10]}"


async def _signup(client, username: str, email: str = ""):
    body = {"username": username, "password": PW, "password2": PW}
    if email:
        body["email"] = email
    r = await client.post("/signup", json=body)
    assert r.status_code == 200, r.text
    return r


_OPT = re.compile(r'data-opt="([^"]+)"')


async def _walk_to_town(client, max_steps: int = 40) -> dict:
    """Click the first option of every card until Roothollow welcomes us —
    story pages, race, class; never a name prompt (the door carved it)."""
    r = await client.post("/play/api/pane/scene", json={})
    assert r.status_code == 200, r.text
    card = r.json()
    for _ in range(max_steps):
        if card["headline"].startswith("Welcome to Roothollow"):
            return card
        m = _OPT.search(card["fragment"])
        assert m, f"stuck on a card with no options: {card['headline']!r}"
        r = await client.post("/play/api/act",
                              json={"option": m.group(1), "mode": "pane"})
        assert r.status_code == 200, r.text
        card = r.json()
    raise AssertionError("never reached Roothollow")


async def test_migration_seeds_web_tenant_and_email_column(client):
    from app import db
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT secret, disabled FROM ascent_tenants WHERE tenant='web'")
    assert row is not None and row["secret"] and not row["disabled"]
    # the email column exists and is nullable (no constraint to trip)
    await pool.fetchval("SELECT email FROM ascent_accounts LIMIT 1")


async def test_hmac_refuses_web_tenant_even_with_its_secret(client):
    from app import db
    pool = await db.get_pool()
    secret = await pool.fetchval(
        "SELECT secret FROM ascent_tenants WHERE tenant='web'")
    body = json.dumps({"player": "anyone"})
    ts = str(int(time.time()))
    sig = hmaclib.new(secret.encode(), f"{ts}.{body}".encode(),
                      hashlib.sha256).hexdigest()
    r = await client.post("/v1/scene", content=body, headers={
        "Content-Type": "application/json",
        "X-Ascent-Api": "1", "X-Ascent-Tenant": "web",
        "X-Ascent-Ts": ts, "X-Ascent-Signature": sig})
    assert r.status_code == 401


async def test_play_gates_without_a_cookie(client):
    r = await client.get("/play")
    assert r.status_code == 303
    assert r.headers["location"] == "/#door-signin"
    for path in ("/play/api/pane/scene", "/play/api/act",
                 "/play/api/pane/faction/enter"):
        assert (await client.post(path, json={})).status_code == 401, path
    for path in ("/play/api/pane/peek", "/play/api/pane/score",
                 "/play/api/pane/community", "/play/api/pane/factions"):
        assert (await client.get(path)).status_code == 401, path


async def test_cross_origin_post_is_403(client):
    await _signup(client, _uname())
    r = await client.post("/play/api/act", json={},
                          headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    # same-origin posts (the pane's own) pass
    r = await client.post("/play/api/pane/scene", json={},
                          headers={"Origin": "http://test"})
    assert r.status_code == 200


async def test_signup_walks_into_the_game_prenamed(client):
    username = _uname("Probe")
    await _signup(client, username)
    card = await _walk_to_town(client)
    assert username in card["headline"]
    from app import db
    pool = await db.get_pool()
    doc = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='web' AND player=$1",
        username.lower()))
    assert doc["stage"] == "playing"
    assert doc["name"] == username
    # one namespace: the account claim IS the claim — exactly one row
    n = await pool.fetchval(
        "SELECT count(*) FROM ascent_names WHERE name_lower = lower($1)",
        username)
    assert n == 1


async def test_play_serves_the_web_pane(client):
    await _signup(client, _uname())
    r = await client.get("/play")
    assert r.status_code == 200
    assert "'/play/api'" in r.text
    assert "const WEB = true;" in r.text


async def test_peek_shape(client):
    await _signup(client, _uname())
    await client.post("/play/api/pane/scene", json={})
    r = await client.get("/play/api/pane/peek")
    assert r.status_code == 200
    j = r.json()
    assert isinstance(j["scene_id"], str) and j["scene_id"]
    assert isinstance(j["floor_presence"], int)


async def test_leaderboard_marks_only_you(client):
    # the shared web tenant holds every browser climber — the you flag
    # must be per (tenant, player), not per tenant
    alpha, bravo = _uname("Alpha"), _uname("Bravo")
    await _signup(client, alpha)
    await _walk_to_town(client)
    await _signup(client, bravo)          # cookie now belongs to bravo
    await _walk_to_town(client)
    r = await client.get("/play/api/pane/score")
    assert r.status_code == 200
    yous = [p["name"] for p in r.json()["players"] if p["you"]]
    assert yous == [bravo]
    await client.post("/login", json={"username": alpha, "password": PW})
    yous = [p["name"]
            for p in (await client.get("/play/api/pane/score")).json()["players"]
            if p["you"]]
    assert yous == [alpha]


async def test_scripts_off_door_redirects_to_play(client):
    username = _uname()
    r = await client.post("/signup", data={
        "username": username, "password": PW, "password2": PW})
    assert r.status_code == 303
    assert r.headers["location"] == "/play"
    r = await client.post("/login", data={"username": username,
                                          "password": PW})
    assert r.status_code == 303
    assert r.headers["location"] == "/play"


async def test_email_stored_optionally(client):
    from app import db
    pool = await db.get_pool()
    with_mail, without = _uname(), _uname()
    await _signup(client, with_mail, email="  roy@example.com ")
    assert await pool.fetchval(
        "SELECT email FROM ascent_accounts WHERE username=$1",
        with_mail) == "roy@example.com"
    await _signup(client, without)
    assert await pool.fetchval(
        "SELECT email FROM ascent_accounts WHERE username=$1",
        without) is None


# ── 076: floor changes ride the lift ─────────────────────────────────────

async def test_076_floor_change_carries_the_lift(client):
    await _signup(client, _uname("Lift"))
    await _walk_to_town(client)
    r = await client.post("/play/api/act",
                          json={"option": "gate", "mode": "pane"})
    assert r.status_code == 200, r.text
    r = await client.post("/play/api/act",
                          json={"option": "floor_1", "mode": "pane"})
    assert r.status_code == 200, r.text
    card = r.json()
    assert 'data-lift="up"' in card["fragment"]
    # step off the movie if the floor introduces itself, then ride down
    if 'data-opt="skip"' in card["fragment"]:
        r = await client.post("/play/api/act",
                              json={"option": "skip", "mode": "pane"})
        assert r.status_code == 200, r.text
        card = r.json()
        assert "data-lift" not in card["fragment"]   # the reel exit is quiet
    r = await client.post("/play/api/act",
                          json={"option": "town", "mode": "pane"})
    assert r.status_code == 200, r.text
    assert 'data-lift="down"' in r.json()["fragment"]


async def test_076_pane_ships_the_lift_overlay_and_the_gifs_serve(client):
    await _signup(client, _uname("Liftp"))
    r = await client.get("/play")
    assert r.status_code == 200
    assert "liftlay" in r.text and "playLift" in r.text
    for slug in ("lift_ascent", "lift_descent"):
        assert f"/static/fxart/{slug}_320x112.gif" in r.text
        g = await client.get(f"/static/fxart/{slug}_320x112.gif")
        assert g.status_code == 200, slug
        assert g.headers["content-type"] == "image/gif"
