"""worldd — shared world service for Linear Ascent.

The one authoritative world every Luna tenant's plugin talks to.
API surface lands per plans/001-worldd; execution per plans/002-execution.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import secrets as pysecrets
import time
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import auth, db
from .config import get_config

API_VERSION = 1

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("worldd")


@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_config()
    await db.init_db(cfg.database_url)
    yield
    await db.close_db()


app = FastAPI(title="ascent-worldd", version="0.3.0", lifespan=lifespan)

# Static shareables (e.g. /static/intro-movie/ — the 016 intro movie mock)
app.mount("/static",
          StaticFiles(directory=Path(__file__).resolve().parent.parent
                      / "static", html=True),
          name="static")


# ── Per-tenant rate limit (in-process token bucket; numInstances: 1) ─────

RATE_CAPACITY = int(os.environ.get("ASCENT_RATE_CAPACITY", "30"))
RATE_REFILL_PER_S = float(os.environ.get("ASCENT_RATE_REFILL", "5"))
_buckets: dict[str, list[float]] = {}  # tenant -> [tokens, last_ts]


def _rate_ok(tenant: str) -> bool:
    now = time.monotonic()
    tokens, last = _buckets.get(tenant, (float(RATE_CAPACITY), now))
    tokens = min(RATE_CAPACITY, tokens + (now - last) * RATE_REFILL_PER_S)
    if tokens < 1.0:
        _buckets[tenant] = [tokens, now]
        return False
    _buckets[tenant] = [tokens - 1.0, now]
    return True


@app.middleware("http")
async def request_log(request: Request, call_next):
    start = time.monotonic()
    tenant = request.headers.get("x-ascent-tenant", "-")
    if request.url.path.startswith("/v1/") and not _rate_ok(tenant):
        return JSONResponse({"detail": "rate limited"}, status_code=429)
    response = await call_next(request)
    ms = (time.monotonic() - start) * 1000
    log.info("req tenant=%s %s %s -> %d %.0fms",
             tenant, request.method, request.url.path,
             response.status_code, ms)
    return response


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "api": API_VERSION,
        "game": _game_version(),
        "server_time": dt.datetime.now(dt.timezone.utc).isoformat(),
        "db": db.ready(),
    }


def _game_version() -> str:
    try:
        from .gamepath import ensure_game_importable
        ensure_game_importable()
        from plugin_linear_ascent.version import VERSION
        return VERSION
    except Exception:
        return "unknown"


# ── Game API (tenant HMAC) ───────────────────────────────────────────────

class SceneIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)


class ActIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    option: str = Field(default="", max_length=64)
    text: str = Field(default="", max_length=64)
    idem: str = Field(default="", max_length=64)


@app.post("/v1/scene")
async def v1_scene(body: SceneIn,
                   tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import game
    scene = await game.run_scene(tenant, body.player)
    return {"scene": scene}


@app.post("/v1/act")
async def v1_act(body: ActIn,
                 tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import game
    scene = await game.run_act(tenant, body.player, body.option.strip(),
                               body.text.strip(), body.idem)
    return {"scene": scene}


@app.post("/v1/character")
async def v1_character(body: SceneIn,
                       tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import game
    return await game.run_character(tenant, body.player)


class ImportIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    doc: dict


@app.post("/v1/import")
async def v1_import(body: ImportIn,
                    tenant: str = Depends(auth.verify_tenant)) -> dict:
    """One-time local→world character migration (007 Phase 1). Only lands
    when the world has no playing character for this (tenant, player) —
    the world copy always wins over the local outage shadow."""
    from . import game
    return await game.run_import(tenant, body.player, body.doc)


# ── Presence (022 §003) ──────────────────────────────────────────────────

@app.post("/v1/presence")
async def v1_presence(body: SceneIn,
                      tenant: str = Depends(auth.verify_tenant)) -> dict:
    """Grade-2 liveness for the pane peek: the caller's floor and its
    hot/camped counts, straight from the 30s presence cache — cheap by
    construction."""
    from . import social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
            tenant, body.player)
        floor = 1
        if row:
            import json as _json
            floor = max(1, int(_json.loads(row["doc"]).get("floor") or 1))
        pres = await social._presence(conn)
    slot = pres["by_floor"].get(floor) or {}
    return {"floor": floor, "hot": int(slot.get("hot", 0)),
            "camped": int(slot.get("camped", 0))}


# ── Score & Community (plan 010) ─────────────────────────────────────────

@app.post("/v1/leaderboard")
async def v1_leaderboard(body: SceneIn,
                         tenant: str = Depends(auth.verify_tenant)) -> dict:
    """Every playing climber — level and gold visible (010 widened this
    deliberately; Muster kept bank as rank-only, the Score tab shows it)."""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT p.tenant, p.player, p.doc, p.updated_at, m.faction "
            "FROM ascent_players p "
            "LEFT JOIN ascent_faction_members m "
            "  ON m.tenant=p.tenant AND m.player=p.player "
            "WHERE p.doc->>'stage'='playing'")
    import json as _json

    from plugin_linear_ascent.engine import state as pstate
    now = pstate.now()
    out = []
    for r in rows:
        d = _json.loads(r["doc"])
        out.append({
            "name": d.get("name") or "a climber",
            "race": d.get("race") or "?",
            "clazz": d.get("clazz") or "?",
            "level": d.get("level", 1),
            "gold": d.get("gold", 0),
            "bank": d.get("bank", 0),
            "floor": d.get("unlocked_floor", 1),
            "faction": r["faction"] or "",
            "you": r["tenant"] == tenant and True or False,
            "last_seen_days": max(0, (now - r["updated_at"]).days),
        })
    out.sort(key=lambda e: (-e["level"], -(e["gold"] + e["bank"])))
    return {"players": out[:200], "total": len(out)}


class FactionCreateIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=3, max_length=24)
    banner: str = Field(default="wolf_howl", max_length=32)
    join_fee: int = Field(default=0, ge=0, le=500)
    weekly_dues: int = Field(default=5, ge=1, le=50)


class FactionJoinIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    faction: str = Field(min_length=3, max_length=24)


class FactionKickIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    target_tenant: str = Field(min_length=1, max_length=64)
    target_player: str = Field(min_length=1, max_length=128)


class FactionDonateIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    amount: int = Field(gt=0, le=1_000_000)


class FactionListIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    q: str = Field(default="", max_length=24)


class FactionNameIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=24)


class FactionTargetIn(BaseModel):
    player: str = Field(min_length=1, max_length=128)
    target_tenant: str = Field(min_length=1, max_length=64)
    target_player: str = Field(min_length=1, max_length=128)


@app.post("/v1/faction/list")
async def v1_faction_list(body: FactionListIn,
                          tenant: str = Depends(auth.verify_tenant)) -> dict:
    """The ledger: top 10 banners by table size; q searches server-side.
    Includes the caller's open request so the UI shows the pending state."""
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        rows = await factions.search_factions(conn, body.q)
        total = int(await conn.fetchval(
            "SELECT count(*) FROM ascent_factions") or 0)
        requested = await factions.my_request(conn, tenant, body.player)
        # 019: the board's call-to-action needs to know the viewer sits
        # at no table (members get no join buttons, no pitch)
        mine = await factions.member_row(conn, tenant, body.player)
    return {"factions": rows,
            "total": total,
            "requested": requested or "",
            "in_faction": (mine or {}).get("faction") or "",
            "banners": factions.banner_slugs(),
            "found_fee": factions.FOUND_FEE,
            "found_min_level": factions.FOUND_MIN_LEVEL}


