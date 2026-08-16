"""003-linearascent-net — the tower's front door.

worldd serves linearascent.net itself: the homepage, the public world
feed its live blocks read, and old-days accounts — a username and a
password, nothing else. The account survives the era (it is the person,
not the climb); at launch it reserves the climber name, and plan 004's
browser client opens the room behind the door.
"""

from __future__ import annotations

import hashlib
import hmac
import html as htmlmod
import json
import logging
import os
import secrets as pysecrets
import time
from pathlib import Path

import base64

import asyncpg
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from . import db, google_oauth
from .config import get_config

log = logging.getLogger("worldd.site")

router = APIRouter()

SITE_DIR = Path(__file__).resolve().parent.parent / "static" / "site"


# ── The page ─────────────────────────────────────────────────────────────

@router.get("/", include_in_schema=False)
async def homepage():
    return FileResponse(SITE_DIR / "index.html", media_type="text/html")


# The back room: every number the tower runs on, one unlinked page.
# Data is baked by tools/gen_mechanics.py — rerun it when balance moves.

@router.get("/mechanics", include_in_schema=False)
async def mechanics():
    return FileResponse(SITE_DIR / "mechanics.html", media_type="text/html")


# Promotion log — unlinked, like /mechanics. Source is a markdown file.
# /promotion.md is the raw page; /promotion wraps it in the terminal face.

_PROMO_WRAP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LINEAR ASCENT — promotion log</title>
<meta name="robots" content="noindex">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23060606'/%3E%3Crect x='6' y='2' width='4' height='12' fill='%23f2b632'/%3E%3Crect x='4' y='12' width='8' height='2' fill='%23f2b632'/%3E%3C/svg%3E">
<link rel="stylesheet" href="/static/site/site.css?v=0.81.2">
<style>
  main.promo { max-width: 84ch; margin: 3.5rem auto 4rem; padding: 0 1ch; }
  pre.md { white-space: pre-wrap; word-break: break-word; color: var(--fg);
           line-height: 1.35; }
</style>
</head>
<body>
<header id="bar">
  <span id="bar-left">PROMOTION LOG</span>
  <span id="bar-right">LINEAR ASCENT</span>
  <a id="bar-cta" href="/promotion.md">[ .MD ]</a>
</header>
<main class="promo">
  <div class="card wide">
    <div class="eyebrow">UNLINKED · RAW NOTES</div>
    <p class="dim">Canonical markdown: <a href="/promotion.md">/promotion.md</a></p>
    <pre class="md">BODY</pre>
  </div>
