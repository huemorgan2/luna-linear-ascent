"""085: the web consumer serves and routes standard maps without Labs."""
import json
import re
import struct
import uuid


async def test_all_native_maps_are_served(client):
    for floor in range(1, 11):
        response = await client.get(
            f"/static/laart/maps/map_{floor:03d}_492x369.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">II", response.content[16:24]) == (492, 369)


async def test_web_maps_are_standard_and_printed_number_routes(client):
    from app import db
    from plugin_linear_ascent.engine import core, state

    username = "Maps" + uuid.uuid4().hex[:10]
    response = await client.post("/signup", json={
        "username": username, "password": "map-test-only",
        "password2": "map-test-only"})
    assert response.status_code == 200
    doc = state.new_player("web:" + username.lower())
    core.current_scene(doc)
    while doc["stage"] == "intro":
        core.apply_choice(doc, "1")
    core.apply_choice(doc, "human")
    core.apply_choice(doc, "warrior")
    core.apply_choice(doc, "", username)
    doc.update(level=99, floor=2, unlocked_floor=11, location="gate_town")
    doc["labs"] = {"floormap": False}
    doc["flags"].update({f"floor_seen_{n}": True for n in range(1, 12)})
    pool = await db.get_pool()
    await pool.execute(
        "INSERT INTO ascent_players (tenant,player,doc) VALUES ('web',$1,$2) "
        "ON CONFLICT (tenant,player) DO UPDATE SET doc=EXCLUDED.doc",
        username.lower(), json.dumps(doc))

    response = await client.post("/play/api/pane/scene", json={})
    assert response.status_code == 200
    card = response.json()
    assert "map_002_492x369.png" in card["fragment"]
    assert "RUSTMAW" in card["fragment"]
    number = re.search(
        r'data-opt="gate"[^>]*>\s*<span class="mknum">\[(\d+)\]',
        card["fragment"]).group(1)
    response = await client.post("/play/api/act", json={
        "option": number, "mode": "pane", "scene_id": card["scene_id"]})
    assert response.status_code == 200
    assert 'data-opt="floor_2"' in response.json()["fragment"]
    after = json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='web' AND player=$1",
        username.lower()))
    assert after["location"] == "gate"
    assert after["gate_from"] == 2
    assert state.energy_now(after) == state.energy_now(doc)
