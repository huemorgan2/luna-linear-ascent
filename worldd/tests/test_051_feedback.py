"""051 the postbox — feedback threads, admin replies, unread badges.

The admin gate hangs on CHARACTER names (MasterChief, huemorgan3 by
default): 004 made names one-per-world, so a name is an identity. Both
doors are walked — the tenant HMAC door via /v1/feedback/* and the web
cookie door via /play/api/pane/feedback/*.
"""

from __future__ import annotations

import base64
import uuid

import pytest

from app import db
from tests.test_social_api import create
from tests.test_world_api import make_tenant, signed

PNG = b"\x89PNG\r\n\x1a\n" + b"not-really-pixels" * 4
PNG_B64 = base64.b64encode(PNG).decode()


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture(autouse=True)
async def scrubbed(client):
    """Feedback rows and the admin names survive across runs — clear both
    so MasterChief is creatable and the admin desk starts empty."""
    pool = await db.get_pool()
    await pool.execute("DELETE FROM ascent_feedback")
    await pool.execute(
        "DELETE FROM ascent_names WHERE name_lower = ANY($1)",
        ["masterchief", "huemorgan3"])
    await pool.execute(
        "DELETE FROM ascent_accounts WHERE lower(username) = ANY($1)",
        ["masterchief", "huemorgan3"])
    await pool.execute(
        "DELETE FROM ascent_players WHERE tenant='web' "
        "AND player = ANY($1)", ["masterchief", "huemorgan3"])


async def fb(client, secret, tenant, player, path, extra=None,
             expect=200):
    body, headers = signed(secret, tenant,
                           {"player": player, **(extra or {})})
    r = await client.post(f"/v1/feedback/{path}", content=body,
                          headers=headers)
    assert r.status_code == expect, (path, r.status_code, r.text)
    return r.json()


