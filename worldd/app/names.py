"""004 — one name, one world: the registry that makes a name unique.

A climber's name IS their username, and worldd is the only judge of who
holds one. Both doors write here — the site's sign-up and the gate's
registrar — so `Fleet` can never be handed out twice, in any tenant.

The rows are PERMANENT (see app/era.py): the Stone keeps what a climber
did, so an era reset must not hand their name to a stranger. Each row
remembers its owner, so the same hands reclaim their own name for free.

The naming law itself lives in the engine (engine/names.py) and is shared,
not restated: the gate and the door must agree on what a name even is.
"""

from __future__ import annotations

from .gamepath import ensure_game_importable

ensure_game_importable()

from plugin_linear_ascent.engine import names as pnames  # noqa: E402

canonical = pnames.canonical
is_legal = pnames.is_legal
NAME_MIN = pnames.NAME_MIN
NAME_MAX = pnames.NAME_MAX

CREATED = "created"      # the world had it free and now it is yours
MINE = "mine"            # you already held it (a retry, or a new era)
TAKEN = "taken"          # somebody else climbs under it

ACCOUNT = "account"
CLIMBER = "climber"


async def claim(conn, name: str, kind: str, tenant: str | None = None,
                player: str | None = None) -> str:
    """Reserve `name` for these hands. One statement decides it, so two
    climbers racing for the same name in the same instant cannot both win."""
    got = await conn.fetchval(
        "INSERT INTO ascent_names (name_lower, name, kind, tenant, player) "
        "VALUES (lower($1), $1, $2, $3, $4) "
        "ON CONFLICT (name_lower) DO NOTHING RETURNING name_lower",
        name, kind, tenant, player)
    if got is not None:
        return CREATED
    held = await conn.fetchrow(
        "SELECT kind, tenant, player FROM ascent_names "
        "WHERE name_lower = lower($1)", name)
    if (held is not None and kind == CLIMBER and held["kind"] == CLIMBER
            and held["tenant"] == tenant and held["player"] == player):
        return MINE
    return TAKEN


async def claim_free(conn, base: str, tenant: str, player: str) -> str:
    """Claim `base`, or the first free variant of it — Fleet, Fleet2, Fleet3.

    Only for names that arrive already carved: a character imported out of
    offline play cannot be sent back to the gate to pick again, so the world
    gives it the nearest free name instead of turning it away.
    """
    stem = canonical(base) or "climber"
    if len(stem) < NAME_MIN:
        stem = "climber"
    for n in range(1, 200):
        want = stem if n == 1 else f"{stem[:NAME_MAX - len(str(n))]}{n}"
        if await claim(conn, want, CLIMBER, tenant, player) != TAKEN:
            return want
    raise RuntimeError(f"no free name near {stem!r}")


async def release(conn, name: str, tenant: str, player: str) -> None:
    """Give a climber name back — used when the registrar reserved it and
    the engine then refused to carve it."""
    await conn.execute(
        "DELETE FROM ascent_names WHERE name_lower = lower($1) "
        "AND kind = $2 AND tenant = $3 AND player = $4",
        name, CLIMBER, tenant, player)


async def holder(conn, name: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT name, kind, tenant, player FROM ascent_names "
        "WHERE name_lower = lower($1)", name)
    return dict(row) if row else None
