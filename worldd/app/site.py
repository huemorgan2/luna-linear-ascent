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
import json
import logging
import os
import re
import secrets as pysecrets
import time
from pathlib import Path

import asyncpg
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from . import db
from .config import get_config

log = logging.getLogger("worldd.site")

router = APIRouter()

SITE_DIR = Path(__file__).resolve().parent.parent / "static" / "site"


# ── The page ─────────────────────────────────────────────────────────────

@router.get("/", include_in_schema=False)
async def homepage():
    return FileResponse(SITE_DIR / "index.html", media_type="text/html")


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
# A username and a password. The name follows the climber-name law
# (2–24 strokes) with the mason's alphabet: letters, numbers, spaces,
# - _ ' — it will be carved on the Stone one day, so it must carve.

USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '\-_]{1,23}$")
PASSWORD_MIN = 4
PASSWORD_MAX = 128

SESSION_COOKIE = "ascent_session"
SESSION_MAX_AGE = 30 * 24 * 3600

SIGNUP_PER_HOUR = int(os.environ.get("ASCENT_SIGNUP_PER_HOUR", "20"))
_signup_hits: dict[str, list[float]] = {}


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


async def _credentials(request: Request) -> tuple[str, str, bool]:
    """(username, password, wants_json) from a JSON fetch or a plain
    urlencoded form POST — the page must work with scripts off."""
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        body = await request.json()
        return (str(body.get("username", "")).strip(),
                str(body.get("password", "")), True)
    form = await request.form()
    return (str(form.get("username", "")).strip(),
            str(form.get("password", "")), False)


def _door_response(request: Request, username: str, wants_json: bool,
                   note: str):
    if wants_json:
        resp = JSONResponse({"ok": True, "username": username,
                             "note": note})
    else:
        resp = RedirectResponse("/#door", status_code=303)
    proto = request.headers.get("x-forwarded-proto",
                                request.url.scheme)
    resp.set_cookie(SESSION_COOKIE, _session_token(username),
                    max_age=SESSION_MAX_AGE, httponly=True,
                    samesite="lax", secure=(proto == "https"), path="/")
    return resp


def _door_error(status: int, msg: str, wants_json: bool):
    if wants_json:
        raise HTTPException(status, msg)
    return RedirectResponse(f"/?door_err={msg.replace(' ', '+')}#door",
                            status_code=303)


@router.post("/signup")
async def signup(request: Request):
    username, password, wants_json = await _credentials(request)
    ip = request.client.host if request.client else "?"
    if not _signup_ok(ip):
        return _door_error(429, "too many doors opened — try later",
                           wants_json)
    if not USERNAME_RE.match(username):
        return _door_error(
            422, "2 to 24 strokes — letters, numbers, spaces, - _ '",
            wants_json)
    if not (PASSWORD_MIN <= len(password) <= PASSWORD_MAX):
        return _door_error(
            422, f"a password of {PASSWORD_MIN}+ strokes", wants_json)
    pool = await db.get_pool()
    try:
        await pool.execute(
            "INSERT INTO ascent_accounts (username, pw_hash) "
            "VALUES ($1, $2)", username, _hash_pw(password))
    except asyncpg.UniqueViolationError:
        return _door_error(409, "that name is already climbing",
                           wants_json)
    log.info("account created: %s (ip=%s)", username, ip)
    return _door_response(request, username, wants_json,
                          "the name is yours — the tower knows it now")


@router.post("/login")
async def login(request: Request):
    username, password, wants_json = await _credentials(request)
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT username, pw_hash FROM ascent_accounts "
        "WHERE lower(username) = lower($1)", username)
    if row is None or not _check_pw(password, row["pw_hash"]):
        return _door_error(401, "the door does not know that knock",
                           wants_json)
    return _door_response(request, row["username"], wants_json,
                          "welcome back")


@router.post("/logout")
async def logout(request: Request):
    wants_json = "application/json" in request.headers.get("accept", "")
    resp = JSONResponse({"ok": True}) if wants_json \
        else RedirectResponse("/", status_code=303)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/me")
async def me(request: Request) -> dict:
    return {"username": session_user(request)}