@app.post("/v1/faction/status")
async def v1_faction_status(body: SceneIn,
                            tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions, social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            me = await factions.member_row(conn, tenant, body.player)
            if me is None:
                return {"faction": None}
            await factions.maybe_resolve(conn, me["faction"])
            panel = await social._faction_panel(
                conn, tenant, body.player, me["faction"])
    return {"faction": me["faction"], **panel}


@app.post("/v1/faction/create")
async def v1_faction_create(body: FactionCreateIn,
                            tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    name = body.name.strip()
    if not factions.NAME_RE.match(name):
        raise HTTPException(422, "3–24 letters, numbers, spaces, - or '")
    if body.banner not in factions.banner_slugs():
        raise HTTPException(422, "unknown banner")
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            if await factions.member_row(conn, tenant, body.player):
                raise HTTPException(409, "you already sit at a table — "
                                         "leave it first")
            row = await conn.fetchrow(
                "SELECT doc FROM ascent_players WHERE tenant=$1 AND "
                "player=$2 FOR UPDATE", tenant, body.player)
            if row is None:
                raise HTTPException(404, "no character")
            import json as _json
            doc = _json.loads(row["doc"])
            if doc.get("stage") != "playing":
                raise HTTPException(409, "finish character creation first")
            if int(doc.get("level", 1)) < factions.FOUND_MIN_LEVEL:
                raise HTTPException(
                    403, "the hall charters banners for level "
                         f"{factions.FOUND_MIN_LEVEL}+ climbers")
            if doc.get("gold", 0) < factions.FOUND_FEE:
                raise HTTPException(
                    402, f"founding a banner costs ◈ {factions.FOUND_FEE}")
            taken = await conn.fetchval(
                "SELECT 1 FROM ascent_factions WHERE name=$1", name)
            if taken:
                raise HTTPException(409, "that banner already flies")
            doc["gold"] -= factions.FOUND_FEE
            await conn.execute(
                "UPDATE ascent_players SET doc=$3, updated_at=now() "
                "WHERE tenant=$1 AND player=$2",
                tenant, body.player, _json.dumps(doc))
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " note) VALUES ($1,$2,'faction_found',$3,$4)",
                tenant, body.player, -factions.FOUND_FEE, name)
            await factions.create_faction(
                conn, tenant, body.player, name, body.banner,
                doc.get("name") or body.player,
                join_fee=body.join_fee, weekly_dues=body.weekly_dues)
    return {"ok": True, "faction": name}


@app.post("/v1/faction/join")
async def v1_faction_join(body: FactionJoinIn,
                          tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            err = await factions.join_faction(conn, tenant, body.player,
                                              body.faction)
            if err:
                raise HTTPException(409, err)
    return {"ok": True, "faction": body.faction}


@app.post("/v1/faction/leave")
async def v1_faction_leave(body: SceneIn,
                           tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await factions.leave_faction(conn, tenant, body.player)
    return {"ok": True}


@app.post("/v1/faction/kick")
async def v1_faction_kick(body: FactionKickIn,
                          tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            me = await factions.member_row(conn, tenant, body.player)
            if me is None or me["role"] != "steward":
                raise HTTPException(403, "only the steward removes members")
            target = await factions.member_row(
                conn, body.target_tenant, body.target_player)
            if target is None or target["faction"] != me["faction"]:
                raise HTTPException(404, "not at your table")
            if (body.target_tenant, body.target_player) == \
                    (tenant, body.player):
                raise HTTPException(422, "leave, don't kick yourself")
            if target["role"] == "steward":
                # 015: admins don't kick admins — the founder can
                founder = await conn.fetchrow(
                    "SELECT founder_tenant, founder_player "
                    "FROM ascent_factions WHERE name=$1", me["faction"])
                if (founder["founder_tenant"],
                        founder["founder_player"]) != (tenant, body.player):
                    raise HTTPException(
                        403, "only the founder unseats an admin")
            await conn.execute(
                "DELETE FROM ascent_faction_members "
                "WHERE tenant=$1 AND player=$2",
                body.target_tenant, body.target_player)
    return {"ok": True}


@app.post("/v1/faction/donate")
async def v1_faction_donate(body: FactionDonateIn,
                            tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            err = await factions.donate(conn, tenant, body.player,
                                        body.amount)
            if err:
                raise HTTPException(409, err)
    return {"ok": True}


@app.post("/v1/faction/enter")
async def v1_faction_enter(body: SceneIn,
                           tenant: str = Depends(auth.verify_tenant)) -> dict:
    """Steward enters THIS week's world challenge — paid from the store."""
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            err = await factions.enter_week(conn, tenant, body.player)
            if err:
                raise HTTPException(409, err)
    return {"ok": True}


@app.post("/v1/faction/board")
async def v1_faction_board(body: SceneIn,
                           tenant: str = Depends(auth.verify_tenant)) -> dict:
    """The COMMUNITY news board — read-only, any tenant. Resolves any
    pending weeks first so 'last week' is always settled."""
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            names = await conn.fetch("SELECT name FROM ascent_factions")
            for r in names:
                await factions.maybe_resolve(conn, r["name"])
            await factions.maybe_post_week(conn)
            return await factions.board(conn)


# ── The faction desk (plan 015) ──────────────────────────────────────────

def _desk_err(err: str | None) -> None:
    if err:
        code = 403 if "only" in err else 409
        raise HTTPException(code, err)


@app.post("/v1/faction/detail")
async def v1_faction_detail(body: FactionNameIn,
                            tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await factions.maybe_resolve(conn, body.name)
            d = await factions.faction_detail(conn, tenant, body.player,
                                              body.name)
    if d is None:
        raise HTTPException(404, "that banner no longer flies")
    return d


@app.post("/v1/faction/request")
async def v1_faction_request(body: FactionNameIn,
                             tenant: str = Depends(auth.verify_tenant)) -> dict:
    """File a join request — no gold moves until an admin accepts."""
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.request_join(conn, tenant, body.player,
                                                  body.name))
    return {"ok": True, "requested": body.name}


@app.post("/v1/faction/cancel_request")
async def v1_faction_cancel_request(
        body: SceneIn, tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await factions.cancel_request(conn, tenant, body.player)
    return {"ok": True}


@app.post("/v1/faction/approve")
async def v1_faction_approve(body: FactionTargetIn,
                             tenant: str = Depends(auth.verify_tenant)) -> dict:
    """Admin accepts a request: the join fee is charged HERE (kept in the
    request queue if the requester can't cover it)."""
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.approve_request(
                conn, tenant, body.player,
                body.target_tenant, body.target_player))
    return {"ok": True}


@app.post("/v1/faction/reject")
async def v1_faction_reject(body: FactionTargetIn,
                            tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.reject_request(
                conn, tenant, body.player,
                body.target_tenant, body.target_player))
    return {"ok": True}


@app.post("/v1/faction/rename")
async def v1_faction_rename(body: FactionNameIn,
                            tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.rename_faction(conn, tenant,
                                                    body.player, body.name))
    return {"ok": True, "name": body.name.strip()}


@app.post("/v1/faction/promote")
async def v1_faction_promote(body: FactionTargetIn,
                             tenant: str = Depends(auth.verify_tenant)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.promote_member(
                conn, tenant, body.player,
                body.target_tenant, body.target_player))
    return {"ok": True}


# ── Self-service enrollment (public, rate-limited) ──────────────────────

ENROLL_PER_HOUR = int(os.environ.get("ASCENT_ENROLL_PER_HOUR", "5"))
_enroll_hits: dict[str, list[float]] = {}


def _enroll_ok(ip: str) -> bool:
    now = time.monotonic()
    hits = [t for t in _enroll_hits.get(ip, []) if now - t < 3600]
    if len(hits) >= ENROLL_PER_HOUR:
        _enroll_hits[ip] = hits
        return False
    hits.append(now)
    _enroll_hits[ip] = hits
    return True


class EnrollIn(BaseModel):
    install_id: str = Field(min_length=8, max_length=128)
    name_hint: str = Field(default="", max_length=32,
                           pattern=r"^[a-zA-Z0-9\-_ ]*$")


@app.post("/v1/enroll")
async def enroll(body: EnrollIn, request: Request) -> dict:
    """One-click world signup for a Luna install. Idempotent per install_id.

    No auth by design: the install_id is a client-generated random token,
    and the response is the tenant's own credentials. Rate limited per IP.
    """
    ip = request.client.host if request.client else "?"
    if not _enroll_ok(ip):
        raise HTTPException(429, "enrollment rate limited; try again later")
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT tenant, secret FROM ascent_tenants WHERE install_id = $1",
        body.install_id)
    if row:
        return {"tenant": row["tenant"], "secret": row["secret"],
                "existing": True}
    hint = "".join(c for c in body.name_hint.lower()
                   if c.isalnum() or c == "-")[:20]
    for _ in range(5):
        tenant = f"{hint or 'luna'}-{pysecrets.token_hex(4)}"
        secret = pysecrets.token_hex(32)
        try:
            await pool.execute(
                "INSERT INTO ascent_tenants (tenant, secret, install_id) "
                "VALUES ($1, $2, $3)", tenant, secret, body.install_id)
        except Exception:
            # either a tenant-name collision (reroll) or a concurrent
            # enroll won the install_id race (return theirs)
            row = await pool.fetchrow(
                "SELECT tenant, secret FROM ascent_tenants "
                "WHERE install_id = $1", body.install_id)
            if row:
                return {"tenant": row["tenant"], "secret": row["secret"],
                        "existing": True}
            continue
        log.info("tenant enrolled: %s (ip=%s)", tenant, ip)
        return {"tenant": tenant, "secret": secret, "existing": False}
    raise HTTPException(500, "could not allocate tenant")


# ── Admin (X-Admin-Key) ──────────────────────────────────────────────────

def _admin(x_admin_key: str = Header(default="")) -> None:
    cfg = get_config()
    if not cfg.admin_key or x_admin_key != cfg.admin_key:
        raise HTTPException(401, "bad admin key")


class TenantIn(BaseModel):
    tenant: str = Field(min_length=2, max_length=64,
                        pattern=r"^[a-z0-9][a-z0-9\-_]+$")


@app.post("/admin/tenants", dependencies=[Depends(_admin)])
async def create_tenant(body: TenantIn) -> dict:
    secret = pysecrets.token_hex(32)
    pool = await db.get_pool()
    try:
        await pool.execute(
            "INSERT INTO ascent_tenants (tenant, secret) VALUES ($1,$2)",
            body.tenant, secret)
    except Exception:
        raise HTTPException(409, "tenant exists")
    log.info("tenant created: %s", body.tenant)
    return {"tenant": body.tenant, "secret": secret}


@app.get("/admin/tenants", dependencies=[Depends(_admin)])
async def list_tenants() -> dict:
    pool = await db.get_pool()
    rows = await pool.fetch(
        "SELECT tenant, created_at, disabled FROM ascent_tenants "
        "ORDER BY created_at")
    return {"tenants": [
        {"tenant": r["tenant"], "created_at": r["created_at"].isoformat(),
         "disabled": r["disabled"]} for r in rows]}


@app.get("/admin/ledger", dependencies=[Depends(_admin)])
async def ledger_audit(tenant: str = "", player: str = "",
                       limit: int = 100) -> dict:
    pool = await db.get_pool()
    rows = await pool.fetch(
        "SELECT tenant, player, created_at, kind, gold, xp, note "
        "FROM ascent_ledger "
        "WHERE ($1 = '' OR tenant = $1) AND ($2 = '' OR player = $2) "
        "ORDER BY id DESC LIMIT $3",
        tenant, player, min(max(limit, 1), 1000))
    return {"entries": [
        {"tenant": r["tenant"], "player": r["player"],
         "at": r["created_at"].isoformat(), "kind": r["kind"],
         "gold": r["gold"], "xp": r["xp"], "note": r["note"]}
        for r in rows]}


@app.get("/admin/world", dependencies=[Depends(_admin)])
async def world_status() -> dict:
    pool = await db.get_pool()
    frontier = await pool.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    players = await pool.fetchrow(
        "SELECT count(*) AS n FROM ascent_players")
    ledger = await pool.fetchrow(
        "SELECT count(*) AS n, coalesce(sum(gold),0) AS gold "
        "FROM ascent_ledger")
    return {
        "frontier": int(frontier["value"]) if frontier else 1,
        "players": players["n"],
        "ledger_rows": ledger["n"],
        "ledger_gold_net": int(ledger["gold"]),
    }
