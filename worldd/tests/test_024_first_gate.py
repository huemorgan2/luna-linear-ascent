"""024 — the first gate, server half.

A pool is frozen at first blood, so a retune has to reach the sieges
already standing: production's floor-1 Warden carried a pool from the old
curve. Rows resize on read with the wound's depth intact — no striker's
work is erased and no row is dropped — and the next write stamps the new
tune.
"""

import datetime as dt
import json

import pytest

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402
from plugin_linear_ascent import economy  # noqa: E402
from tests.test_war_face import (_strike, _warden_row, clean_world,  # noqa: E402,F401
                                 tenant_a)


OLD_POOL = 1_064          # floor 1 under the pre-024 flat-8 curve


async def _seed_legacy_row(pool, hp, hp_max=OLD_POOL, floor=1, **extra):
    """A row exactly as the old code left it: no tune stamp."""
    v = {"hp": hp, "hp_max": hp_max, "pity": 0, "strikers": [],
         "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
         "called": [], "horns": [], **extra}
    await pool.execute(
        "INSERT INTO ascent_world (key, value) VALUES ($1,$2::jsonb) "
        "ON CONFLICT (key) DO UPDATE SET value=excluded.value",
        f"warden:{floor}", json.dumps(v))
    return v


def test_the_old_pool_really_was_the_thing_that_shrank():
    assert economy.world_warden_hp(1) < OLD_POOL / 3


async def test_a_legacy_pool_resizes_and_keeps_the_wound_depth(
        client, tenant_a, clean_world):
    pool = await db.get_pool()
    v = await _seed_legacy_row(pool, hp=OLD_POOL // 2)
    st = social._warden_now(v, 1, None)
    assert st["hp_max"] == economy.world_warden_hp(1)
    # half-cut before, half-cut after — the siege's progress survives
    assert st["hp"] == pytest.approx(st["hp_max"] / 2, abs=1)


async def test_an_untouched_legacy_pool_resizes_to_full(client, tenant_a,
                                                        clean_world):
    pool = await db.get_pool()
    v = await _seed_legacy_row(pool, hp=OLD_POOL)
    st = social._warden_now(v, 1, None)
    assert st["hp"] == st["hp_max"] == economy.world_warden_hp(1)


async def test_a_legacy_pity_ramp_survives_the_resize(client, tenant_a,
                                                      clean_world):
    pool = await db.get_pool()
    v = await _seed_legacy_row(pool, hp=OLD_POOL, pity=2)
    st = social._warden_now(v, 1, None)
    expected = round(economy.world_warden_hp(1)
                     * (1 - economy.WARDEN_PITY_PCT) ** 2)
    assert st["hp_max"] == expected
    assert st["base"] == economy.world_warden_hp(1)


async def test_the_next_strike_stamps_the_tune_and_the_new_pool(
        client, tenant_a, clean_world):
    pool = await db.get_pool()
    await _seed_legacy_row(pool, hp=OLD_POOL)
    await _strike("tenant-a", "p-024", {"name": "Kettle"}, 1, 30)
    v = await _warden_row(pool)
    assert v["tune"] == economy.WARDEN_POOL_TUNE
    assert v["hp_max"] == economy.world_warden_hp(1)
    assert v["hp"] == economy.world_warden_hp(1) - 30
    # a resized row is stable: reading it again must not shrink it twice
    st = social._warden_now(v, 1, None)
    assert st["hp_max"] == economy.world_warden_hp(1)


async def test_two_strikes_close_the_first_gate(client, tenant_a,
                                               clean_world):
    """The complaint, answered end to end: one player, two full fights."""
    pool = await db.get_pool()
    unit = economy.strike_fight_damage(1)
    # the fall rolls loot on the doc — a real one, not a name-only stub
    doc = {"name": "Kettle", "luna_user": "t:solo", "rng_counter": 0,
           "gold": 0, "xp": 0, "inventory": {}, "unlocked_floor": 1}
    await _strike("tenant-a", "p-solo", doc, 1, unit)
    v = await _warden_row(pool)
    assert v is not None and v["hp"] > 0          # still standing, wounded
    await _strike("tenant-a", "p-solo", doc, 1, unit)
    frontier = await pool.fetchval(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    assert int(json.loads(frontier)) == 2         # the floor opened