def _p(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


async def test_create_mine_thread_roundtrip(client, tenant_a):
    player = _p("poster")
    name = f"Post{player[-4:]}"
    await create(client, tenant_a, "tenant-a", player, name)

    out = await fb(client, tenant_a, "tenant-a", player, "create", {
        "subject": "the lift ate my sword",
        "body": "floor 3, after the gate — it vanished.",
        "attachments": [{"mime": "image/png", "data": PNG_B64}]})
    fid = out["id"]

    mine = await fb(client, tenant_a, "tenant-a", player, "mine")
    assert [t["id"] for t in mine["threads"]] == [fid]
    t = mine["threads"][0]
    assert t["subject"] == "the lift ate my sword"
    assert t["author"] == name            # the character signs, not the key
    assert t["last_sender"] == "player" and t["unread"] == 0

    th = await fb(client, tenant_a, "tenant-a", player, "thread",
                  {"id": fid})
    assert th["tenant"] == "" and th["player"] == ""   # only admins see keys
    (msg,) = th["messages"]
    assert msg["sender"] == "player" and msg["author"] == name
    assert msg["body"].startswith("floor 3")
    (att,) = msg["attachments"]
    assert att["mime"] == "image/png"

    got = await fb(client, tenant_a, "tenant-a", player, "att",
                   {"id": att["id"]})
    assert got["mime"] == "image/png"
    assert base64.b64decode(got["data"]) == PNG


async def test_admin_gate_is_the_character_name(client, tenant_a):
    civilian, chief, hue = _p("civ"), _p("chief"), _p("hue")
    await create(client, tenant_a, "tenant-a", civilian,
                 f"Civ{civilian[-4:]}")
    await create(client, tenant_a, "tenant-a", chief, "MasterChief")

    out = await fb(client, tenant_a, "tenant-a", civilian, "create", {
        "subject": "hello wardens", "body": "just waving",
        "attachments": []})
    fid = out["id"]

    # a civilian is turned away from the desk, however they ask
    await fb(client, tenant_a, "tenant-a", civilian, "admin", expect=403)
    await fb(client, tenant_a, "tenant-a", civilian, "thread",
             {"id": fid, "as_admin": True}, expect=403)

    # MasterChief walks in (gate compares lowercased)
    desk = await fb(client, tenant_a, "tenant-a", chief, "admin")
    row = next(t for t in desk["threads"] if t["id"] == fid)
    assert row["tenant"] == "tenant-a" and row["player"] == civilian
    assert row["last_line"].startswith("just waving")

    th = await fb(client, tenant_a, "tenant-a", chief, "thread",
                  {"id": fid, "as_admin": True})
    assert th["tenant"] == "tenant-a" and th["player"] == civilian

    # the second warden's name opens the same door
    await create(client, tenant_a, "tenant-a", hue, "huemorgan3")
    await fb(client, tenant_a, "tenant-a", hue, "admin")

    # a stranger who is not an admin can't read someone else's thread
    await fb(client, tenant_a, "tenant-a", chief, "thread", {"id": fid},
             expect=404)


async def test_reply_unread_and_whatsapp_sort(client, tenant_a):
    poster, chief = _p("poster"), _p("chief")
    await create(client, tenant_a, "tenant-a", poster,
                 f"Pip{poster[-4:]}")
    await create(client, tenant_a, "tenant-a", chief, "MasterChief")

    t1 = (await fb(client, tenant_a, "tenant-a", poster, "create", {
        "subject": "first thread", "body": "one", "attachments": []}))["id"]
    t2 = (await fb(client, tenant_a, "tenant-a", poster, "create", {
        "subject": "second thread", "body": "two", "attachments": []}))["id"]

    # freshest first: t2 on top, both unread at the admin desk
    desk = await fb(client, tenant_a, "tenant-a", chief, "admin")
    assert [t["id"] for t in desk["threads"][:2]] == [t2, t1]
    u = await fb(client, tenant_a, "tenant-a", chief, "unread")
    assert u["admin"] is True and u["admin_unread"] == 2

    # the poster is no admin and has nothing unread yet
    u = await fb(client, tenant_a, "tenant-a", poster, "unread")
    assert u == {"unread": 0, "admin": False}

    # the warden answers t1 — with a screenshot of their own
    await fb(client, tenant_a, "tenant-a", chief, "reply", {
        "id": t1, "as_admin": True, "body": "on it",
        "attachments": [{"mime": "image/jpeg", "data": PNG_B64}]})

    # t1 jumps to the top, WhatsApp-style; replying read it for the desk
    desk = await fb(client, tenant_a, "tenant-a", chief, "admin")
    assert [t["id"] for t in desk["threads"][:2]] == [t1, t2]
    assert desk["threads"][0]["unread"] == 0
    assert desk["threads"][0]["last_sender"] == "admin"

    # the badge lights for the poster; opening the thread puts it out
    u = await fb(client, tenant_a, "tenant-a", poster, "unread")
    assert u["unread"] == 1
    th = await fb(client, tenant_a, "tenant-a", poster, "thread",
                  {"id": t1})
    assert [m["sender"] for m in th["messages"]] == ["player", "admin"]
    assert th["messages"][1]["author"] == "MasterChief"
    u = await fb(client, tenant_a, "tenant-a", poster, "unread")
    assert u["unread"] == 0


async def test_attachment_privacy(client, tenant_a):
    poster, nosy, chief = _p("poster"), _p("nosy"), _p("chief")
    await create(client, tenant_a, "tenant-a", poster,
                 f"Owl{poster[-4:]}")
    await create(client, tenant_a, "tenant-a", nosy, f"Fox{nosy[-4:]}")
    await create(client, tenant_a, "tenant-a", chief, "MasterChief")

    fid = (await fb(client, tenant_a, "tenant-a", poster, "create", {
        "subject": "see attached", "body": "look",
        "attachments": [{"mime": "image/webp", "data": PNG_B64}]}))["id"]
    th = await fb(client, tenant_a, "tenant-a", poster, "thread",
                  {"id": fid})
    att_id = th["messages"][0]["attachments"][0]["id"]

    # strangers get a 404, never a 403 that admits the thing exists
    await fb(client, tenant_a, "tenant-a", nosy, "att", {"id": att_id},
             expect=404)
    await fb(client, tenant_a, "tenant-a", nosy, "thread", {"id": fid},
             expect=404)

    got = await fb(client, tenant_a, "tenant-a", chief, "att",
                   {"id": att_id})
    assert base64.b64decode(got["data"]) == PNG


async def test_validation_limits(client, tenant_a):
    player = _p("val")
    await create(client, tenant_a, "tenant-a", player, f"Val{player[-4:]}")

    def draft(**over):
        d = {"subject": "a fine subject", "body": "a fine body",
             "attachments": []}
        d.update(over)
        return d

    for bad in (
        draft(subject="no"),                        # under 3
        draft(subject="s" * 81),                    # over 80
        draft(body=""),                             # empty message
        draft(body="  \n "),                        # whitespace is empty
        draft(body="b" * 4001),                     # over 4000
        draft(attachments=[{"mime": "image/png", "data": PNG_B64}] * 4),
        draft(attachments=[{"mime": "image/tiff", "data": PNG_B64}]),
        draft(attachments=[{"mime": "image/png", "data": "@@not-b64@@"}]),
        draft(attachments=[{"mime": "image/png", "data": ""}]),
        draft(attachments=[{"mime": "image/png", "data": base64.b64encode(
            b"x" * (2 * 1024 * 1024 + 1)).decode()}]),
    ):
        await fb(client, tenant_a, "tenant-a", player, "create", bad,
                 expect=422)

    # and the good one still lands
    await fb(client, tenant_a, "tenant-a", player, "create", draft())


async def test_web_door_mirror(client):
    """The cookie door: file feedback, see the badge, fetch the image as a
    real HTTP image; a MasterChief ACCOUNT is a warden before it ever
    steps through the gate (004: the username IS the climber name)."""
    poster = f"Webfb{uuid.uuid4().hex[:8]}"
    pw = {"password": "probeprobe", "password2": "probeprobe"}
    r = await client.post("/signup", json={"username": poster, **pw})
    assert r.status_code == 200, r.text

    r = await client.post("/play/api/pane/feedback/create", json={
        "subject": "from the web door", "body": "hello from a browser",
        "attachments": [{"mime": "image/png", "data": PNG_B64}]})
    assert r.status_code == 200, r.text
    fid = r.json()["id"]

    r = await client.get("/play/api/pane/feedback/mine")
    assert r.status_code == 200
    assert [t["id"] for t in r.json()["threads"]] == [fid]
    # before the doc boots, the door signs with the account's own name
    assert r.json()["threads"][0]["author"].lower() == poster.lower()

    r = await client.post("/play/api/pane/feedback/thread",
                          json={"id": fid})
    att_id = r.json()["messages"][0]["attachments"][0]["id"]
    r = await client.get(f"/play/api/pane/feedback/att/{att_id}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/png")
    assert r.content == PNG

    r = await client.get("/play/api/pane/feedback/unread")
    assert r.json() == {"unread": 0, "admin": False}

    # the warden signs up at the same door — the cookie switches hands
    r = await client.post("/signup", json={"username": "MasterChief",
                                           **pw})
    assert r.status_code == 200, r.text
    r = await client.get("/play/api/pane/feedback/admin")
    assert r.status_code == 200
    row = next(t for t in r.json()["threads"] if t["id"] == fid)
    assert row["player"] == poster.lower()
    r = await client.post("/play/api/pane/feedback/reply", json={
        "id": fid, "as_admin": True, "body": "the wardens hear you",
        "attachments": []})
    assert r.status_code == 200, r.text

    # back as the poster: the badge is lit, the chat holds both turns
    r = await client.post("/login", json={"username": poster,
                                          "password": "probeprobe"})
    assert r.status_code == 200, r.text
    r = await client.get("/play/api/pane/feedback/unread")
    assert r.json() == {"unread": 1, "admin": False}
    r = await client.post("/play/api/pane/feedback/thread",
                          json={"id": fid})
    senders = [m["sender"] for m in r.json()["messages"]]
    assert senders == ["player", "admin"]
