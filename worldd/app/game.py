"""World game service — runs the plugin engine against worldd storage.

One row per (tenant, player); scenes computed by the same engine the
plugin ships. Row-level locking (SELECT ... FOR UPDATE) serializes a
player's turns; idempotency rows dedupe retried mutations. The world
frontier is shared across tenants.
"""

from __future__ import annotations

import json

from .gamepath import ensure_game_importable

ensure_game_importable()

from plugin_linear_ascent.engine import combat  # noqa: E402
from plugin_linear_ascent.engine import core  # noqa: E402
from plugin_linear_ascent.engine import state as pstate  # noqa: E402
from plugin_linear_ascent.engine.scene import Scene  # noqa: E402
from plugin_linear_ascent.sheet import character_sheet  # noqa: E402

from . import db  # noqa: E402


async def _world_frontier(conn) -> int:
    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    return int(json.loads(row["value"])) if row else 1


async def _raise_frontier(conn, floor: int) -> None:
    await conn.execute(
        "UPDATE ascent_world SET value=$1::jsonb "
        "WHERE key='frontier' AND (value)::int < $2",
        json.dumps(floor), floor)
    # 078: an open floor must show on the very next click, not in TTL
    from . import worldcache
    worldcache.invalidate()


async def _load_doc(conn, tenant: str, player: str,
                    display_name: str = "") -> dict:
    row = await conn.fetchrow(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2 "
        "FOR UPDATE", tenant, player)
    if row:
        return json.loads(row["doc"])
    doc = pstate.new_player(f"{tenant}:{player}")
    if display_name:
        # 005 web play: the door already carved this name at signup
        # (names.ACCOUNT) — the doc boots named and the engine skips the
        # registrar's name ask.
        doc["name"] = display_name
    # 022/007: a name the reincarnation ledger knows boots with the
    # glyph and the time-perks (never power).
    from . import era
    await era.prestige_boot(conn, tenant, player, doc)
    await conn.execute(
        "INSERT INTO ascent_players (tenant, player, doc) "
        "VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
        tenant, player, json.dumps(doc))
    return doc


async def _save_doc(conn, tenant: str, player: str, doc: dict,
                    ledger: list[dict]) -> None:
    await conn.execute(
        "UPDATE ascent_players SET doc=$3, updated_at=now() "
        "WHERE tenant=$1 AND player=$2",
        tenant, player, json.dumps(doc))
    if ledger:
        # 078: one round trip for the whole receipt — executemany keeps
        # insertion (and therefore id) order.
        await conn.executemany(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, xp,"
            " note) VALUES ($1,$2,$3,$4,$5,$6)",
            [(tenant, player, e.get("kind", ""), int(e.get("gold", 0)),
              int(e.get("xp", 0)), str(e.get("note", ""))[:256])
             for e in ledger])


def _sync_frontier_into_doc(doc: dict, frontier: int) -> None:
    if frontier > doc.get("unlocked_floor", 1):
        doc["unlocked_floor"] = frontier


def _patch_kill_receipt(doc: dict, scene) -> None:
    """033: the Warden fell in THIS request — `_warden_fall` settled the
    finisher's share after the engine had already drawn the card, so
    the settled numbers land on the outgoing scene here. The receipt
    (minus the one-shot `_new` flag) stays on the doc for the rest of
    the fall reel; the reel's exit pops it."""
    receipt = doc.get("kill_receipt") or {}
    if not receipt.pop("_new", False):
        return
    new = combat.kill_receipt_lines(
        {k: receipt[k] for k in ("xp", "gold", "loot", "shared")
         if k in receipt})
    lines = list(scene.body_lines)
    if lines and lines[-1].startswith("FLOOR"):
        lines[-1:-1] = new          # the open-floor line stays last
    else:
        lines += new
    scene.body_lines = lines
    if receipt.get("names"):
        scene.support = f"Struck down by {receipt['names']}."
    scene.tally = [{"kind": "gold", "n": int(receipt.get("gold", 0))},
                   {"kind": "aether", "n": int(receipt.get("xp", 0))}]


