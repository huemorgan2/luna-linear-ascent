"""051 the postbox — player feedback, admin replies, unread badges.

Threads belong to (tenant, player); every message is a chat turn from the
player or from an admin. Admins are CHARACTER names (004: a name is unique
across the whole world, so a name is an identity), held in the
ascent_admins table — seeded once from ASCENT_FEEDBACK_ADMINS, managed
from the desk's ADMINS tab. Attachments are small screenshots stored as bytea
right in the world database.
"""

from __future__ import annotations

import base64
import json
import os

from fastapi import HTTPException

MAX_ATTACHMENTS = 3
MAX_ATTACHMENT_BYTES = 2 * 1024 * 1024
ALLOWED_MIMES = {"image/png", "image/jpeg", "image/webp", "image/gif"}
SUBJECT_MIN, SUBJECT_MAX = 3, 80
BODY_MAX = 4000
ADMIN_LIST_LIMIT = 500


def admin_names() -> set[str]:
    """The env list — only the SEED for ascent_admins, read once when
    the table is empty. The table is the truth; the desk edits it."""
    raw = os.environ.get("ASCENT_FEEDBACK_ADMINS",
                         "masterchief,huemorgan3")
    return {n.strip().lower() for n in raw.split(",") if n.strip()}


async def admin_set(conn) -> set[str]:
    """The approved admins, from the database. An empty table means a
    fresh world — the env list walks in and signs the book."""
    rows = await conn.fetch("SELECT name FROM ascent_admins")
    if rows:
        return {r["name"] for r in rows}
    seed = admin_names()
    for n in sorted(seed):
        await conn.execute(
            "INSERT INTO ascent_admins (name, added_by) VALUES ($1, 'seed') "
            "ON CONFLICT (name) DO NOTHING", n)
    return seed


async def character_name(conn, tenant: str, player: str) -> str:
    row = await conn.fetchrow(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player)
    if row is None:
        return ""
    return json.loads(row["doc"]).get("name") or ""


async def is_admin(conn, tenant: str, player: str) -> bool:
    name = await character_name(conn, tenant, player)
    if not name and tenant == "web":
        # 004: the site username IS the climber name — an account that
        # hasn't stepped through the gate yet still owns its name.
        name = player
    return name.lower() in await admin_set(conn)


def _decode_attachments(attachments: list) -> list[tuple[str, bytes]]:
    if len(attachments) > MAX_ATTACHMENTS:
        raise HTTPException(422,
                            f"at most {MAX_ATTACHMENTS} screenshots a message")
    blobs: list[tuple[str, bytes]] = []
    for att in attachments:
        mime = (att.get("mime") if isinstance(att, dict)
                else att.mime).strip().lower()
        data = att.get("data") if isinstance(att, dict) else att.data
        if mime not in ALLOWED_MIMES:
            raise HTTPException(422, "screenshots only — png, jpeg, webp "
                                     "or gif")
        try:
            raw = base64.b64decode(data or "", validate=True)
        except Exception:
            raise HTTPException(422, "attachment is not valid base64")
        if not raw:
            raise HTTPException(422, "empty attachment")
        if len(raw) > MAX_ATTACHMENT_BYTES:
            raise HTTPException(422, "a screenshot tops out at 2 MB")
        blobs.append((mime, raw))
    return blobs


async def _author(conn, tenant: str, player: str) -> str:
    name = await character_name(conn, tenant, player)
    if name:
        return name
    return player if tenant == "web" else "a climber"


async def _append(conn, fid: int, sender: str, author: str, body: str,
                  blobs: list[tuple[str, bytes]]) -> int:
    mid = await conn.fetchval(
        "INSERT INTO ascent_feedback_messages (feedback_id, sender, author,"
        " body) VALUES ($1,$2,$3,$4) RETURNING id",
        fid, sender, author, body)
    for mime, raw in blobs:
        await conn.execute(
            "INSERT INTO ascent_feedback_attachments (message_id, mime,"
            " bytes) VALUES ($1,$2,$3)", mid, mime, raw)
    unread = "admin_unread" if sender == "player" else "player_unread"
    await conn.execute(
        f"UPDATE ascent_feedback SET last_msg_at=now(), last_sender=$2, "
        f"{unread}={unread}+1 WHERE id=$1", fid, sender)
    return mid


def _check_body(body: str) -> str:
    body = (body or "").strip()
    if not body:
        raise HTTPException(422, "say something — the message is empty")
    if len(body) > BODY_MAX:
        raise HTTPException(422, f"the message tops out at {BODY_MAX} "
                                 "characters")
    return body


async def create(conn, tenant: str, player: str, subject: str, body: str,
                 attachments: list) -> dict:
    subject = (subject or "").strip()
    if not (SUBJECT_MIN <= len(subject) <= SUBJECT_MAX):
        raise HTTPException(422, f"subject: {SUBJECT_MIN}–{SUBJECT_MAX} "
                                 "characters")
    body = _check_body(body)
    blobs = _decode_attachments(attachments)
    author = await _author(conn, tenant, player)
    fid = await conn.fetchval(
        "INSERT INTO ascent_feedback (tenant, player, author, subject) "
        "VALUES ($1,$2,$3,$4) RETURNING id",
        tenant, player, author, subject)
    await _append(conn, fid, "player", author, body, blobs)
    return {"ok": True, "id": fid}


