"""010 — faction colors: the named ink on the banner (real DB).

A founder picks one of the 9 roster slugs at creation; a steward can
change it from the desk; everyone else is refused; pre-plan rows read
warden-violet (the column default) so legacy banners keep the exact ink
their sigils always wore.
"""

import uuid

import pytest

from app import db, factions
from tests.test_factions import _set_money, post
from tests.test_factions import clean_factions, tenant_a, tenant_b  # noqa: F401
from tests.test_multiplayer import create_player


def _name():
    return f"Ink {uuid.uuid4().hex[:6]}"


async def _color_of(pool, name):
    return await pool.fetchval(
        "SELECT color FROM ascent_factions WHERE name=$1", name)


async def test_found_with_color_persists(client, tenant_a, clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Ember")
    await _set_money(pool, "tenant-a", pa, 2000, level=4)
    name = _name()
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl",
                    "color": "ember-red"})
    assert r.status_code == 200, r.text
    assert await _color_of(pool, name) == "ember-red"


async def test_found_without_color_defaults(client, tenant_a,
                                            clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Plain")
    await _set_money(pool, "tenant-a", pa, 2000, level=4)
    name = _name()
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl"})
    assert r.status_code == 200, r.text
    assert await _color_of(pool, name) == factions.DEFAULT_COLOR


async def test_found_with_unknown_color_refused(client, tenant_a,
                                                clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Pinky")
    await _set_money(pool, "tenant-a", pa, 2000, level=4)
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": _name(), "banner": "wolf_howl",
                    "color": "hot-pink"})
    assert r.status_code == 422 and "unknown color" in r.json()["detail"]


async def test_recolor_steward_only(client, tenant_a, tenant_b,
                                    clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Boss")
    pb = await create_player(client, tenant_b, "tenant-b", "Hand")
    await _set_money(pool, "tenant-a", pa, 2000, level=4)
    await _set_money(pool, "tenant-b", pb, 200)
    name = _name()
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl",
                    "color": "mouse-grey", "join_fee": 0})
    assert r.status_code == 200, r.text
    # seat pb as a plain member: request + approve
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/request",
                   {"player": pb, "name": name})
    assert r.status_code == 200, r.text
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/approve",
                   {"player": pa, "target_tenant": "tenant-b",
                    "target_player": pb})
    assert r.status_code == 200, r.text

    # the steward recolors
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/recolor",
                   {"player": pa, "color": "aether-teal"})
    assert r.status_code == 200, r.text
    assert await _color_of(pool, name) == "aether-teal"

    # a plain member is refused
    r = await post(client, tenant_b, "tenant-b", "/v1/faction/recolor",
                   {"player": pb, "color": "coin-gold"})
    assert r.status_code == 403, r.text
    assert await _color_of(pool, name) == "aether-teal"

    # an unknown slug is refused even for the steward
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/recolor",
                   {"player": pa, "color": "hot-pink"})
    assert r.status_code == 409, r.text
    assert await _color_of(pool, name) == "aether-teal"


async def test_member_payload_carries_color(client, tenant_a,
                                            clean_factions):
    pool = await db.get_pool()
    pa = await create_player(client, tenant_a, "tenant-a", "Shade")
    await _set_money(pool, "tenant-a", pa, 2000, level=4)
    name = _name()
    r = await post(client, tenant_a, "tenant-a", "/v1/faction/create",
                   {"player": pa, "name": name, "banner": "wolf_howl",
                    "color": "root-brown"})
    assert r.status_code == 200, r.text
    from app import social
    async with pool.acquire() as conn:
        panel = await social._faction_panel(conn, "tenant-a", pa, name)
    assert panel["color"] == "root-brown"


async def test_legacy_rows_default_to_warden_violet(client, tenant_a,
                                                    clean_factions):
    """A row inserted without the column (pre-plan shape) reads the
    DB default — the ink legacy sigils always wore."""
    pool = await db.get_pool()
    name = _name()
    await pool.execute(
        "INSERT INTO ascent_factions (name, banner, founder_tenant,"
        " founder_player, created_week, join_fee, weekly_dues) "
        "VALUES ($1,'wolf_howl','tenant-a','legacy',1,0,5)", name)
    assert await _color_of(pool, name) == "warden-violet"


def test_roster_mirrors_are_sane():
    assert len(factions.COLOR_SLUGS) == 9
    assert len(set(factions.COLOR_SLUGS)) == 9
    assert factions.DEFAULT_COLOR in factions.COLOR_SLUGS
