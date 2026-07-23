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

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
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
        "server_time": dt.datetime.now(dt.timezone.utc).isoformat(),
        "db": db.ready(),
    }


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
