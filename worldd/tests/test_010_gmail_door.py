"""010 — the Gmail door: sign up with Google, keep password login.

The Google token exchange is mocked (no network): every test drives the
real /auth/google/start → /auth/google/callback → name-step flow with a
fixed identity, exactly as the browser would, and asserts the account,
the session, and the branch each identity should take.
"""

import os
import uuid
from urllib.parse import parse_qs, urlsplit

import pytest

# config must carry the Google creds before the app reads it (conftest
# calls reset_config in the client fixture, so setting env here is enough)
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-secret")
os.environ.setdefault("GOOGLE_REDIRECT_URI", "http://test/auth/google/callback")

from app import db, google_oauth, site  # noqa: E402


def _identity(**over) -> dict:
    uid = uuid.uuid4().hex[:10]
    who = {"sub": f"g-{uid}", "email": f"{uid}@gmail.com",
           "email_verified": True, "name": f"Ash {uid}",
           "given_name": f"Ash{uid}"}
    who.update(over)
    return who


async def _google_return(client, monkeypatch, identity):
    """Walk start→callback with a mocked exchange; return the callback resp.
    Cookies (oauth state, then pending/session) ride the client jar."""
    async def fake_exchange(code, verifier):
        return identity
    monkeypatch.setattr(google_oauth, "exchange_code", fake_exchange)
    r = await client.get("/auth/google/start")
    assert r.status_code == 303
    state = parse_qs(urlsplit(r.headers["location"]).query)["state"][0]
    return await client.get(
        f"/auth/google/callback?code=abc&state={state}")


# ── the happy path: brand-new climber picks a name ───────────────────────

async def test_new_gmail_signup_names_then_plays(client, monkeypatch):
    client.cookies.clear()
    who = _identity()
    r = await _google_return(client, monkeypatch, who)
    # a new sub → no account yet, held in a pending cookie, sent to name step
    assert r.status_code == 303
    assert r.headers["location"] == "/auth/google/name"
    assert site.PENDING_COOKIE in r.cookies or \
        site.PENDING_COOKIE in client.cookies
    assert site.SESSION_COOKIE not in client.cookies
    pool = await db.get_pool()
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_accounts WHERE google_sub=$1",
        who["sub"]) == 0

    # the name step is served, prefilled from the Google given name
    page = await client.get("/auth/google/name")
    assert page.status_code == 200
    assert "Pick your name" in page.text
    assert who["given_name"] in page.text

    # choose the name → account is written, session set, into the game
    name = f"Climb{uuid.uuid4().hex[:6]}"
    r = await client.post("/auth/google/name", data={"username": name})
    assert r.status_code == 303 and r.headers["location"] == "/play"
    assert site.SESSION_COOKIE in client.cookies

    row = await pool.fetchrow(
        "SELECT username, pw_hash, auth_provider, google_sub, email "
        "FROM ascent_accounts WHERE google_sub=$1", who["sub"])
    assert row["username"] == name
    assert row["pw_hash"] is None
    assert row["auth_provider"] == "google"
    assert row["email"] == who["email"]
    # the name is claimed in the one registry
    assert await pool.fetchval(
        "SELECT kind FROM ascent_names WHERE name_lower=lower($1)",
        name) == "account"

    # /me now knows it is a Gmail account
    me = (await client.get("/me")).json()
    assert me["username"] == name
    assert me["gmail"] is True
    assert me["auth_provider"] == "google"


# ── a known Google identity walks straight back in ───────────────────────

async def test_returning_gmail_logs_in_without_name_step(client, monkeypatch):
    client.cookies.clear()
    who = _identity()
    await _google_return(client, monkeypatch, who)
    name = f"Back{uuid.uuid4().hex[:6]}"
    await client.post("/auth/google/name", data={"username": name})

    # fresh browser, same Google account → straight to /play, no name step
    client.cookies.clear()
    r = await _google_return(client, monkeypatch, who)
    assert r.status_code == 303 and r.headers["location"] == "/play"
    assert site.SESSION_COOKIE in client.cookies
    pool = await db.get_pool()
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_accounts WHERE google_sub=$1",
        who["sub"]) == 1                       # not duplicated


# ── an old password account whose email IS the Google address ────────────

async def test_gmail_adopts_matching_password_account(client, monkeypatch):
    client.cookies.clear()
    name = f"Old{uuid.uuid4().hex[:6]}"
    email = f"{name.lower()}@gmail.com"
    pool = await db.get_pool()
    await pool.execute(
        "INSERT INTO ascent_accounts (username, pw_hash, email) "
        "VALUES ($1, $2, $3)", name, site._hash_pw("hunter2"), email)

    who = _identity(email=email)
    r = await _google_return(client, monkeypatch, who)
    # linked + logged in, no name step, no duplicate
    assert r.status_code == 303 and r.headers["location"] == "/play"
    row = await pool.fetchrow(
        "SELECT google_sub, auth_provider FROM ascent_accounts "
        "WHERE lower(username)=lower($1)", name)
    assert row["google_sub"] == who["sub"]
    assert row["auth_provider"] == "google"
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_accounts WHERE lower(email)=lower($1)",
        email) == 1


