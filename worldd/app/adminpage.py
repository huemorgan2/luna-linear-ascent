"""The admin desk page — players and feedback, behind the admin key.

/admin serves a small static console (PLAYERS and FEEDBACK tabs); its
JSON api lives under /admin/api/* and is gated by the same X-Admin-Key
header as the rest of the /admin endpoints. PLAYERS: the top 100 by the
leaderboard's own ordering, a search that finds anyone, and a player
page where energy, xp, gold and bank can be set and weapons of every
line granted straight into the pack. FEEDBACK: the 051 postbox from the
desk side — threads, messages, replies signed as the admin.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from . import db, feedback, site, social
from .config import get_config
from .game import pstate  # gamepath made the plugin importable

from plugin_linear_ascent import economy  # noqa: E402

router = APIRouter()

SITE_DIR = Path(__file__).resolve().parent.parent / "static" / "site"


def _admin(request: Request, x_admin_key: str = Header(default="")) -> None:
    # two ways past the lock: the X-Admin-Key that guards main.py's
    # /admin endpoints, or a signed-in site session whose username is a
    # feedback admin (004: a name is an identity) — huemorgan3 walks in
    # without typing the key.
    cfg = get_config()
    if cfg.admin_key and x_admin_key == cfg.admin_key:
        return
    user = site.session_user(request)
    if user and user.lower() in feedback.admin_names():
        return
    raise HTTPException(401, "bad admin key")


def _admin_ident() -> tuple[str, str]:
    """The key-holder acts as the first configured feedback admin —
    004 name-is-identity holds even when nobody typed a password."""
    names = sorted(feedback.admin_names())
    return "web", (names[0] if names else "admin")


# ── The page ─────────────────────────────────────────────────────────────

@router.get("/admin", include_in_schema=False)
async def admin_page():
    return FileResponse(SITE_DIR / "admin.html", media_type="text/html")


# ── Players ──────────────────────────────────────────────────────────────

def _row_summary(tenant: str, player: str, doc: dict, updated_at) -> dict:
    return {
        "tenant": tenant, "player": player,
        "name": doc.get("name") or "a climber",
        "race": doc.get("race") or "?",
        "stage": doc.get("stage") or "?",
        "level": doc.get("level", 1),
        "xp": doc.get("xp", 0),
        "gold": doc.get("gold", 0),
        "bank": doc.get("bank", 0),
        "floor": doc.get("floor", 1),
        "unlocked_floor": doc.get("unlocked_floor", 1),
        "updated_at": updated_at.isoformat() if updated_at else "",
    }


@router.get("/admin/api/players", dependencies=[Depends(_admin)])
async def players(q: str = "", limit: int = 100) -> dict:
    """No q: the top of the tower, leaderboard ordering (level, then
    wealth). With q: anyone whose character name, player key, or luna
    user matches."""
    pool = await db.get_pool()
    rows = await pool.fetch(
        "SELECT tenant, player, doc, updated_at FROM ascent_players "
        "WHERE $1 = '' OR doc->>'name' ILIKE '%'||$1||'%' "
        "   OR player ILIKE '%'||$1||'%' "
        "   OR doc->>'luna_user' ILIKE '%'||$1||'%' "
        "ORDER BY coalesce((doc->>'level')::int, 1) DESC, "
        "  coalesce((doc->>'gold')::numeric, 0)"
        "   + coalesce((doc->>'bank')::numeric, 0) DESC "
        "LIMIT $2", q.strip(), min(max(limit, 1), 200))
    total = await pool.fetchval("SELECT count(*) FROM ascent_players")
    return {"players": [
        _row_summary(r["tenant"], r["player"], json.loads(r["doc"]),
                     r["updated_at"]) for r in rows],
        "total": int(total)}


def _gear_name(slug: str) -> str:
    g = economy.FORGE.get(slug or "")
    return g.name if g else (slug or "")


def _detail(tenant: str, player: str, doc: dict, updated_at) -> dict:
    out = _row_summary(tenant, player, doc, updated_at)
    try:
        out["energy"] = pstate.energy_now(doc)
        out["energy_cap"] = pstate.energy_cap_of(doc)
    except Exception:   # pre-energy docs never crash the desk
        out["energy"] = out["energy_cap"] = None
    out["hp"] = doc.get("hp")
    out["luna_user"] = doc.get("luna_user", "")
    out["training"] = doc.get("training") or {}
    out["slots"] = doc.get("slots", 1)
    out["gear"] = {slot: {"slug": s, "name": _gear_name(s)}
                   for slot, s in (doc.get("gear") or {}).items() if s}
    out["held"] = [{"slug": s, "name": _gear_name(s)}
                   for s in (doc.get("held") or [])]
    out["inventory"] = [{"slug": s, "name": _gear_name(s), "count": n}
                        for s, n in sorted(
                            (doc.get("inventory") or {}).items())]
    return out


@router.get("/admin/api/player", dependencies=[Depends(_admin)])
async def player_detail(tenant: str, player: str) -> dict:
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT doc, updated_at FROM ascent_players "
        "WHERE tenant=$1 AND player=$2", tenant, player)
    if row is None:
        raise HTTPException(404, "no such player")
    return _detail(tenant, player, json.loads(row["doc"]), row["updated_at"])


class PlayerEdit(BaseModel):
    tenant: str
    player: str
    energy: int | None = Field(default=None, ge=0, le=10_000)
    xp: int | None = Field(default=None, ge=0)
    gold: int | None = Field(default=None, ge=0)
    bank: int | None = Field(default=None, ge=0)
    grant: list[str] = Field(default_factory=list, max_length=50)


@router.post("/admin/api/player", dependencies=[Depends(_admin)])
async def player_edit(body: PlayerEdit) -> dict:
    for slug in body.grant:
        g = economy.FORGE.get(slug)
        if g is None or g.slot != "weapon":
            raise HTTPException(400, f"not a weapon: {slug}")
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT doc, updated_at FROM ascent_players "
                "WHERE tenant=$1 AND player=$2 FOR UPDATE",
                body.tenant, body.player)
            if row is None:
                raise HTTPException(404, "no such player")
            doc = json.loads(row["doc"])
            changes: list[str] = []
            if body.energy is not None:
                # the ts+val regen model: pin the value at "now"
                doc["energy_val"] = float(body.energy)
                doc["energy_ts"] = pstate.now().isoformat()
                changes.append(f"energy={body.energy}")
            for field in ("xp", "gold", "bank"):
                val = getattr(body, field)
                if val is not None:
                    old = int(doc.get(field, 0))
                    doc[field] = int(val)
                    changes.append(f"{field} {old}→{val}")
            for slug in body.grant:
                g = economy.FORGE[slug]
                inv = doc.setdefault("inventory", {})
                inv[slug] = inv.get(slug, 0) + 1
                if economy.wears(g):
                    # a granted weapon arrives with a full pool, like a
                    # bought spare — unless a stashed copy owns the key
                    doc.setdefault("durability_pack", {}).setdefault(
                        slug, economy.item_pool(g))
                changes.append(f"grant {slug}")
            if not changes:
                raise HTTPException(400, "nothing to change")
            # doc only — updated_at stays the player's own last turn
            await conn.execute(
                "UPDATE ascent_players SET doc=$3 "
                "WHERE tenant=$1 AND player=$2",
                body.tenant, body.player, json.dumps(doc))
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " xp, note) VALUES ($1,$2,'admin',0,0,$3)",
                body.tenant, body.player, ("; ".join(changes))[:256])
    return {"ok": True, "changes": changes,
            "player": _detail(body.tenant, body.player, doc,
                              row["updated_at"])}


@router.get("/admin/api/player/doc", dependencies=[Depends(_admin)])
async def player_doc(tenant: str, player: str) -> dict:
    """The raw doc, read-only — the last resort when the cards don't
    explain a stuck climber. Edits stay named, audited verbs."""
    pool = await db.get_pool()
    raw = await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player)
    if raw is None:
        raise HTTPException(404, "no such player")
    return {"doc": json.loads(raw)}


@router.get("/admin/api/player/ledger", dependencies=[Depends(_admin)])
async def player_ledger(tenant: str, player: str, limit: int = 50) -> dict:
    pool = await db.get_pool()
    rows = await pool.fetch(
        "SELECT created_at, kind, gold, xp, note FROM ascent_ledger "
        "WHERE tenant=$1 AND player=$2 ORDER BY id DESC LIMIT $3",
        tenant, player, min(max(limit, 1), 200))
    return {"entries": [{
        "at": r["created_at"].isoformat(), "kind": r["kind"],
        "gold": r["gold"], "xp": r["xp"], "note": r["note"]}
        for r in rows]}


class RescueIn(BaseModel):
    tenant: str
    player: str


@router.post("/admin/api/player/rescue", dependencies=[Depends(_admin)])
async def player_rescue(body: RescueIn) -> dict:
    """The unstick: full hp, no encounter, back to town, unlodged —
    the safe state the engine itself returns climbers to."""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT doc, updated_at FROM ascent_players "
                "WHERE tenant=$1 AND player=$2 FOR UPDATE",
                body.tenant, body.player)
            if row is None:
                raise HTTPException(404, "no such player")
            doc = json.loads(row["doc"])
            if doc.get("stage") != "playing":
                raise HTTPException(400, "not a playing doc")
            doc["hp"] = pstate.max_hp(doc)
            doc["encounter"] = None
            doc["scene"] = None
            doc["location"] = "town"
            doc["lodged_until_day"] = -1
            await conn.execute(
                "UPDATE ascent_players SET doc=$3 "
                "WHERE tenant=$1 AND player=$2",
                body.tenant, body.player, json.dumps(doc))
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " xp, note) VALUES ($1,$2,'admin',0,0,'rescue')",
                body.tenant, body.player)
    return {"ok": True,
            "player": _detail(body.tenant, body.player, doc,
                              row["updated_at"])}


@router.get("/admin/api/weapons", dependencies=[Depends(_admin)])
async def weapons() -> dict:
    """Every weapon the forge knows — all lines, all tiers, plus the
    gate steel — for the grant dropdown."""
    items = [g for g in economy.FORGE.values() if g.slot == "weapon"]
    items.sort(key=lambda g: (g.line, g.tier, g.rung, g.style, g.slug))
    return {"weapons": [{
        "slug": g.slug, "name": g.name, "line": g.line or "shared",
        "tier": g.tier, "rung": g.rung, "style": g.style,
        "bonus": g.bonus, "price": g.price} for g in items]}


# ── World ────────────────────────────────────────────────────────────────

@router.get("/admin/api/world", dependencies=[Depends(_admin)])
async def world_overview() -> dict:
    """The tower at a glance: census (the same 7-day window that sizes
    warden quorums), population, frontier + its warden pool, postbox
    and ledger vitals."""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        raw = await conn.fetchval(
            "SELECT value FROM ascent_world WHERE key='frontier'")
        frontier = int(json.loads(raw)) if raw else 1
        census = await social._census(conn)
        pop = await conn.fetchrow(
            "SELECT count(*) AS total, "
            "count(*) FILTER (WHERE doc->>'stage'='playing') AS playing, "
            "count(*) FILTER (WHERE updated_at > now() - interval '1 day')"
            " AS seen_today FROM ascent_players")
        ledger = await conn.fetchrow(
            "SELECT count(*) AS n, coalesce(sum(gold),0) AS gold, "
            "coalesce(sum(xp),0) AS xp FROM ascent_ledger")
        fb = await conn.fetchrow(
            "SELECT count(*) AS threads, coalesce(sum(admin_unread),0) "
            "AS unread FROM ascent_feedback")
        wraw = await conn.fetchval(
            "SELECT value FROM ascent_world WHERE key='warden:'||$1",
            str(frontier))
    warden = None
    if wraw:
        v = json.loads(wraw)
        warden = {"hp": v.get("hp"),
                  "strikers": len(v.get("strikers") or [])}
    return {
        "frontier": frontier,
        "census": census,
        "population": {"total": int(pop["total"]),
                       "playing": int(pop["playing"]),
                       "seen_today": int(pop["seen_today"])},
        "warden": warden,
        "feedback": {"threads": int(fb["threads"]),
                     "unread": int(fb["unread"])},
        "ledger": {"rows": int(ledger["n"]),
                   "gold_net": int(ledger["gold"]),
                   "xp_net": int(ledger["xp"])},
    }


# ── Feedback ─────────────────────────────────────────────────────────────

@router.get("/admin/api/feedback", dependencies=[Depends(_admin)])
async def feedback_threads() -> dict:
    tenant, player = _admin_ident()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await feedback.admin_threads(conn, tenant, player)


# registered before /{fid} — "unread" must not parse as a thread id
@router.get("/admin/api/feedback/unread", dependencies=[Depends(_admin)])
async def feedback_unread() -> dict:
    pool = await db.get_pool()
    n = await pool.fetchval(
        "SELECT coalesce(sum(admin_unread),0) FROM ascent_feedback")
    return {"unread": int(n)}


@router.get("/admin/api/feedback/{fid}", dependencies=[Depends(_admin)])
async def feedback_thread(fid: int) -> dict:
    tenant, player = _admin_ident()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        return await feedback.thread(conn, tenant, player, fid,
                                     as_admin=True)


class ReplyIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


@router.post("/admin/api/feedback/{fid}/reply",
             dependencies=[Depends(_admin)])
async def feedback_reply(fid: int, body: ReplyIn) -> dict:
    tenant, player = _admin_ident()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await feedback.reply(conn, tenant, player, fid,
                                        body.body, [], as_admin=True)


@router.get("/admin/api/feedback/attachment/{att_id}",
            dependencies=[Depends(_admin)])
async def feedback_attachment(att_id: int) -> Response:
    tenant, player = _admin_ident()
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        mime, raw = await feedback.attachment(conn, tenant, player, att_id)
    return Response(content=raw, media_type=mime)
