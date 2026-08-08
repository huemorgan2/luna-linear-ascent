"""042 — guilds, players here, looting (real DB, over the wire).

The presence grid rides the scene, the Stone of Names opens on a click,
gifts land in the receiver's pack, a cold camp is lootable, the guild
directory seats a joiner on the spot and the door rules gate the door
server-side."""

import json
import uuid

import pytest

from app import db, factions
from tests.test_multiplayer import create_player
from tests.test_world_api import act, make_tenant, scene


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def tenant_b(client):
    return await make_tenant(client, "tenant-b")


@pytest.fixture
async def clean_042(client):
    pool = await db.get_pool()

    async def wipe():
        # earlier test files leave same-named climbers behind and the
        # name-keyed reads pick the newest row — clear the field first
        await pool.execute(
            "DELETE FROM ascent_players "
            "WHERE tenant IN ('tenant-a','tenant-b')")
        await pool.execute("DELETE FROM ascent_faction_requests")
        await pool.execute("DELETE FROM ascent_faction_members")
        await pool.execute("DELETE FROM ascent_faction_ledger")
        await pool.execute("DELETE FROM ascent_factions")
        await pool.execute("DELETE FROM ascent_loot_attempts")
        await pool.execute(
            "DELETE FROM ascent_happenings WHERE kind IN ('faction','loot')")
    await wipe()
    yield
    await wipe()


def _name():
    return f"Banner {uuid.uuid4().hex[:6]}"


async def _doc(pool, tenant, player):
    return json.loads(await pool.fetchval(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player))


async def _patch(pool, tenant, player, **kw):
    await pool.execute(
        "UPDATE ascent_players SET doc = doc || $3::jsonb "
        "WHERE tenant=$1 AND player=$2", tenant, player, json.dumps(kw))


# ── the presence grid + the Stone of Names ──────────────────────────────

async def test_town_scene_carries_the_other_climbers_tile(
        client, tenant_a, tenant_b, clean_042):
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    await create_player(client, tenant_b, "tenant-b", "Brai")
    s = await scene(client, tenant_a, "tenant-a", pa)
    tiles = s.get("players_here") or []
    assert any(t["name"] == "Brai" for t in tiles)
    assert all(t["name"] != "Aldo" for t in tiles)   # never your own face
    tile = next(t for t in tiles if t["name"] == "Brai")
    assert tile["opt"] == "pv:Brai"
    assert "gold" in tile and "energy" in tile and "armor" in tile


async def test_tile_click_opens_the_profile_with_no_bank_anywhere(
        client, tenant_a, tenant_b, clean_042):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")
    await _patch(pool, "tenant-b", pb, gold=77, bank=9999)
    s = await act(client, tenant_a, "tenant-a", pa, option="pv:Brai")
    assert "BRAI" in s["headline"].upper()
    text = json.dumps(s, ensure_ascii=False)
    assert "◈ 77" in text                  # carried coin is public
    assert "9999" not in text              # the bank never rides the wire
    assert "9,999" not in text


# ── gifts ───────────────────────────────────────────────────────────────

async def test_gift_lands_in_the_receivers_pack(
        client, tenant_a, tenant_b, clean_042):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")
    await _patch(pool, "tenant-a", pa, inventory={"trollblood_tonic": 2})
    await act(client, tenant_a, "tenant-a", pa, option="pv:Brai")
    await act(client, tenant_a, "tenant-a", pa, option="pf_gift")
    await act(client, tenant_a, "tenant-a", pa,
              option="pf_gift_trollblood_tonic")
    da = await _doc(pool, "tenant-a", pa)
    db_ = await _doc(pool, "tenant-b", pb)
    assert da["inventory"].get("trollblood_tonic") == 1
    assert db_["inventory"].get("trollblood_tonic") == 1
    assert any("sent you" in json.dumps(ev)
               for ev in db_.get("pending_events", []))


# ── looting ─────────────────────────────────────────────────────────────

