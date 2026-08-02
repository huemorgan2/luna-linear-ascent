"""The faction armory (017 phase 007) — a shared rack of gear.

The EV law (plan 007 §1): no gold ever enters or leaves through the
armory. A deposit moves (slug, wear-stash) out of the donor's doc into
a row; a take moves the SAME pair back into the taker's pack — a
round-trip is worth exactly zero, whatever the pawn broker pays today.
Caps guard the two remaining abuses: bought chest slots per faction
(storage — 032 turned the flat 50-row roof into CHEST_SLOTS tiers) and
one take per player per world day (vacuuming). Member-only both ways.
"""

from __future__ import annotations

from .gamepath import ensure_game_importable

ensure_game_importable()

from plugin_linear_ascent import economy  # noqa: E402
from plugin_linear_ascent.engine import state as pstate  # noqa: E402

from . import factions  # noqa: E402


async def slot_cap(conn, faction: str) -> int:
    """The chest's bought capacity (032) — CHEST_SLOTS by chest tier."""
    tier = await conn.fetchval(
        "SELECT chest_tier FROM ascent_factions WHERE name=$1", faction)
    return factions.CHEST_SLOTS.get(int(tier or 1),
                                    factions.CHEST_SLOTS[1])


def _gear(slug: str):
    g = economy.FORGE.get(slug)
    return g if (g is not None and g.price > 0) else None


async def shelf(conn, faction: str) -> list[dict]:
    """The rack, oldest first — what inject_world hands the engine."""
    rows = await conn.fetch(
        "SELECT id, slug, uses_left, donor_name FROM ascent_armory "
        "WHERE faction=$1 ORDER BY id", faction)
    out = []
    for r in rows:
        g = _gear(r["slug"])
        if g is None:
            continue
        pool = economy.item_pool(g)
        left = r["uses_left"] if r["uses_left"] is not None else pool
        out.append({"id": r["id"], "slug": r["slug"], "name": g.name,
                    "slot": g.slot, "bonus": g.bonus,
                    "frac": round(min(1.0, left / pool), 2) if pool else 1.0,
                    "donor": r["donor_name"] or "a member"})
    return out


async def deposit(conn, tenant: str, player: str, doc: dict,
                  slug: str, uses_left: int | None) -> str | None:
    """Called from the engine's armory_deposit effect — the engine has
    already lifted the item (and its wear stash) out of the doc; this
    validates and shelves it, or returns an error so the caller can
    hand the piece back."""
    if _gear(slug) is None:
        return "the armory racks paid steel only"
    mine = await factions.member_row(conn, tenant, player)
    if not mine:
        return "only members reach the armory racks"
    cap = await slot_cap(conn, mine["faction"])
    count = await conn.fetchval(
        "SELECT count(*) FROM ascent_armory WHERE faction=$1",
        mine["faction"])
    if count >= cap:
        return (f"the chest is full — {cap} slots, every one filled. "
                "The works sell a bigger one")
    await conn.execute(
        "INSERT INTO ascent_armory "
        "(faction, tenant, player, donor_name, slug, uses_left) "
        "VALUES ($1,$2,$3,$4,$5,$6)",
        mine["faction"], tenant, player,
        str(doc.get("name") or player)[:32], slug, uses_left)
    return None


async def take(conn, tenant: str, player: str, doc: dict,
               item_id: int) -> str | None:
    """Desk take, called from the armory_take effect: move a rack row
    into the taker's pack (the doc in flight — the caller saves it),
    wear intact. One take per world day — a commons, not a mine."""
    mine = await factions.member_row(conn, tenant, player)
    if not mine:
        return "only members reach the armory racks"
    day = pstate.world_day()
    prior = await conn.fetchval(
        "SELECT take_day FROM ascent_armory_takes "
        "WHERE tenant=$1 AND player=$2", tenant, player)
    if prior is not None and int(prior) >= day:
        return "one piece a day — the racks open again tomorrow"
    row = await conn.fetchrow(
        "SELECT id, slug, uses_left FROM ascent_armory "
        "WHERE id=$1 AND faction=$2 FOR UPDATE", item_id, mine["faction"])
    if row is None:
        return "that piece already left the rack"
    slug = row["slug"]
    inv = doc.setdefault("inventory", {})
    inv[slug] = int(inv.get(slug, 0)) + 1
    if row["uses_left"] is not None:
        # the wear rides with the piece — never laundered to full. The
        # pack keeps ONE stash per slug: when a copy is already there,
        # the worse of the two survives (anything else launders).
        pack = doc.setdefault("durability_pack", {})
        cur = pack.get(slug)
        pack[slug] = (int(row["uses_left"]) if cur is None
                      else min(int(cur), int(row["uses_left"])))
    await conn.execute("DELETE FROM ascent_armory WHERE id=$1", row["id"])
    await conn.execute(
        "INSERT INTO ascent_armory_takes (tenant, player, take_day) "
        "VALUES ($1,$2,$3) ON CONFLICT (tenant, player) "
        "DO UPDATE SET take_day=$3", tenant, player, day)
    return None
