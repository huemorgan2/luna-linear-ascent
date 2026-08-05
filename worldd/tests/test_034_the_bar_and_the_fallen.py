"""034 — the server side of two corrections.

§2 the bar is the bar: every XP the world pays a doc goes through
`gain_xp`, so nothing lands past a full bar and the ledger records what
landed rather than what was offered.

§3 a Warden dies once: `fallen:{floor}` grew a date so the memorial in a
broken keep can say when, and both the new object shape and the legacy
bare-names string are read forever.
"""

import json
import uuid

import pytest

from app import db, social
from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import state as pstate
from tests.test_world_api import act, enter_floor, make_tenant, scene, signed  # noqa: F401


@pytest.fixture
async def tenant_a(client):
    return await make_tenant(client, "tenant-a")


@pytest.fixture
async def clean_world(client):
    pool = await db.get_pool()
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")
    await pool.execute("DELETE FROM ascent_world WHERE key LIKE 'warden:%'")
    yield
    await pool.execute(
        "UPDATE ascent_world SET value='1'::jsonb WHERE key='frontier'")
    await pool.execute("DELETE FROM ascent_world WHERE key LIKE 'warden:%'")


async def create_player(client, secret, tenant, name):
    player = f"p-{uuid.uuid4().hex[:8]}"
    await scene(client, secret, tenant, player)
    for _ in range(9):
        await act(client, secret, tenant, player, option="next")
    await act(client, secret, tenant, player, option="begin")
    await act(client, secret, tenant, player, option="human")
    await act(client, secret, tenant, player, option="warrior")
    await act(client, secret, tenant, player, text=name)
    return player


# ── §3 both shapes of the fall record ───────────────────────────────────

def test_a_legacy_names_string_reads_as_a_record():
    """`fallen:{floor}` held a bare JSON string until this plan. Rows
    written before it keep their names and simply have no date."""
    rec = social.fallen_record("MASTER-CHIEF, bob")
    assert rec == {"names": "MASTER-CHIEF, bob"}
    assert "day" not in rec


def test_a_dated_record_passes_through_untouched():
    full = {"names": "MASTER-CHIEF", "day": 41, "ts": "2026-08-01T09:12:03",
            "warden": "Warden Applewrath", "top": "MASTER-CHIEF",
            "top_dmg": 559}
    assert social.fallen_record(full) == full


def test_an_empty_row_does_not_explode():
    assert social.fallen_record(None) == {"names": ""}


async def test_the_world_payload_carries_the_fall_records(
        client, tenant_a, clean_world):
    """The memorial reads `fallen` off the TOP of the payload, not from
    under `warden` — which is None at a milestone frontier and at the
    end of content, and the memorial has to stand on every dead keep."""
    pool = await db.get_pool()
    await pool.execute(
        "INSERT INTO ascent_world (key, value) VALUES ($1,$2::jsonb) "
        "ON CONFLICT (key) DO UPDATE SET value=$2::jsonb",
        "fallen:1", json.dumps({"names": "Aldo", "day": 7,
                                "top": "Aldo", "top_dmg": 412}))
    try:
        p = await create_player(client, tenant_a, "tenant-a", "Reader")
        async with pool.acquire() as conn:
            doc = {"level": 1, "unlocked_floor": 1, "floor": 0}
            await social.inject_world(conn, "tenant-a", p, doc)
        w = doc["_world"]
        assert w["fallen"]["1"]["names"] == "Aldo"
        assert w["fallen"]["1"]["day"] == 7
        assert w["fallen"]["1"]["top_dmg"] == 412
        # 030's names-only map is untouched, so old clients keep reading
        assert w["warden"]["fallen_by"]["1"] == "Aldo"
    finally:
        await pool.execute(
            "DELETE FROM ascent_world WHERE key='fallen:1'")


async def test_a_legacy_row_survives_the_payload_round_trip(
        client, tenant_a, clean_world):
    pool = await db.get_pool()
    await pool.execute(
        "INSERT INTO ascent_world (key, value) VALUES ($1,$2::jsonb) "
        "ON CONFLICT (key) DO UPDATE SET value=$2::jsonb",
        "fallen:1", json.dumps("MASTER-CHIEF"))
    try:
        async with (await db.get_pool()).acquire() as conn:
            fallen = await social._fallen_map(conn)
        assert fallen["1"] == {"names": "MASTER-CHIEF"}
    finally:
        await pool.execute(
            "DELETE FROM ascent_world WHERE key='fallen:1'")


# ── §2 nothing the world pays lands past a full bar ─────────────────────

def test_gain_xp_is_the_only_door():
    """The four raw `doc["xp"] +=` sites are gone; this is the helper
    they now share, and it stops at the bar."""
    doc = {"level": 10, "xp": 0}
    need = economy.xp_need(10)
    assert pstate.gain_xp(doc, 10 * need) == need
    assert doc["xp"] == need
    assert pstate.gain_xp(doc, 1) == 0


def test_a_milestone_pays_more_than_a_bar_can_hold():
    """Floor 10's boss pays 1,500 into a bar that holds 758. Before this
    plan the surplus landed and then carried into level 11 for free."""
    ms = economy.MILESTONES[10]
    doc = {"level": 10, "xp": 0}
    landed = pstate.gain_xp(doc, ms.xp)
    assert landed == economy.xp_need(10) < ms.xp
    assert doc["xp"] == landed
