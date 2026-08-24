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
from html import escape as html_escape
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

# 067: the two 3D modules on /play — kill finisher and the Labs arena
# 071: figure3d is its own folder (Labs isolation — drop = delete it)
FIGHT3D_URL = "/static/site/fight3d/fight3d.js?v=13"
ARENA3D_URL = "/static/site/fight3d/arena3d.js?v=4"
FIGURE3D_URL = "/static/site/figure3d/figure3d.js?v=3"


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


class FactionFoundIn(BaseModel):
    name: str = Field(min_length=3, max_length=24)
    banner: str = Field(default="wolf_howl", max_length=32)
    join_fee: int = Field(default=0, ge=0, le=500)
    weekly_dues: int = Field(default=5, ge=1, le=50)
    color: str = Field(default="", max_length=24)


class FactionColorIn(BaseModel):
    color: str = Field(min_length=1, max_length=24)


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


async def _web_gmail(player: str) -> bool:
    """010: the website account is Gmail-connected iff it carries a
    google_sub. New accounts always are (signup is Gmail); only legacy
    password accounts come back False — and lose the portrait until linked."""
    pool = await db.get_pool()
    sub = await pool.fetchval(
        "SELECT google_sub FROM ascent_accounts "
        "WHERE lower(username)=lower($1)", player)
    return sub is not None


def _card(scene_dict: dict, portrait_locked: bool = False) -> dict:
    """The pane's contract for scene answers — same shape routes.py
    returns to Luna, fragment rendered by the same renderer."""
    ensure_game_importable()
    from plugin_linear_ascent.engine.scene import Scene
    from plugin_linear_ascent.render import render_scene_fragment
    scene = Scene.from_dict(scene_dict)
    # 010: gate the player portrait behind a Gmail link (web-only). Set as a
    # runtime attribute the renderer reads via getattr — never serialized.
    if portrait_locked:
        scene.portrait_locked = True
    return {"ok": True, "scene_id": scene.scene_id,
            "event_kind": scene.event_kind, "headline": scene.headline,
            "fragment": render_scene_fragment(scene),
            # 050: a rule said no — the pane toasts this line and keeps
            # the card it has instead of swapping the fragment in.
            "refusal": getattr(scene, "refusal", "")}


def _desk_err(err: str | None) -> None:
    if err:
        from . import factions
        raise HTTPException(factions.desk_code(err), err)


# ── The page ─────────────────────────────────────────────────────────────

@router.get("/play", include_in_schema=False)
async def play_page(request: Request):
    """The pane, full-viewport — the exact HTML Luna renders, wired to
    /play/api with cookie auth. Signed out → the door, sign-in tab up."""
    user = site.session_user(request)
    if not user:
        return RedirectResponse("/#door-signin", status_code=303)
    ensure_game_importable()
    from plugin_linear_ascent.pane import render_pane
    page = render_pane(api_base="/play/api", web=True)
    # Funnel Fighters rides only the WEBSITE's /play — injected here, so
    # the plugin (and every Luna chat surface) stays tracker-free. The
    # tag's data-user lets funnel.js identify without an extra fetch;
    # usernames are names.is_legal (letters, digits, - _), safe to embed.
    # data-door=signup|signin: the Gmail door lands here with ?door=…, and
    # funnel.js turns it into the signup / signin_ok event.
    door = request.query_params.get("door", "")
    door_attr = f' data-door="{door}"' if door in ("signup", "signin") else ""
    tag = (f'<script src="/static/site/funnel.js?v=2" '
           f'data-user="{html_escape(user)}"{door_attr} defer></script>')
    # PLAN3: the live 3D kill finisher — website-only, like funnel. The
    # importmap must land in the initial HTML, before the module loads;
    # fight3d.js watches #game for data-kill3d cards and degrades to the
    # GIF when WebGL or a model is missing.
    # 067: arena3d.js (the Labs turn-based stage) imports fight3d's
    # primitives through the "fight3d" map entry — the SAME URL as the
    # script tag, so the browser holds one module instance (one kill
    # observer, one asset cache). Bump both together via FIGHT3D_URL.
    tag += ('<script type="importmap">{"imports":{"three":'
            '"/static/site/fight3d/vendor/three.module.js",'
            f'"fight3d":"{FIGHT3D_URL}"}}}}</script>'
            f'<script type="module" src="{FIGHT3D_URL}"></script>'
            f'<script type="module" src="{ARENA3D_URL}"></script>'
            f'<script type="module" src="{FIGURE3D_URL}"></script>')
    return HTMLResponse(page.replace("</head>", tag + "</head>", 1))


# ── The game loop ────────────────────────────────────────────────────────

@router.post("/play/api/pane/scene")
async def pane_scene(ident: tuple = Depends(_identity)) -> dict:
    player, display = ident
    from . import game
    locked = not await _web_gmail(player)
    scene = await game.run_scene(WEB_TENANT, player, display_name=display)
    return _card(scene, portrait_locked=locked)