def _patch_loot_receipt(doc: dict, scene) -> None:
    """042: the raid resolved in THIS request — `_fx_loot` queued the
    attacker's verdict after the engine had already drawn the "you slip
    toward the camp" card. The verdict takes the card's face here; the
    profile's buttons stay so the raider can walk back. Popping it now
    also keeps it from re-playing on the next act."""
    q = doc.get("pending_events") or []
    if not q or (q[0] or {}).get("eyebrow") != "THE FIELDS · AFTER":
        return
    ev = q.pop(0)
    scene.eyebrow = ev.get("eyebrow", "")
    scene.headline = ev.get("headline", "")
    scene.support = ev.get("support", "")
    scene.body_lines = list(ev.get("body_lines") or [])
    scene.event_kind = ev.get("event_kind", "")
    scene.banner = ev.get("banner", "")


async def _claim_name(conn, tenant: str, player: str, doc: dict,
                      option: str, text: str) -> str:
    """004: the registrar, before the engine writes anything.

    A name is unique across the whole world, and only worldd can know that.
    The claim happens inside this turn's transaction — two climbers racing
    for `Fleet` in the same instant cannot both win — and the verdict rides
    into the engine on `_world`, which decides what the card says. Returns
    the name it newly reserved (so a refusal can give it back), or "".
    """
    if doc.get("stage") != "creation_name" or option or not text:
        return ""
    from . import names
    want = names.canonical(text)
    if not names.is_legal(want):
        return ""                      # the engine refuses it on its own
    verdict = await names.claim(conn, want, names.CLIMBER, tenant, player)
    doc["_world"]["name_claim"] = verdict
    return want if verdict == names.CREATED else ""


async def run_scene(tenant: str, player: str,
                    display_name: str = "") -> dict:
    from . import social
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            doc = await _load_doc(conn, tenant, player, display_name)
            await social.inject_world(conn, tenant, player, doc)
            _sync_frontier_into_doc(doc, doc["_world"]["frontier"])
            scene: Scene = core.current_scene(doc)
            ledger = doc.pop("_ledger", [])
            await social.execute_effects(conn, tenant, player, doc)
            doc.pop("_world", None)
            doc["scene"] = scene.to_dict()
            await _save_doc(conn, tenant, player, doc, ledger)
            return scene.to_dict()


# 081: effects that move gold/letters mid-act — the card apply_choice
# built predates them and must be rebuilt from the settled doc.
_REFRESH_KINDS = {"collect_letter_gold"}


