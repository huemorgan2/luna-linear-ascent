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


async def group_fixture(client,monkeypatch):
    from plugin_linear_ascent.engine import core,bestiary,groups
    from plugin_linear_ascent.content import schema
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    key=await player(client)
    p=await saved(key)
    p.update(floor=1,location='gate_town',training=dict(blade=10,bow=10,staff=10))
    # Returning player owns a legacy blade; these explicit test copies are
    # fixture grants, not the opening or simulation progression path.
    bow=collection.mint(p,'hawkeye',source='starter')
    collection.set_slot(p,1,bow['id'])
    members=[bestiary.rolled_member(p,1,schema.get_floor(1).encounters[0].id,opening=True) for _ in range(2)]
    for m in members:
        m.update(hp=1,hp_max=1,defense=0,gap=3)
        m['rewards']=dict(gold=11,xp=3,materials={'Wood':1},weapon=None)
    groups.open_group(p,members=members)
    core.apply_choice(p,'strike:'+bow['id'])
    p.pop('_ledger',None)
    await (await db.get_pool()).execute("UPDATE ascent_players SET doc=$2::jsonb WHERE tenant='web' AND player=$1",key,json.dumps(p))
    return key,bow['id'],p


@pytest.mark.asyncio
async def test_two_http_clients_settle_final_group_once(client,monkeypatch):
    key,bow,p=await group_fixture(client,monkeypatch)
    before=p['gold'];scene=f"s{p['act_seq']}"
    a,b=await asyncio.gather(
        game.run_act('web',key,'strike:'+bow,'','final-a',expected_scene=scene),
        game.run_act('web',key,'strike:'+bow,'','final-b',expected_scene=scene))
    final=await saved(key)
    assert final['gold']==before+22 and final['materials']['Wood']==2
    assert final['group'] is None and final['group_result']['won']
    assert sum(bool(x['refusal']) for x in (a,b))==1
    assert await (await db.get_pool()).fetchval("SELECT count(*) FROM ascent_ledger WHERE tenant='web' AND player=$1 AND kind='group_clear'",key)==1


@pytest.mark.asyncio
async def test_http_group_read_and_external_bank_action_cannot_escape_lock(client,monkeypatch):
    key,bow,p=await group_fixture(client,monkeypatch)
    before=(p['gold'],p['bank'],p['energy_val'],p['rng_counter'],deepcopy(p['group']))
    await game.run_scene('web',key)
    refused=await game.run_act('web',key,'deposit_all','','illegal-during-group')
    final=await saved(key)
    assert refused['refusal']
    assert (final['gold'],final['bank'],final['energy_val'],final['rng_counter'],final['group'])==before


@pytest.mark.asyncio
async def test_http_expediton_extract_retry_banks_once(client,monkeypatch):
    from plugin_linear_ascent.engine import core
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    key=await player(client);p=await saved(key)
    p.update(floor=3,location='gate_town',unlocked_floor=3)
    for oid in ('gather_site:drowned-copse','gather_tool','gather_begin'):
        assert not core.apply_choice(p,oid).refusal
    p['expedition']['haul']['Wood']=9
    p['materials']['Wood']=17
    p['expedition']['gold']=13
    p.pop('_ledger',None)
    await (await db.get_pool()).execute("UPDATE ascent_players SET doc=$2::jsonb WHERE tenant='web' AND player=$1",key,json.dumps(p))
    args=('web',key,'gather_extract','','extract-retry')
    a,b=await asyncio.gather(game.run_act(*args),game.run_act(*args))
    final=await saved(key)
    assert a==b and final['materials']['Wood']==26 and final['gold']==p['gold']+13
    assert final['expedition'] is None
