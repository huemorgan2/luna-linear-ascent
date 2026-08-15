"""060 — the toast fetch: scope=both, rows carry their scope, and the
in-process feed cache answers a burst without a second query.
"""

import uuid

from app import gamepath

gamepath.ensure_game_importable()

from app import db, social  # noqa: E402


def _reset():
    social._feed_head["id"] = None
    social._feed_cache.clear()


async def _add(conn, **kw):
    kw.setdefault("kind", "climb")
    kw.setdefault("line", "test line")
    await social.add_happening(conn, **kw)


async def test_both_is_world_plus_my_faction_with_scope_tags(client):
    _reset()
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    fac = f"Toast {tag}"
    ten = f"t-toast-{tag}"
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO ascent_tenants (tenant, secret) VALUES ($1,'s') "
            "ON CONFLICT DO NOTHING", ten)
        await conn.execute(
            "INSERT INTO ascent_factions (name) VALUES ($1) "
            "ON CONFLICT DO NOTHING", fac)
        await conn.execute(
            "INSERT INTO ascent_faction_members (tenant, player, faction) "
            "VALUES ($1,'m1',$2)", ten, fac)
        try:
            since = await social.feed_head(conn)
            await _add(conn, line=f"{tag} world")
            await _add(conn, line=f"{tag} mine", scope="faction",
                       faction=fac)
            await _add(conn, line=f"{tag} theirs", scope="faction",
                       faction="Some Other Faction")
            out = await social.playing_feed(conn, ten, "m1", "both", since)
            got = {r["line"]: r["scope"] for r in out["rows"]}
            assert got[f"{tag} world"] == "world"
            assert got[f"{tag} mine"] == "faction"
            assert f"{tag} theirs" not in got
            assert out["faction"] == fac
            # newest first, no duplicates
            ids = [r["id"] for r in out["rows"]]
            assert ids == sorted(ids, reverse=True)
            assert len(ids) == len(set(ids))

            # a memberless caller: world only, still tagged
            out = await social.playing_feed(conn, ten, "loner", "both",
                                            since)
            got = {r["line"]: r["scope"] for r in out["rows"]}
            assert got == {f"{tag} world": "world"}
            assert out["faction"] is None
        finally:
            await conn.execute(
                "DELETE FROM ascent_faction_members WHERE tenant=$1", ten)
            await conn.execute(
                "DELETE FROM ascent_factions WHERE name=$1", fac)


async def test_feed_cache_answers_a_burst_and_refills_on_news(client):
    _reset()
    pool = await db.get_pool()
    tag = uuid.uuid4().hex[:8]
    async with pool.acquire() as conn:
        since = await social.feed_head(conn)
        await _add(conn, line=f"{tag} first")
        out = await social.playing_feed(conn, "t-none", "nobody", "world",
                                        since)
        assert f"{tag} first" in [r["line"] for r in out["rows"]]

        # same head, inside the TTL: no fetch reaches the connection
        class Boom:
            async def fetch(self, *a, **k):
                raise AssertionError("cache miss")

            def __getattr__(self, name):
                return getattr(conn, name)

        out2 = await social.playing_feed(Boom(), "t-none", "nobody",
                                         "world", since)
        assert [r["id"] for r in out2["rows"]] == \
            [r["id"] for r in out["rows"]]

        # news moves the head — the next read refills from the table
        await _add(conn, line=f"{tag} second")
        out3 = await social.playing_feed(conn, "t-none", "nobody", "world",
                                         since)
        assert f"{tag} second" in [r["line"] for r in out3["rows"]]