</main>
</body>
</html>
"""


@router.get("/promotion.md", include_in_schema=False)
async def promotion_md():
    return FileResponse(
        SITE_DIR / "promotion.md", media_type="text/plain; charset=utf-8")


@router.get("/promotion", include_in_schema=False)
async def promotion():
    raw = (SITE_DIR / "promotion.md").read_text(encoding="utf-8")
    return HTMLResponse(_PROMO_WRAP.replace("BODY", htmlmod.escape(raw)))


# ── The public world feed (no auth — this is the shop window) ────────────

PUBLIC_TTL_S = 60.0
_world_cache: dict = {"at": 0.0, "data": None}


def _public_json(data: dict) -> JSONResponse:
    # CORS-open by design: read-only numbers anyone could see in game
    return JSONResponse(data, headers={
        "Access-Control-Allow-Origin": "*",
        "Cache-Control": f"public, max-age={int(PUBLIC_TTL_S)}"})


@router.get("/v1/public/world")
async def public_world() -> JSONResponse:
    now = time.monotonic()
    if _world_cache["data"] is not None \
            and now - _world_cache["at"] < PUBLIC_TTL_S:
        return _public_json(_world_cache["data"])

    from .gamepath import ensure_game_importable
    ensure_game_importable()
    from plugin_linear_ascent.content import schema
    from plugin_linear_ascent.engine import state as pstate
    from plugin_linear_ascent.version import VERSION

    from . import era as era_mod
    from . import social

    pool = await db.get_pool()
    async with pool.acquire() as conn:
        day = pstate.world_day()
        row = await conn.fetchrow(
            "SELECT value FROM ascent_world WHERE key='frontier'")
        frontier = int(json.loads(row["value"])) if row else 1
        census = await social._census(conn)
        active = int(census.get("total", 0))
        pres = await social._presence(conn)
        online = sum(int(s.get("hot", 0)) + int(s.get("camped", 0))
                     for s in pres["by_floor"].values())

        warden = await social._world_warden(conn, frontier, active)
        wout = None
        if warden is not None:
            try:
                wname = schema.get_floor(frontier).warden_name
            except Exception:
                wname = f"the Warden of floor {frontier}"
            hp_max = max(1, int(warden["hp_max"]))
            wout = {"name": wname, "floor": int(warden["floor"]),
                    "pct": max(0, min(100, round(
                        100 * int(warden["hp"]) / hp_max))),
                    "blades": [s.get("name") or "a climber"
                               for s in warden.get("strikers", [])][-6:]}

        happ = await conn.fetch(
            "SELECT kind, line, floor FROM ascent_happenings "
            "WHERE world_day >= $1 ORDER BY id DESC LIMIT 20", day - 1)
        crier = social._condense_war([dict(r) for r in happ])[:4]

        stone = [r["line"] for r in await conn.fetch(
            "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 8")]

        era_now = await era_mod.current_era(conn)
        eras = []
        for r in await conn.fetch(
                "SELECT era, data FROM ascent_eras ORDER BY era DESC "
                "LIMIT 8"):
            d = json.loads(r["data"])
            eras.append({
                "era": int(r["era"]),
                "day": d.get("world_day"),
                "finisher": d.get("finisher") or "?",
                "blades": max(0, len(d.get("war_party", [])) - 1)})

    data = {
        "ok": True,
        "day": day,
        "era": era_now,
        "game": VERSION,
        "frontier": frontier,
        "climbers": {"total": active, "online": online},
        "warden": wout,
        "crier": crier,
        "stone": stone,
        "eras": eras,
    }
    _world_cache.update(at=now, data=data)
    return _public_json(data)


# ── Old-days accounts ────────────────────────────────────────────────────
# A username and a password — and 004: that username IS the climber's name,
# one word, unique across the whole world. The naming law is the engine's
# (engine/names.py, via app/names.py) so the door and the gate cannot
# disagree about what a name is: letters and numbers in any script, plus
# - and _, and spaces JOINED rather than refused — someone who types
# "Master Chief" means MasterChief.

PASSWORD_MIN = 4
PASSWORD_MAX = 128

SESSION_COOKIE = "ascent_session"
SESSION_MAX_AGE = 30 * 24 * 3600

SIGNUP_PER_HOUR = int(os.environ.get("ASCENT_SIGNUP_PER_HOUR", "20"))
_signup_hits: dict[str, list[float]] = {}


class _NameTaken(Exception):
    """The registry already holds this name — the door's 409, in flight."""


def _signup_ok(ip: str) -> bool:
    now = time.monotonic()
    hits = [t for t in _signup_hits.get(ip, []) if now - t < 3600]
    ok = len(hits) < SIGNUP_PER_HOUR
    if ok:
        hits.append(now)
    _signup_hits[ip] = hits
    return ok


def _hash_pw(password: str) -> str:
    salt = pysecrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt,
                       n=2 ** 14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${h.hex()}"


