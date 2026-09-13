"""Two tabs, retried requests and different players share authoritative state."""
import asyncio
from copy import deepcopy
import json
import uuid

import pytest

from app import db, game
from plugin_linear_ascent.engine import collection, state
from tests.test_web_play import _signup


async def player(client, *, gold=1000, candidate=True):
    name = "Instance" + uuid.uuid4().hex[:8]
    await _signup(client, name)
    key = name.lower()
    p = state.new_player("web:" + key)
    p.update(stage="playing", name=name, race="human", location="vault", gold=gold)
    state.ensure_current(p)
    if candidate:
        collection.migrate(p)
    await (await db.get_pool()).execute(
        "INSERT INTO ascent_players(tenant,player,doc) VALUES ('web',$1,$2::jsonb)", key, json.dumps(p))
    return key


async def saved(key):
    return json.loads(await (await db.get_pool()).fetchval(
        "SELECT doc FROM ascent_players WHERE tenant='web' AND player=$1", key))


@pytest.mark.asyncio
async def test_parallel_same_request_is_one_deposit(client):
    key = await player(client)
    args = ("web", key, "deposit_half", "", "same-click")
    a, b = await asyncio.gather(game.run_act(*args, expected_scene="s0"),
                                game.run_act(*args, expected_scene="s0"))
    p = await saved(key)
    assert a == b
    assert p["gold"] == 500 and p["bank"] == 500 and p["act_seq"] == 1
    assert await (await db.get_pool()).fetchval(
        "SELECT count(*) FROM ascent_ledger WHERE tenant='web' AND player=$1 AND kind='deposit'", key) == 1


@pytest.mark.asyncio
async def test_retry_key_cannot_return_another_players_scene(client):
    a = await player(client, gold=1000)
    b = await player(client, gold=2000)
    one = await game.run_act("web", a, "deposit_half", "", "identical-client-key")
    two = await game.run_act("web", b, "deposit_half", "", "identical-client-key")
    assert one["meters"]["name"] != two["meters"]["name"]
    assert (await saved(a))["bank"] == 500
    assert (await saved(b))["bank"] == 1000


@pytest.mark.asyncio
async def test_different_action_on_stale_scene_is_read_only(client):
    key = await player(client)
    await game.run_act("web", key, "deposit_half", "", "first", expected_scene="s0")
    before = deepcopy(await saved(key))
    refused = await game.run_act("web", key, "deposit_all", "", "second", expected_scene="s0")
    assert refused["refusal"] and (await saved(key)) == before


@pytest.mark.asyncio
async def test_web_double_click_uses_observed_scene(client):
    key = await player(client)
    scene = (await client.post("/play/api/pane/scene")).json()
    body = dict(option="deposit_half", scene_id=scene["scene_id"])
    first, second = await asyncio.gather(client.post("/play/api/act", json=body),
                                         client.post("/play/api/act", json=body))
    assert first.status_code == second.status_code == 200
    assert first.json()["scene_id"] == second.json()["scene_id"]
    p = await saved(key)
    assert p["gold"] == p["bank"] == 500


@pytest.mark.asyncio
async def test_conversion_reads_actual_paid_school_receipts(client, monkeypatch):
    key = await player(client, candidate=False)
    pool = await db.get_pool()
    p = await saved(key)
    p["slots"] = 3
    await pool.execute("UPDATE ascent_players SET doc=$2::jsonb WHERE tenant='web' AND player=$1", key, json.dumps(p))
    await pool.execute("INSERT INTO ascent_ledger(tenant,player,kind,note,gold,xp) VALUES ('web',$1,'train','carry 2',-30,-60),('web',$1,'train','carry 3',-8765,-500)", key)
    monkeypatch.setenv("ASCENT_RULESET", collection.RULESET)
    await game.run_scene("web", key)
    converted = await saved(key)
    assert converted["gold"] == 1000 + 30 + 8765
    assert state.xp_total(converted) == 560
    await game.run_scene("web", key)
    assert (await saved(key))["gold"] == converted["gold"]
