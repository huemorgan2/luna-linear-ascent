"""005 web play — the game itself, at linearascent.net/play.

The website is a tenant of the world: reserved id `web`, one character
per account at (web, lower(username)). These routes mirror the pane's
surface (the plugin's routes.py serves the same shapes to Luna) behind
the site session cookie instead of tenant HMAC — the same game.run_scene
/ run_act and shared read bodies underneath, so the browser and Luna
climb one world.

Auth belt and suspenders: the cookie is SameSite=Lax (no foreign-site
POST cookies), and any POST that does carry an Origin must match the
request host. The web tenant's HMAC secret exists only as a row nobody
reads — auth.py refuses tenant 'web' outright.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from . import db, ratelimit, site
from .gamepath import ensure_game_importable

WEB_TENANT = "web"

log = logging.getLogger("worldd.webplay")

router = APIRouter()


# ── Bodies (mirror the plugin's routes.py, minus the chat-bridge ids) ────

class ActIn(BaseModel):
    option: str = Field(default="", max_length=64)
    text: str = Field(default="", max_length=200)
    mode: str = Field(default="", max_length=16)
    scene_id: str = Field(default="", max_length=64)


class FactionNameIn(BaseModel):
    name: str = Field(min_length=1, max_length=24)


class FactionTargetIn(BaseModel):
    tenant: str = Field(min_length=1, max_length=64)
    player: str = Field(min_length=1, max_length=128)


# ── The guard ────────────────────────────────────────────────────────────

def _identity(request: Request) -> tuple[str, str]:
    """(player, display_name) for the session — 401 without a live
    cookie, 403 on a cross-origin POST, 429 past the per-account bucket."""
    username = site.session_user(request)
    if not username:
        raise HTTPException(401, "sign in")
    if request.method == "POST":
        origin = request.headers.get("origin", "")
        if origin:
            host = request.headers.get("x-forwarded-host") \
                or request.headers.get("host") or ""
            if urlsplit(origin).netloc.lower() != host.lower():
                raise HTTPException(403, "cross-origin")
    if not ratelimit.allow(f"web:{username.lower()}"):
        raise HTTPException(429, "rate limited")
    return username.lower(), username


def _card(scene_dict: dict) -> dict:
    """The pane's contract for scene answers — same shape routes.py
    returns to Luna, fragment rendered by the same renderer."""
    ensure_game_importable()
    from plugin_linear_ascent.engine.scene import Scene
    from plugin_linear_ascent.render import render_scene_fragment
    scene = Scene.from_dict(scene_dict)
    return {"ok": True, "scene_id": scene.scene_id,
            "event_kind": scene.event_kind, "headline": scene.headline,
            "fragment": render_scene_fragment(scene)}


def _desk_err(err: str | None) -> None:
    if err:
        from . import factions
        raise HTTPException(factions.desk_code(err), err)


# ── The page ─────────────────────────────────────────────────────────────

@router.get("/play", include_in_schema=False)
async def play_page(request: Request):
    """The pane, full-viewport — the exact HTML Luna renders, wired to
    /play/api with cookie auth. Signed out → the door, sign-in tab up."""
    if not site.session_user(request):
        return RedirectResponse("/#door-signin", status_code=303)
    ensure_game_importable()
    from plugin_linear_ascent.pane import render_pane
    return HTMLResponse(render_pane(api_base="/play/api", web=True))


# ── The game loop ────────────────────────────────────────────────────────

@router.post("/play/api/pane/scene")
async def pane_scene(ident: tuple = Depends(_identity)) -> dict:
    player, display = ident
    from . import game
    scene = await game.run_scene(WEB_TENANT, player, display_name=display)
    return _card(scene)


@router.post("/play/api/act")
async def act(body: ActIn, ident: tuple = Depends(_identity)) -> dict:
    # no idem: a browser click never auto-retries; the row lock plus the
    # engine's stale-option answer already make double-clicks harmless
    player, display = ident
    from . import game
    scene = await game.run_act(WEB_TENANT, player, body.option.strip(),
                               body.text.strip(), "",
                               display_name=display)
    return _card(scene)


@router.get("/play/api/pane/peek")
async def pane_peek(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
            WEB_TENANT, player)
        scene_id = ""
        if row:
            scene_id = ((json.loads(row["doc"]).get("scene") or {})
                        .get("scene_id") or "")
        pres = await social.floor_presence(conn, WEB_TENANT, player)
    return {"scene_id": scene_id, "floor_presence": int(pres["hot"])}


# ── Score & community ────────────────────────────────────────────────────

@router.get("/play/api/pane/score")
async def pane_score(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await social.leaderboard(conn, WEB_TENANT, player)


@router.get("/play/api/pane/community")
async def pane_community(ident: tuple = Depends(_identity)) -> dict:
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await factions.settled_board(conn)


@router.get("/play/api/pane/factions")
async def pane_factions(q: str = "",
                        ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await factions.browse(conn, WEB_TENANT, player, q[:24])


# ── The faction desk (015 surface, cookie flavor) ────────────────────────

@router.post("/play/api/pane/faction/detail")
async def faction_detail(body: FactionNameIn,
                         ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await factions.maybe_resolve(conn, body.name)
            d = await factions.faction_detail(conn, WEB_TENANT, player,
                                              body.name)
    if d is None:
        raise HTTPException(404, "that banner no longer flies")
    return d


@router.post("/play/api/pane/faction/request")
async def faction_request(body: FactionNameIn,
                          ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.request_join(conn, WEB_TENANT, player,
                                                  body.name))
    return {"ok": True, "requested": body.name}


@router.post("/play/api/pane/faction/cancel_request")
async def faction_cancel_request(
        ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await factions.cancel_request(conn, WEB_TENANT, player)
    return {"ok": True}


@router.post("/play/api/pane/faction/approve")
async def faction_approve(body: FactionTargetIn,
                          ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.approve_request(
                conn, WEB_TENANT, player, body.tenant, body.player))
    return {"ok": True}


@router.post("/play/api/pane/faction/reject")
async def faction_reject(body: FactionTargetIn,
                         ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.reject_request(
                conn, WEB_TENANT, player, body.tenant, body.player))
    return {"ok": True}


@router.post("/play/api/pane/faction/kick")
async def faction_kick(body: FactionTargetIn,
                       ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.kick_member(
                conn, WEB_TENANT, player, body.tenant, body.player))
    return {"ok": True}


@router.post("/play/api/pane/faction/promote")
async def faction_promote(body: FactionTargetIn,
                          ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.promote_member(
                conn, WEB_TENANT, player, body.tenant, body.player))
    return {"ok": True}


@router.post("/play/api/pane/faction/rename")
async def faction_rename(body: FactionNameIn,
                         ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.rename_faction(conn, WEB_TENANT,
                                                    player, body.name))
    return {"ok": True, "name": body.name.strip()}


@router.post("/play/api/pane/faction/enter")
async def faction_enter(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.enter_week(conn, WEB_TENANT, player))
    return {"ok": True}


# ── Sigil art (public, like the pane shell itself) ───────────────────────

_SLUG_RE = re.compile(r"[a-z0-9_]{1,32}")


@router.get("/play/api/art/factions/{slug}.png")
async def faction_banner(slug: str):
    if not _SLUG_RE.fullmatch(slug):
        raise HTTPException(404, "no such sigil")
    ensure_game_importable()
    import plugin_linear_ascent as pkg
    path = (Path(pkg.__file__).resolve().parent / "content" / "art"
            / "banners" / "factions" / f"{slug}_320x112.png")
    if not path.exists():
        raise HTTPException(404, "no such sigil")
    return FileResponse(path, media_type="image/png",
                        headers={"Cache-Control": "max-age=86400"})
