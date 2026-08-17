"""Funnel Fighters — one file owns the tracker, pages only carry its tag.

Tracked: /, /mechanics, and the website's /play (tag injected
server-side with data-user). NOT tracked: the admin console, and every
surface the plugin renders for Luna — the chat pane must stay clean.
"""

from __future__ import annotations

import uuid

PW = "probeprobe"


async def _signup(client, username: str):
    r = await client.post("/signup", json={
        "username": username, "password": PW, "password2": PW})
    assert r.status_code == 200, r.text


async def test_the_one_file_serves_with_the_config_inside(client):
    r = await client.get("/static/site/funnel.js")
    assert r.status_code == 200
    js = r.text
    assert "4a62eb26-43d4-464e-835e-b11481d24645" in js
    assert "funnelfighters.io" in js
    assert "window.ff" in js
    for ev in ("page_view", "door_view", "door_click", '"signup"',
               "signin_ok", "enter_game", "identify"):
        assert ev in js, f"funnel.js lost the {ev} wrapper"
    # the vendor SDK drops its pre-load queue (drainQueue's `root` is out
    # of scope) — funnel.js must keep its own and flush on the SDK's onload
    assert "t.onload = flush" in js and "pending.push" in js
    assert "m[e].q" not in js, "back on the vendor queue — it is silently dropped"


async def test_gmail_door_lands_on_play_with_the_door_named(client):
    name = f"Funl{uuid.uuid4().hex[:10]}"
    await _signup(client, name)
    r = await client.get("/play?door=signup")
    assert 'data-door="signup"' in r.text
    r = await client.get("/play?door=signin")
    assert 'data-door="signin"' in r.text
    r = await client.get("/play?door=bogus")
    assert "data-door" not in r.text
    r = await client.get("/play")
    assert "data-door" not in r.text


async def test_home_and_mechanics_carry_the_tag(client):
    for path in ("/", "/mechanics"):
        r = await client.get(path)
        assert r.status_code == 200
        assert "/static/site/funnel.js" in r.text, f"{path} lost the tag"


async def test_play_injects_the_tag_with_the_username(client):
    name = f"Funl{uuid.uuid4().hex[:10]}"
    await _signup(client, name)
    r = await client.get("/play")
    assert r.status_code == 200
    html = r.text
    assert "/static/site/funnel.js" in html
    assert f'data-user="{name}"' in html
    assert html.count("funnel.js") == 1


async def test_signed_out_play_bounces_untracked(client):
    r = await client.get("/play", follow_redirects=False)
    assert r.status_code == 303
    assert "funnel.js" not in r.text


async def test_admin_console_is_not_tracked(client):
    r = await client.get("/static/site/admin.html")
    assert r.status_code == 200
    assert "funnel" not in r.text.lower()


async def test_the_luna_pane_stays_tracker_free():
    """The plugin's own render never mentions the tracker — only
    worldd's /play route injects it, so chat surfaces stay clean."""
    from app.gamepath import ensure_game_importable
    ensure_game_importable()
    from plugin_linear_ascent.pane import render_pane
    html = render_pane()
    assert "funnel" not in html.lower()