async def my_threads(conn, tenant: str, player: str) -> dict:
    rows = await conn.fetch(
        "SELECT id, subject, author, created_at, last_msg_at, last_sender,"
        " player_unread FROM ascent_feedback WHERE tenant=$1 AND player=$2 "
        "ORDER BY last_msg_at DESC", tenant, player)
    return {"threads": [{
        "id": r["id"], "subject": r["subject"], "author": r["author"],
        "created_at": r["created_at"].isoformat(),
        "last_msg_at": r["last_msg_at"].isoformat(),
        "last_sender": r["last_sender"],
        "unread": r["player_unread"]} for r in rows]}


async def _thread_row(conn, fid: int):
    row = await conn.fetchrow(
        "SELECT id, tenant, player, author, subject FROM ascent_feedback "
        "WHERE id=$1", fid)
    if row is None:
        raise HTTPException(404, "no such feedback")
    return row


async def _authorize(conn, row, tenant: str, player: str,
                     as_admin: bool) -> None:
    if as_admin:
        if not await is_admin(conn, tenant, player):
            raise HTTPException(403, "the desk is not yours")
        return
    if row["tenant"] != tenant or row["player"] != player:
        raise HTTPException(404, "no such feedback")


async def thread(conn, tenant: str, player: str, fid: int,
                 as_admin: bool = False) -> dict:
    row = await _thread_row(conn, fid)
    await _authorize(conn, row, tenant, player, as_admin)
    unread = "admin_unread" if as_admin else "player_unread"
    await conn.execute(
        f"UPDATE ascent_feedback SET {unread}=0 WHERE id=$1", fid)
    msgs = await conn.fetch(
        "SELECT id, sender, author, body, created_at "
        "FROM ascent_feedback_messages WHERE feedback_id=$1 ORDER BY id",
        fid)
    atts = await conn.fetch(
        "SELECT a.id, a.message_id, a.mime FROM ascent_feedback_attachments a"
        " JOIN ascent_feedback_messages m ON m.id=a.message_id "
        "WHERE m.feedback_id=$1 ORDER BY a.id", fid)
    by_msg: dict[int, list] = {}
    for a in atts:
        by_msg.setdefault(a["message_id"], []).append(
            {"id": a["id"], "mime": a["mime"]})
    return {
        "id": row["id"], "subject": row["subject"], "author": row["author"],
        "tenant": row["tenant"] if as_admin else "",
        "player": row["player"] if as_admin else "",
        "messages": [{
            "id": m["id"], "sender": m["sender"], "author": m["author"],
            "body": m["body"], "at": m["created_at"].isoformat(),
            "attachments": by_msg.get(m["id"], [])} for m in msgs]}


async def reply(conn, tenant: str, player: str, fid: int, body: str,
                attachments: list, as_admin: bool = False) -> dict:
    row = await _thread_row(conn, fid)
    await _authorize(conn, row, tenant, player, as_admin)
    body = _check_body(body)
    blobs = _decode_attachments(attachments)
    author = await _author(conn, tenant, player)
    await _append(conn, fid, "admin" if as_admin else "player",
                  author, body, blobs)
    # the writer has obviously read the thread up to their own message
    unread = "admin_unread" if as_admin else "player_unread"
    await conn.execute(
        f"UPDATE ascent_feedback SET {unread}=0 WHERE id=$1", fid)
    return {"ok": True}


async def unread(conn, tenant: str, player: str) -> dict:
    n = await conn.fetchval(
        "SELECT coalesce(sum(player_unread),0) FROM ascent_feedback "
        "WHERE tenant=$1 AND player=$2", tenant, player)
    admin = await is_admin(conn, tenant, player)
    out = {"unread": int(n), "admin": admin}
    if admin:
        out["admin_unread"] = int(await conn.fetchval(
            "SELECT coalesce(sum(admin_unread),0) FROM ascent_feedback"))
    return out


async def admin_threads(conn, tenant: str, player: str) -> dict:
    if not await is_admin(conn, tenant, player):
        raise HTTPException(403, "the desk is not yours")
    rows = await conn.fetch(
        "SELECT f.id, f.tenant, f.player, f.author, f.subject, f.created_at,"
        " f.last_msg_at, f.last_sender, f.admin_unread,"
        " (SELECT left(m.body, 120) FROM ascent_feedback_messages m"
        "  WHERE m.feedback_id=f.id ORDER BY m.id DESC LIMIT 1) AS last_line"
        " FROM ascent_feedback f ORDER BY f.last_msg_at DESC LIMIT $1",
        ADMIN_LIST_LIMIT)
    return {"threads": [{
        "id": r["id"], "tenant": r["tenant"], "player": r["player"],
        "author": r["author"], "subject": r["subject"],
        "created_at": r["created_at"].isoformat(),
        "last_msg_at": r["last_msg_at"].isoformat(),
        "last_sender": r["last_sender"], "unread": r["admin_unread"],
        "last_line": r["last_line"] or ""} for r in rows]}


async def attachment(conn, tenant: str, player: str,
                     att_id: int) -> tuple[str, bytes]:
    row = await conn.fetchrow(
        "SELECT a.mime, a.bytes, f.tenant, f.player "
        "FROM ascent_feedback_attachments a "
        "JOIN ascent_feedback_messages m ON m.id=a.message_id "
        "JOIN ascent_feedback f ON f.id=m.feedback_id WHERE a.id=$1", att_id)
    if row is None:
        raise HTTPException(404, "no such attachment")
    if (row["tenant"] != tenant or row["player"] != player) \
            and not await is_admin(conn, tenant, player):
        raise HTTPException(404, "no such attachment")
    return row["mime"], bytes(row["bytes"])