def _check_pw(password: str, stored: str) -> bool:
    try:
        kind, salt_hex, want_hex = stored.split("$")
        if kind != "scrypt":
            return False
        got = hashlib.scrypt(password.encode(),
                             salt=bytes.fromhex(salt_hex),
                             n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(got.hex(), want_hex)
    except Exception:
        return False


def _session_secret() -> bytes:
    return get_config().shared_secret.encode() or b"dev-only"


def _sign(payload: str) -> str:
    return hmac.new(_session_secret(), payload.encode(),
                    hashlib.sha256).hexdigest()


def _session_token(username: str) -> str:
    payload = f"{username}|{int(time.time()) + SESSION_MAX_AGE}"
    return f"{payload}|{_sign(payload)}"


def session_user(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE, "")
    parts = token.split("|")
    if len(parts) != 3:
        return None
    payload = f"{parts[0]}|{parts[1]}"
    if not hmac.compare_digest(_sign(payload), parts[2]):
        return None
    try:
        if int(parts[1]) < time.time():
            return None
    except ValueError:
        return None
    return parts[0]


async def _credentials(request: Request) -> tuple[str, str, str, str, bool]:
    """(username, password, retyped, email, wants_json) from a JSON fetch
    or a plain urlencoded form POST — the page must work with scripts off.

    The username arrives as the world will hold it: 004 joins the words
    here, once, so every path down the door agrees on the name. The email
    is optional and unvalidated on purpose (005): trimmed, capped, stored
    — it exists so a lost password can be resurrected by hand later.
    """
    from . import names
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        body = await request.json()
        return (names.canonical(body.get("username", "")),
                str(body.get("password", "")),
                str(body.get("password2", "")),
                str(body.get("email", "")).strip()[:254], True)
    form = await request.form()
    return (names.canonical(form.get("username", "")),
            str(form.get("password", "")),
            str(form.get("password2", "")),
            str(form.get("email", "")).strip()[:254], False)


def _set_session_cookie(resp, request: Request, username: str) -> None:
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    resp.set_cookie(SESSION_COOKIE, _session_token(username),
                    max_age=SESSION_MAX_AGE, httponly=True,
                    samesite="lax", secure=(proto == "https"), path="/")


def _door_response(request: Request, username: str, wants_json: bool,
                   note: str):
    if wants_json:
        resp = JSONResponse({"ok": True, "username": username,
                             "note": note})
    else:
        # 005: the door opens INTO the game — scripts-off included
        resp = RedirectResponse("/play", status_code=303)
    _set_session_cookie(resp, request, username)
    return resp


def _door_error(status: int, msg: str, wants_json: bool):
    if wants_json:
        raise HTTPException(status, msg)
    return RedirectResponse(f"/?door_err={msg.replace(' ', '+')}#door",
                            status_code=303)


@router.post("/signup")
async def signup(request: Request):
    from . import names
    username, password, retyped, email, wants_json = \
        await _credentials(request)
    ip = request.client.host if request.client else "?"
    if not _signup_ok(ip):
        return _door_error(429, "too many sign-ups — try later",
                           wants_json)
    if not names.is_legal(username):
        return _door_error(
            422, "username: 2–24 letters, numbers, - or _", wants_json)
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return _door_error(
            422, f"password must be {PASSWORD_MIN}+ characters", wants_json)
    if retyped and retyped != password:
        return _door_error(422, "passwords do not match", wants_json)
    pool = await db.get_pool()
    try:
        async with pool.acquire() as conn, conn.transaction():
            # 004: one namespace. The door and the gate both write the
            # registry, in the same breath as the account, so neither can
            # hand out a name the other already gave away. A rollback takes
            # the reservation with it.
            if await names.claim(conn, username,
                                 names.ACCOUNT) == names.TAKEN:
                raise _NameTaken
            await conn.execute(
                "INSERT INTO ascent_accounts (username, pw_hash, email) "
                "VALUES ($1, $2, $3)", username, _hash_pw(password),
                email or None)
    except (_NameTaken, asyncpg.UniqueViolationError):
        return _door_error(409, "username already taken", wants_json)
    log.info("account created: %s (ip=%s)", username, ip)
    return _door_response(request, username, wants_json, "signed up")


@router.post("/login")
async def login(request: Request):
    username, password, _retyped, _email, wants_json = \
        await _credentials(request)
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT username, pw_hash FROM ascent_accounts "
        "WHERE lower(username) = lower($1)", username)
    if row is None or not _check_pw(password, row["pw_hash"]):
        return _door_error(401, "wrong username or password", wants_json)
    return _door_response(request, row["username"], wants_json,
                          "signed in")


@router.post("/logout")
async def logout(request: Request):
    wants_json = "application/json" in request.headers.get("accept", "")
    resp = JSONResponse({"ok": True}) if wants_json \
        else RedirectResponse("/", status_code=303)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


# ── The Gmail door (010) ─────────────────────────────────────────────────
# Two short-lived, HMAC-signed cookies carry the OAuth round-trip without a
# server-side session store: OAUTH_COOKIE holds the CSRF nonce + PKCE
# verifier (and, if the caller was already signed in, the account to LINK);
# PENDING_COOKIE holds the verified Google identity between the callback and
# the moment a brand-new climber picks a name.

OAUTH_COOKIE = "ascent_oauth"
PENDING_COOKIE = "ascent_pending"
OAUTH_MAX_AGE = 600
PENDING_MAX_AGE = 900