# ── a taken name is refused at the name step ─────────────────────────────

async def test_name_step_refuses_a_taken_name(client, monkeypatch):
    client.cookies.clear()
    # someone already holds this name
    first = _identity()
    await _google_return(client, monkeypatch, first)
    taken = f"Dup{uuid.uuid4().hex[:6]}"
    await client.post("/auth/google/name", data={"username": taken})

    # a brand-new climber tries the same name (form path → redirect w/ err)
    client.cookies.clear()
    second = _identity()
    await _google_return(client, monkeypatch, second)
    r = await client.post("/auth/google/name", data={"username": taken})
    assert r.status_code == 303
    assert r.headers["location"].startswith("/auth/google/name?err=")
    pool = await db.get_pool()
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_accounts WHERE google_sub=$1",
        second["sub"]) == 0

    # the JSON path answers 409 with the reason
    r = await client.post("/auth/google/name",
                          json={"username": taken})
    assert r.status_code == 409


# ── CSRF: a mismatched state is refused, nothing is written ──────────────

async def test_callback_rejects_bad_state(client, monkeypatch):
    client.cookies.clear()

    async def fake_exchange(code, verifier):
        raise AssertionError("exchange must not run on a bad state")
    monkeypatch.setattr(google_oauth, "exchange_code", fake_exchange)
    await client.get("/auth/google/start")            # sets the oauth cookie
    r = await client.get("/auth/google/callback?code=abc&state=not-the-nonce")
    assert r.status_code == 303
    assert "door_err=" in r.headers["location"]
    assert site.SESSION_COOKIE not in client.cookies


# ── the profile "connect Gmail" link links the signed-in account ─────────

async def test_signed_in_account_links_gmail(client, monkeypatch):
    client.cookies.clear()
    # a password account signs in the old way
    name = f"Link{uuid.uuid4().hex[:6]}"
    await client.post("/signup", json={"username": name,
                                       "password": "hunter2"})
    assert (await client.get("/me")).json()["gmail"] is False

    # from the profile, "connect Gmail" runs the same round-trip
    who = _identity()
    r = await _google_return(client, monkeypatch, who)
    assert r.status_code == 303 and r.headers["location"] == "/play"
    me = (await client.get("/me")).json()
    assert me["username"] == name          # still the same account
    assert me["gmail"] is True
    pool = await db.get_pool()
    assert await pool.fetchval(
        "SELECT google_sub FROM ascent_accounts WHERE lower(username)=lower($1)",
        name) == who["sub"]


# ── the door is unavailable when Google isn't configured ─────────────────

async def test_start_is_503_when_unconfigured(client, monkeypatch):
    monkeypatch.setattr(google_oauth, "configured", lambda: False)
    r = await client.get("/auth/google/start")
    assert r.status_code == 503


# ── password login still works for a pre-Gmail account ───────────────────

async def test_password_login_still_open(client):
    name = f"Pwd{uuid.uuid4().hex[:6]}"
    await client.post("/signup", json={"username": name,
                                       "password": "hunter2"})
    client.cookies.clear()
    r = await client.post("/login", json={"username": name,
                                          "password": "hunter2"})
    assert r.status_code == 200 and r.json()["username"] == name


# ── the ID-token decoder validates aud / iss / verified ──────────────────

def _fake_id_token(claims: dict) -> str:
    import base64
    import json

    def seg(d):
        return base64.urlsafe_b64encode(
            json.dumps(d).encode()).rstrip(b"=").decode()
    return f"{seg({'alg': 'RS256'})}.{seg(claims)}.sig"


def test_claims_from_id_token_validates(monkeypatch):
    import time
    from app.config import reset_config
    reset_config()
    cid = os.environ["GOOGLE_CLIENT_ID"]
    good = {"aud": cid, "iss": "https://accounts.google.com",
            "exp": int(time.time()) + 600, "sub": "g-1",
            "email": "A@Gmail.com", "email_verified": True,
            "name": "A", "given_name": "A"}
    who = google_oauth.claims_from_id_token(_fake_id_token(good))
    assert who["sub"] == "g-1"
    assert who["email"] == "a@gmail.com"       # normalized

    with pytest.raises(google_oauth.OAuthError):
        google_oauth.claims_from_id_token(
            _fake_id_token({**good, "aud": "someone-else"}))
    with pytest.raises(google_oauth.OAuthError):
        google_oauth.claims_from_id_token(
            _fake_id_token({**good, "email_verified": False}))
    with pytest.raises(google_oauth.OAuthError):
        google_oauth.claims_from_id_token(
            _fake_id_token({**good, "exp": int(time.time()) - 1}))