async def run_act(tenant: str, player: str, option: str, text: str,
                  idem: str, display_name: str = "") -> dict:
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            if idem:
                prior = await conn.fetchrow(
                    "SELECT response FROM ascent_idempotency "
                    "WHERE tenant=$1 AND idem=$2", tenant, idem)
                if prior:
                    return json.loads(prior["response"])
            from . import factions, social
            # 010: any act marks today attended; the player's faction
            # resolves its previous week lazily on the first act of a
            # new one.
            first_today = await factions.record_attendance(conn, tenant,
                                                           player)
            mine = await factions.member_row(conn, tenant, player)
            if mine:
                await factions.maybe_resolve(conn, mine["faction"])
            doc = await _load_doc(conn, tenant, player, display_name)
            if first_today and doc.get("stage") == "playing":
                await social.add_happening(
                    conn, kind="climb",
                    line=f"{doc.get('name') or 'A climber'} entered "
                         "the tower",
                    actor=doc.get("name"), faction=doc.get("guild"))
            await social.inject_world(conn, tenant, player, doc,
                                      option=option)
            before = doc.get("unlocked_floor", 1)
            _sync_frontier_into_doc(doc, doc["_world"]["frontier"])
            reserved = await _claim_name(conn, tenant, player, doc,
                                         option, text)
            scene = core.apply_choice(doc, option, text)
            if reserved and doc.get("name") != reserved:
                from . import names
                await names.release(conn, reserved, tenant, player)
            ledger = doc.pop("_ledger", [])
            fx = {e.get("kind") for e in doc.get("_effects") or ()}
            await social.execute_effects(conn, tenant, player, doc)
            _patch_kill_receipt(doc, scene)
            if option == "pf_loot_go":
                _patch_loot_receipt(doc, scene)
            if fx & _REFRESH_KINDS:
                # 081: these effects move gold/letters the already-built
                # card can't see — rebuild it on post-effect truth,
                # keeping the act's own note. Effects the rebuild emits
                # (letters_seen) run in a second pass, same transaction.
                got = doc.pop("_collected_gold", 0)
                await social.inject_world(conn, tenant, player, doc,
                                          option=option)
                fresh = core.current_scene(doc)
                if scene.shard_note and not fresh.shard_note:
                    fresh.shard_note = scene.shard_note
                if got and not fresh.shard_note:
                    fresh.shard_note = (f"The clerk counts out ◈ {got:,} "
                                        "— yours now.")
                scene = fresh
                await social.execute_effects(conn, tenant, player, doc)
            doc.pop("_world", None)
            doc["scene"] = scene.to_dict()
            await _save_doc(conn, tenant, player, doc, ledger)
            after = doc.get("unlocked_floor", 1)
            if after > before:
                await _raise_frontier(conn, after)
            out = scene.to_dict()
            if idem:
                await conn.execute(
                    "INSERT INTO ascent_idempotency (tenant, idem, response)"
                    " VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
                    tenant, idem, json.dumps(out))
        if after > before:
            # 078: invalidate AGAIN outside the transaction — a snapshot
            # rebuilt between the in-txn invalidate and this commit read
            # the old frontier and must not live out its TTL.
            from . import worldcache
            worldcache.invalidate()
        return out


_IMPORT_STAGES = {"intro", "creation_race", "creation_class",
                  "creation_name", "playing"}


def _sanitize_import(doc: dict) -> dict | None:
    """A migrated doc is tenant-authenticated but still client-supplied:
    strip transient keys and clamp the obvious levers."""
    if not isinstance(doc, dict) or doc.get("stage") not in _IMPORT_STAGES:
        return None
    clean = {k: v for k, v in doc.items()
             if isinstance(k, str) and not k.startswith("_")
             and k != "scene"}
    try:
        clean["level"] = max(1, min(100, int(clean.get("level", 1))))
        clean["gold"] = max(0, int(clean.get("gold", 0)))
        clean["bank"] = max(0, int(clean.get("bank", 0)))
        clean["xp"] = max(0, int(clean.get("xp", 0)))
        clean["unlocked_floor"] = max(
            1, min(100, int(clean.get("unlocked_floor", 1))))
        pstate.ensure_current(clean)
    except Exception:
        return None
    return clean


async def run_import(tenant: str, player: str, doc: dict) -> dict:
    clean = _sanitize_import(doc)
    if clean is None:
        return {"imported": False, "reason": "not a valid character doc"}
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            existing = await _load_doc(conn, tenant, player)
            if existing.get("stage") == "playing":
                return {"imported": False,
                        "reason": "a world character already exists"}
            clean["luna_user"] = f"{tenant}:{player}"
            out = {"imported": True}
            # 004: an offline name lands in a world where names are unique.
            # It cannot be sent back to the gate to pick again, so it takes
            # the nearest free name and is told which.
            if clean.get("name"):
                from . import names
                held = await names.claim_free(conn, clean["name"],
                                              tenant, player)
                if held != clean["name"]:
                    out["renamed"] = held
                    clean["name"] = held
            await _save_doc(conn, tenant, player, clean, [])
            return out


async def run_character(tenant: str, player: str) -> dict:
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            doc = await _load_doc(conn, tenant, player)
            if doc["stage"] != "playing":
                return {"status": "no character yet",
                        "hint": "Call ascent_scene to start creation."}
            return character_sheet(doc)