async def test_cold_camp_loses_carried_gold_never_the_bank(
        client, tenant_a, tenant_b, clean_042):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")
    await _patch(pool, "tenant-a", pa, level=6)
    await _patch(pool, "tenant-b", pb, level=6, gold=1000, bank=500)
    await pool.execute(
        "UPDATE ascent_players SET updated_at = now() - interval '2 hours' "
        "WHERE tenant='tenant-b' AND player=$1", pb)
    gold_before = (await _doc(pool, "tenant-a", pa))["gold"]
    s = await act(client, tenant_a, "tenant-a", pa, option="pv:Brai")
    row = next(o for o in s["options"] if o["id"] == "pf_loot")
    assert not row.get("locked"), row
    await act(client, tenant_a, "tenant-a", pa, option="pf_loot")
    verdict = await act(client, tenant_a, "tenant-a", pa,
                        option="pf_loot_go")
    # the verdict rides THIS response — not the next act's card
    assert verdict["headline"] == "You cleaned out their camp"
    assert any("carried gold seized" in ln
               for ln in verdict["body_lines"])
    s_after = await scene(client, tenant_a, "tenant-a", pa)
    assert s_after.get("eyebrow") != "THE FIELDS · AFTER"   # no replay
    da = await _doc(pool, "tenant-a", pa)
    db_ = await _doc(pool, "tenant-b", pb)
    haul = 1000 - db_["gold"]
    assert 100 <= haul <= 250              # 10–25% of carried, cold camp
    assert da["gold"] == gold_before + haul
    assert db_["bank"] == 500              # the Vault keeps its word
    logged = await pool.fetchrow(
        "SELECT outcome, haul FROM ascent_loot_attempts "
        "WHERE tenant='tenant-a' AND player=$1", pa)
    assert logged["outcome"] == "win" and logged["haul"] == haul
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_happenings WHERE kind='loot'") == 1


async def test_guildmates_and_beginners_are_shielded(
        client, tenant_a, tenant_b, clean_042):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")
    # a beginner (level 1) is under the tower's protection
    s = await act(client, tenant_a, "tenant-a", pa, option="pv:Brai")
    row = next(o for o in s["options"] if o["id"] == "pf_loot")
    assert row.get("locked")
    # a guildmate is out of reach at any level — server law included
    await _patch(pool, "tenant-a", pa, level=6)
    await _patch(pool, "tenant-b", pb, level=6)
    name = _name()
    await factions.create_faction((await db.get_pool()), "tenant-a", pa,
                                  name, "wolf_howl", "Aldo")
    await factions.join_faction((await db.get_pool()), "tenant-b", pb,
                                name)
    doc_a = await _doc(pool, "tenant-a", pa)
    doc_a["_effects"] = [{"kind": "loot_attempt", "target_name": "Brai"}]
    from app import social
    await social.execute_effects((await db.get_pool()), "tenant-a", pa,
                                 doc_a)
    logged = await pool.fetchrow(
        "SELECT outcome FROM ascent_loot_attempts "
        "WHERE tenant='tenant-a' AND player=$1", pa)
    assert logged["outcome"] == "blocked"


# ── the guild directory + the door rules ────────────────────────────────

async def test_directory_join_seats_the_climber_and_posts_the_news(
        client, tenant_a, tenant_b, clean_042):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")
    await _patch(pool, "tenant-a", pa, level=6, gold=2000)
    await _patch(pool, "tenant-b", pb, gold=100)
    name = _name()
    await factions.create_faction(pool, "tenant-a", pa, name,
                                  "wolf_howl", "Aldo", join_fee=25)
    await act(client, tenant_b, "tenant-b", pb, option="guildhall")
    s = await act(client, tenant_b, "tenant-b", pb, option="hall_ledger")
    assert any(g["opt"] == f"gjoin_{name}" for g in s.get("gallery") or [])
    s = await act(client, tenant_b, "tenant-b", pb, option=f"gjoin_{name}")
    assert "takes you" in s["headline"]
    member = await pool.fetchrow(
        "SELECT faction FROM ascent_faction_members "
        "WHERE tenant='tenant-b' AND player=$1", pb)
    assert member["faction"] == name
    assert (await _doc(pool, "tenant-b", pb))["gold"] == 75
    assert await pool.fetchval(
        "SELECT count(*) FROM ascent_happenings "
        "WHERE kind='faction' AND line LIKE '%joined%'") == 1


async def test_steward_writes_the_door_and_the_server_holds_it(
        client, tenant_a, tenant_b, clean_042):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Aldo")
    pb = await create_player(client, tenant_b, "tenant-b", "Brai")
    await _patch(pool, "tenant-a", pa, level=6, gold=2000)
    name = _name()
    await factions.create_faction(pool, "tenant-a", pa, name,
                                  "wolf_howl", "Aldo")
    await act(client, tenant_a, "tenant-a", pa, option="guildhall")
    await act(client, tenant_a, "tenant-a", pa, option="door_rules")
    await act(client, tenant_a, "tenant-a", pa, option="dr_lv_10")
    req = factions.parse_requirements(await pool.fetchval(
        "SELECT requirements FROM ascent_factions WHERE name=$1", name))
    assert req.get("min_level") == 10
    # the server holds the door even against a direct join
    err = await factions.join_faction(pool, "tenant-b", pb, name)
    assert err and "level 10" in err
    err = await factions.request_join(pool, "tenant-b", pb, name)
    assert err and "level 10" in err