def _blob_sign(payload: dict) -> str:
    raw = base64.urlsafe_b64encode(
        json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{raw}.{_sign(raw)}"


def _blob_read(token: str) -> dict | None:
    try:
        raw, sig = token.split(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(raw), sig):
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        data = json.loads(base64.urlsafe_b64decode(raw + pad))
    except Exception:
        return None
    if int(data.get("exp", 0)) < int(time.time()):
        return None
    return data


def _cookie(resp, request: Request, name: str, value: str,
            max_age: int) -> None:
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    resp.set_cookie(name, value, max_age=max_age, httponly=True,
                    samesite="lax", secure=(proto == "https"), path="/")


def _finish_session(request: Request, username: str):
    """Land a signed-in climber in the game, clearing the round-trip crumbs."""
    resp = RedirectResponse("/play", status_code=303)
    _set_session_cookie(resp, request, username)
    resp.delete_cookie(OAUTH_COOKIE, path="/")
    resp.delete_cookie(PENDING_COOKIE, path="/")
    return resp


def _oauth_fail(msg: str):
    return RedirectResponse(f"/?door_err={msg.replace(' ', '+')}#door",
                            status_code=303)


@router.get("/auth/google/start")
async def google_start(request: Request):
    if not google_oauth.configured():
        raise HTTPException(503, "Gmail sign-in is not configured")
    verifier, challenge = google_oauth.make_pkce()
    nonce = pysecrets.token_urlsafe(16)
    # a signed-in caller → link Gmail to THIS account (profile's "connect")
    link = session_user(request)
    blob = _blob_sign({"nonce": nonce, "verifier": verifier, "link": link,
                       "exp": int(time.time()) + OAUTH_MAX_AGE})
    resp = RedirectResponse(google_oauth.auth_url(nonce, challenge),
                            status_code=303)
    _cookie(resp, request, OAUTH_COOKIE, blob, OAUTH_MAX_AGE)
    return resp


@router.get("/auth/google/callback")
async def google_callback(request: Request):
    if request.query_params.get("error"):
        return _oauth_fail("Gmail sign-in was cancelled")
    code = request.query_params.get("code", "")
    state = request.query_params.get("state", "")
    blob = _blob_read(request.cookies.get(OAUTH_COOKIE, ""))
    if not code or not blob \
            or not hmac.compare_digest(blob.get("nonce", ""), state):
        return _oauth_fail("Gmail sign-in expired — try again")
    try:
        who = await google_oauth.exchange_code(code, blob["verifier"])
    except google_oauth.OAuthError:
        return _oauth_fail("Gmail sign-in failed — try again")

    pool = await db.get_pool()
    link_user = blob.get("link")
    if link_user:
        # linking Gmail to the already-signed-in account
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE ascent_accounts SET google_sub=$1, "
                "auth_provider='google', email=coalesce(email,$2) "
                "WHERE lower(username)=lower($3) AND "
                "(google_sub IS NULL OR google_sub=$1)",
                who["sub"], who["email"], link_user)
        return _finish_session(request, link_user)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT username FROM ascent_accounts WHERE google_sub=$1",
            who["sub"])
        if row:                                   # a known Google identity
            return _finish_session(request, row["username"])
        # an old account whose stored email IS this address → adopt it
        row = await conn.fetchrow(
            "SELECT username, google_sub FROM ascent_accounts "
            "WHERE lower(email)=lower($1) ORDER BY id LIMIT 1", who["email"])
        if row and not row["google_sub"]:
            await conn.execute(
                "UPDATE ascent_accounts SET google_sub=$1, "
                "auth_provider='google' WHERE lower(username)=lower($2)",
                who["sub"], row["username"])
            return _finish_session(request, row["username"])

    # brand new — hold the proven identity until they pick a name
    pending = _blob_sign({"sub": who["sub"], "email": who["email"],
                          "given": who.get("given_name") or who.get("name"),
                          "exp": int(time.time()) + PENDING_MAX_AGE})
    resp = RedirectResponse("/auth/google/name", status_code=303)
    resp.delete_cookie(OAUTH_COOKIE, path="/")
    _cookie(resp, request, PENDING_COOKIE, pending, PENDING_MAX_AGE)
    return resp


@router.get("/auth/google/name")
async def google_name(request: Request):
    from . import names
    pending = _blob_read(request.cookies.get(PENDING_COOKIE, ""))
    if not pending:
        return RedirectResponse("/", status_code=303)
    base = (pending.get("given") or "").strip() \
        or pending.get("email", "").split("@")[0]
    suggested = names.canonical(base) or ""
    err = request.query_params.get("err", "")
    return HTMLResponse(_name_page(pending.get("email", ""), suggested, err))


