"""003-linearascent-net — the front door worldd serves itself.

The homepage, the public world feed, and old-days accounts: a username
and a password, nothing else. The page must work with scripts off, so
the form paths (urlencoded POST → redirect) are tested alongside the
JSON paths the page's JS uses.
"""

import uuid

from app import db, site


def _name() -> str:
    return f"Door{uuid.uuid4().hex[:6]}"


# ── the page ─────────────────────────────────────────────────────────────

async def test_homepage_serves_the_terminal(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    body = r.text
    assert "LINEAR ASCENT" in body
    assert "FREE" in body                      # ours is free — play on that
    assert 'action="/signup"' in body          # the door posts without JS
    # 004: two doors, named the way everyone names them
    assert "SIGN-UP" in body and "SIGN-IN" in body
    assert "NEW PASSWORD" in body and "RETYPE PASSWORD" in body
    assert 'formaction="/login"' in body       # sign-in works scripts off too
    # the terminal law: the one vendored font, no external requests
    assert "WebPlus_IBM_VGA_8x16.woff" in (await client.get(
        "/static/site/site.css")).text
    assert "googleapis" not in body and "cdn." not in body


async def test_health_is_untouched_by_the_site(client):
    r = await client.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True


# ── the public feed ──────────────────────────────────────────────────────

async def test_public_world_shape_and_cors(client):
    site._world_cache.update(at=0.0, data=None)     # a fresh read
    r = await client.get("/v1/public/world")
    assert r.status_code == 200
    assert r.headers["access-control-allow-origin"] == "*"
    w = r.json()
    assert w["ok"] is True
    assert isinstance(w["day"], int)
    assert w["frontier"] >= 1
    assert w["era"] >= 1
    assert "total" in w["climbers"] and "online" in w["climbers"]
    assert isinstance(w["stone"], list)
    assert isinstance(w["crier"], list)
    assert w["game"] not in ("", "unknown")
    # frontier 1 is no milestone: the shop window shows the live Warden
    if w["frontier"] == 1:
        assert w["warden"]["name"]
        assert 0 <= w["warden"]["pct"] <= 100


async def test_public_world_is_cached(client):
    site._world_cache.update(at=0.0, data=None)
    first = (await client.get("/v1/public/world")).json()
    pool = await db.get_pool()
    await pool.execute(
        "INSERT INTO ascent_stone (line) VALUES ('a line the cache hides')")
    try:
        again = (await client.get("/v1/public/world")).json()
        assert again == first                    # 60s window: same payload
    finally:
        await pool.execute(
            "DELETE FROM ascent_stone WHERE line='a line the cache hides'")
        site._world_cache.update(at=0.0, data=None)


# ── the door: JSON (the page's JS) ───────────────────────────────────────

async def test_signup_login_logout_json(client):
    name = _name()
    r = await client.post("/signup", json={"username": name,
                                           "password": "hunter2",
                                           "password2": "hunter2"})
    assert r.status_code == 200
    assert r.json()["username"] == name
    assert site.SESSION_COOKIE in r.cookies

    # the cookie is a signed session — /me knows the name
    r = await client.get("/me")
    assert r.json()["username"] == name

    # same name, any casing: the door is taken
    r = await client.post("/signup", json={"username": name.upper(),
                                           "password": "other"})
    assert r.status_code == 409

    # wrong knock
    r = await client.post("/login", json={"username": name,
                                          "password": "wrong"})
    assert r.status_code == 401

    # right knock, case-blind name — the stored casing comes back
    r = await client.post("/login", json={"username": name.lower(),
                                          "password": "hunter2"})
    assert r.status_code == 200 and r.json()["username"] == name

    r = await client.post("/logout",
                          headers={"Accept": "application/json"})
    assert r.status_code == 200
    client.cookies.clear()
    assert (await client.get("/me")).json()["username"] is None


async def test_signup_rules(client):
    r = await client.post("/signup", json={"username": "x",
                                           "password": "hunter2"})
    assert r.status_code == 422                   # one stroke is no name
    r = await client.post("/signup", json={"username": "«»",
                                           "password": "hunter2"})
    assert r.status_code == 422                   # nothing granite can hold
    r = await client.post("/signup", json={"username": _name(),
                                           "password": "abc"})
    assert r.status_code == 422                   # password too short
    # 004: sign-up asks twice, and a mismatch is refused with the reason
    r = await client.post("/signup", json={"username": _name(),
                                           "password": "hunter2",
                                           "password2": "hunter3"})
    assert r.status_code == 422
    assert "differ" in r.json()["detail"]


async def test_the_username_is_the_climber_name_one_word(client):
    """"Master Chief" is MasterChief: the space is joined, not refused —
    the same law the gate's registrar follows."""
    stem = _name()
    r = await client.post("/signup", json={"username": f"{stem} Chief",
                                           "password": "hunter2",
                                           "password2": "hunter2"})
    assert r.status_code == 200
    assert r.json()["username"] == f"{stem}Chief"
    # and it is the name the world now holds
    from app import db as _db
    assert await (await _db.get_pool()).fetchval(
        "SELECT kind FROM ascent_names WHERE name_lower = lower($1)",
        f"{stem}Chief") == "account"


# ── the door: scripts off (plain form POST → redirect) ───────────────────

async def test_signup_form_post_redirects_and_sets_cookie(client):
    name = _name()
    r = await client.post("/signup", data={"username": name,
                                           "password": "hunter2"})
    assert r.status_code == 303
    assert r.headers["location"] == "/#door"
    assert site.SESSION_COOKIE in r.cookies
    assert (await client.get("/me")).json()["username"] == name

    # a taken name walks back to the door with the reason in hand
    client.cookies.clear()
    r = await client.post("/signup", data={"username": name,
                                           "password": "hunter2"})
    assert r.status_code == 303
    assert "door_err=" in r.headers["location"]


# ── the account outlives the era ─────────────────────────────────────────

async def test_accounts_survive_the_era_reset(client):
    from app import era
    assert "ascent_accounts" in era.PERMANENT_TABLES
    assert "ascent_accounts" not in era.TRANSIENT_TABLES