@router.post("/play/api/act")
async def act(body: ActIn, ident: tuple = Depends(_identity)) -> dict:
    # no idem: a browser click never auto-retries; the row lock plus the
    # engine's stale-option answer already make double-clicks harmless
    player, display = ident
    from . import game
    locked = not await _web_gmail(player)
    scene = await game.run_act(WEB_TENANT, player, body.option.strip(),
                               body.text.strip(), "",
                               display_name=display)
    return _card(scene, portrait_locked=locked)


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
        online = await social.online_count(conn)
        head = await social.feed_head(conn)
    return {"scene_id": scene_id, "floor_presence": int(pres["hot"]),
            "online": online, "feed_head": head}


@router.get("/play/api/pane/playing/feed")
async def pane_playing_feed(scope: str = "world", since: int = 0,
                            ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await social.playing_feed(conn, WEB_TENANT, player,
                                         scope, since)


@router.post("/play/api/pane/room_more")
async def pane_room_more(ident: tuple = Depends(_identity)) -> dict:
    """The presence grid's MORE — the rest of the viewer's room."""
    player, _ = ident
    from . import social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await social.room_more(conn, WEB_TENANT, player)


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


@router.post("/play/api/pane/faction/found")
async def faction_found(body: FactionFoundIn,
                        ident: tuple = Depends(_identity)) -> dict:
    """061: raise a banner from the COMMUNITY desk — the same charter
    the Guildhall signs, without walking there."""
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            code, err = await factions.found_faction(
                conn, WEB_TENANT, player, body.name, body.banner,
                body.join_fee, body.weekly_dues, color=body.color)
            if err:
                raise HTTPException(code, err)
    return {"ok": True, "faction": body.name.strip()}


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


@router.post("/play/api/pane/faction/recolor")
async def faction_recolor(body: FactionColorIn,
                          ident: tuple = Depends(_identity)) -> dict:
    """010: the admin desk's color row — a named 1-bit ink for the
    banner, beside rename."""
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.recolor_faction(conn, WEB_TENANT,
                                                     player, body.color))
    return {"ok": True, "color": body.color}


@router.post("/play/api/pane/faction/enter")
async def faction_enter(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import factions
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            _desk_err(await factions.enter_week(conn, WEB_TENANT, player))
    return {"ok": True}


# ── 051: the postbox (cookie flavor) ─────────────────────────────────────

class FeedbackAttachmentIn(BaseModel):
    mime: str = Field(max_length=64)
    data: str = Field(max_length=4_000_000)


class FeedbackCreateIn(BaseModel):
    subject: str = Field(default="", max_length=200)
    body: str = Field(default="", max_length=8000)
    attachments: list[FeedbackAttachmentIn] = Field(
        default_factory=list, max_length=8)


class FeedbackThreadIn(BaseModel):
    id: int = Field(gt=0)
    as_admin: bool = False


class FeedbackReplyIn(BaseModel):
    id: int = Field(gt=0)
    body: str = Field(default="", max_length=8000)
    attachments: list[FeedbackAttachmentIn] = Field(
        default_factory=list, max_length=8)
    as_admin: bool = False


@router.post("/play/api/pane/feedback/create")
async def feedback_create(body: FeedbackCreateIn,
                          ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await feedback.create(
                conn, WEB_TENANT, player, body.subject, body.body,
                [a.model_dump() for a in body.attachments])


@router.get("/play/api/pane/feedback/mine")
async def feedback_mine(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await feedback.my_threads(conn, WEB_TENANT, player)


@router.post("/play/api/pane/feedback/thread")
async def feedback_thread(body: FeedbackThreadIn,
                          ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await feedback.thread(conn, WEB_TENANT, player, body.id,
                                         as_admin=body.as_admin)


@router.post("/play/api/pane/feedback/reply")
async def feedback_reply(body: FeedbackReplyIn,
                         ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await feedback.reply(
                conn, WEB_TENANT, player, body.id, body.body,
                [a.model_dump() for a in body.attachments],
                as_admin=body.as_admin)


@router.get("/play/api/pane/feedback/unread")
async def feedback_unread(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await feedback.unread(conn, WEB_TENANT, player)


@router.get("/play/api/pane/feedback/admin")
async def feedback_admin(ident: tuple = Depends(_identity)) -> dict:
    player, _ = ident
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await feedback.admin_threads(conn, WEB_TENANT, player)


@router.get("/play/api/pane/feedback/att/{att_id}")
async def feedback_att(att_id: int, ident: tuple = Depends(_identity)):
    player, _ = ident
    from fastapi.responses import Response
    from . import feedback
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        mime, raw = await feedback.attachment(conn, WEB_TENANT, player,
                                              att_id)
    return Response(content=raw, media_type=mime,
                    headers={"Cache-Control": "private, max-age=3600"})


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