@router.post("/auth/google/name")
async def google_name_post(request: Request):
    from . import names
    pending = _blob_read(request.cookies.get(PENDING_COOKIE, ""))
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        body = await request.json()
        raw_name, wants_json = str(body.get("username", "")), True
    else:
        form = await request.form()
        raw_name, wants_json = str(form.get("username", "")), False
    username = names.canonical(raw_name)
    if not pending:
        return _name_expired(wants_json)
    if not names.is_legal(username):
        return _name_retry(wants_json, "name: 2–24 letters, numbers, - or _")
    pool = await db.get_pool()
    try:
        async with pool.acquire() as conn, conn.transaction():
            if await names.claim(conn, username,
                                 names.ACCOUNT) == names.TAKEN:
                raise _NameTaken
            await conn.execute(
                "INSERT INTO ascent_accounts "
                "(username, pw_hash, email, auth_provider, google_sub) "
                "VALUES ($1, NULL, $2, 'google', $3)",
                username, pending["email"], pending["sub"])
    except (_NameTaken, asyncpg.UniqueViolationError):
        # a racing double-submit may have already made THIS Google account
        existing = await pool.fetchval(
            "SELECT username FROM ascent_accounts WHERE google_sub=$1",
            pending["sub"])
        if existing:
            return _finish_session(request, existing)
        return _name_retry(wants_json, "that name is taken — try another")
    log.info("account created via Gmail: %s", username)
    return _finish_session(request, username)


def _name_expired(wants_json: bool):
    if wants_json:
        raise HTTPException(400, "sign-in expired — start again")
    return RedirectResponse("/", status_code=303)


def _name_retry(wants_json: bool, msg: str):
    if wants_json:
        raise HTTPException(409, msg)
    return RedirectResponse(f"/auth/google/name?err={msg.replace(' ', '+')}",
                            status_code=303)


_NAME_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LINEAR ASCENT — name your climber</title>
<meta name="robots" content="noindex">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' fill='%23060606'/%3E%3Crect x='6' y='2' width='4' height='12' fill='%23f2b632'/%3E%3Crect x='4' y='12' width='8' height='2' fill='%23f2b632'/%3E%3C/svg%3E">
<link rel="stylesheet" href="/static/site/site.css?v=0.81.2">
<style>
  main.namestep { max-width: 60ch; margin: 3.5rem auto 4rem; padding: 0 1ch; }
  .signedin { color: var(--dim); }
  .signedin b { color: var(--gold); }
  .nameerr { color: var(--hurt); }
</style>
</head>
<body>
<header id="bar">
  <span id="bar-left">LINEAR ASCENT</span>
  <span id="bar-right">NAME YOUR CLIMBER</span>
</header>
<main class="namestep">
  <div class="card doorcard">
    <div class="eyebrow">NAME YOUR CLIMBER</div>
    <h2>Pick your name</h2>
    <p class="signedin">Signed in as <b>{{EMAIL}}</b>. Choose the one word
       the whole tower will know you by.</p>
    <form method="post" action="/auth/google/name">
      <label>CLIMBER NAME <span class="dim">— one word: letters, numbers,
             - or _</span>
             <input name="username" value="{{SUGG}}" maxlength="24"
             minlength="2" autocomplete="off" autofocus
             placeholder="one word" required></label>
      {{ERR}}
      <div class="options">
        <button class="opt gold-opt" type="submit">[ ENTER THE TOWER ]</button>
      </div>
    </form>
    <p class="dim" style="margin-top:.75rem">Permanent and unique across the
       world. Google proves your email; we never post anything and never read
       your mail.</p>
  </div>
</main>
</body>
</html>
"""


def _name_page(email: str, suggested: str, err: str) -> str:
    err_html = (f'<p class="nameerr">{htmlmod.escape(err)}</p>'
                if err else "")
    return (_NAME_PAGE
            .replace("{{EMAIL}}", htmlmod.escape(email))
            .replace("{{SUGG}}", htmlmod.escape(suggested, quote=True))
            .replace("{{ERR}}", err_html))


@router.get("/me")
async def me(request: Request) -> dict:
    username = session_user(request)
    if not username:
        return {"username": None}
    out = {"username": username, "auth_provider": None, "gmail": False}
    if db.ready():
        row = await (await db.get_pool()).fetchrow(
            "SELECT auth_provider, google_sub FROM ascent_accounts "
            "WHERE lower(username)=lower($1)", username)
        if row:
            out["auth_provider"] = row["auth_provider"]
            out["gmail"] = bool(row["google_sub"])
    return out
