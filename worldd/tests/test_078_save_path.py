"""078 Phase 4 — the batched ledger write.

Golden fixture: one save carrying three ledger entries lands three rows,
in entry order, with identical content to the old per-row loop.
"""

import json

from app import gamepath

gamepath.ensure_game_importable()

from app import db, game  # noqa: E402


async def test_ledger_batch_preserves_order_and_content(client):
    pool = await db.get_pool()
    await pool.execute(
        "INSERT INTO ascent_tenants (tenant, secret) VALUES ('t078s', 's') "
        "ON CONFLICT (tenant) DO NOTHING")
    await pool.execute(
        "INSERT INTO ascent_players (tenant, player, doc) "
        "VALUES ('t078s', 'saver', $1) ON CONFLICT (tenant, player) "
        "DO UPDATE SET doc = EXCLUDED.doc",
        json.dumps({"stage": "playing", "name": "Saver", "gear": {}}))
    await pool.execute(
        "DELETE FROM ascent_ledger WHERE tenant='t078s'")
    ledger = [
        {"kind": "kill", "gold": 12, "xp": 30, "note": "first blood"},
        {"kind": "loot", "gold": 5, "note": "the purse"},
        {"kind": "levelup", "xp": 0, "note": "n" * 300},   # clipped to 256
    ]
    doc = {"stage": "playing", "name": "Saver", "gear": {}, "gold": 17}
    async with pool.acquire() as conn:
        async with conn.transaction():
            await game._save_doc(conn, "t078s", "saver", doc, ledger)
    rows = await pool.fetch(
        "SELECT kind, gold, xp, note FROM ascent_ledger "
        "WHERE tenant='t078s' AND player='saver' ORDER BY id")
    assert [dict(r) for r in rows] == [
        {"kind": "kill", "gold": 12, "xp": 30, "note": "first blood"},
        {"kind": "loot", "gold": 5, "xp": 0, "note": "the purse"},
        {"kind": "levelup", "gold": 0, "xp": 0, "note": "n" * 256},
    ]
    saved = await pool.fetchrow(
        "SELECT doc, gold FROM ascent_players "
        "WHERE tenant='t078s' AND player='saver'")
    assert json.loads(saved["doc"])["gold"] == 17
    assert saved["gold"] == 17          # projection follows the write
    await pool.execute("DELETE FROM ascent_ledger WHERE tenant='t078s'")
    await pool.execute("DELETE FROM ascent_players WHERE tenant='t078s'")
