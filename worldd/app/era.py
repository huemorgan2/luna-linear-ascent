"""022/007 — the era: the ending, the frozen ledger, reincarnation, reset.

The game ends, together, on purpose — and the Tower remembers. Two
tables are PERMANENT (ascent_eras, ascent_reincarnation) plus
ascent_tenants (auth is not era state); everything else is wiped by
`era_reset`. v1 ruling: eras cannot end in defeat — a broken party at
100 refunds and regroups; only Vharuk's fall closes the book.
"""

from __future__ import annotations

import json

from . import gamepath

gamepath.ensure_game_importable()

from plugin_linear_ascent import economy  # noqa: E402
from plugin_linear_ascent.engine import state as pstate  # noqa: E402
from plugin_linear_ascent.engine.scene import Scene  # noqa: E402

# Every ascent_* table that does NOT survive the era. ascent_tenants,
# ascent_eras and ascent_reincarnation are deliberately absent.
TRANSIENT_TABLES = (
    "ascent_players", "ascent_world", "ascent_ledger",
    "ascent_idempotency", "ascent_letters", "ascent_happenings",
    "ascent_boss_commits", "ascent_guilds", "ascent_stone",
    "ascent_factions", "ascent_faction_members", "ascent_attendance",
    "ascent_faction_weeks", "ascent_faction_ledger",
    "ascent_faction_requests", "ascent_armory", "ascent_armory_takes",
    "ascent_faction_notes", "ascent_faction_bed_claims",
)
PERMANENT_TABLES = ("ascent_eras", "ascent_reincarnation",
                    "ascent_accounts", "ascent_names")

# The mark is earned, not given: a level-5 climber has cleared mercy's
# floors and paid the first training fees — tourists don't reincarnate.
REINCARNATION_MIN_LEVEL = 5


async def current_era(conn) -> int:
    """The era being PLAYED — one past the last frozen ledger."""
    last = await conn.fetchval("SELECT coalesce(max(era), 0) FROM ascent_eras")
    return int(last) + 1


async def close_era(conn, tenant: str, player: str, doc: dict,
                    commits: list) -> int:
    """Vharuk fell. Freeze the ledger, grant reincarnation, hand every
    climber the closing ceremony. The caller (the resolving act) still
    holds `doc` in memory and saves it LAST — so the finisher's ceremony
    is appended to that doc, never to their row."""
    era = await current_era(conn)
    day = pstate.world_day()
    finisher = doc.get("name") or player
    party = [c["name"] for c in commits]
    committed = {(c["tenant"], c["player"]) for c in commits}

    stone = [r["line"] for r in await conn.fetch(
        "SELECT line FROM ascent_stone ORDER BY id")]
    factions = [dict(r) for r in await conn.fetch(
        "SELECT name, count(m.player) AS members FROM ascent_factions f "
        "LEFT JOIN ascent_faction_members m ON m.faction = f.name "
        "GROUP BY f.name ORDER BY members DESC")]
    rows = await conn.fetch("SELECT tenant, player, doc FROM ascent_players")

    data = {
        "era": era, "world_day": day, "finisher": finisher,
        "war_party": party, "population": len(rows),
        "factions": factions[:12],
        # the era's whole Stone, frozen — first clears, the war's lines,
        # the fall. Readable in-game forever.
        "stone": stone[-400:],
    }
    await conn.execute(
        "INSERT INTO ascent_eras (era, data) VALUES ($1, $2::jsonb)",
        era, json.dumps(data))

    ceremony = Scene(
        eyebrow=f"ERA {era} · THE TOWER FALLS",
        headline="Vharuk, the Demon King, is cast down",
        support=f"The final blow was {finisher}'s. The era closes; "
                "the Tower remembers every name on its Stone.",
        body_lines=[
            f"Day {day}. {len(party)} blades stood in the last siege.",
            "The Stone of Eras keeps this era's ledger forever — "
            "read it in any era to come.",
            "Climbers of level 5 and above carry a reincarnation mark "
            "into the next era: doors open early, and you wake rested.",
            "The world will be made again from floor 1. Same tower, "
            "new war.",
        ],
        event_kind="boss",
    ).to_dict()

    for r in rows:
        me = r["tenant"] == tenant and r["player"] == player
        # the resolving player's row is stale mid-act — their truth is
        # the in-memory doc the caller saves after us.
        d = doc if me else json.loads(r["doc"])
        if d.get("stage") != "playing":
            continue
        # reincarnation: one point per level-5+ climber of the era,
        # tiers from the FROZEN moment — never recomputed later.
        if int(d.get("level", 1)) >= REINCARNATION_MIN_LEVEL:
            tiers = []
            if int(d.get("unlocked_floor", 1)) >= 100:
                tiers.append("stood_100")
            if (r["tenant"], r["player"]) in committed:
                tiers.append("struck_vharuk")
            if me:
                tiers.append("final_blow")      # one per era, ever
            await conn.execute(
                "INSERT INTO ascent_reincarnation (tenant, player, era,"
                " name, points, tiers) VALUES ($1,$2,$3,$4,1,$5::jsonb) "
                "ON CONFLICT DO NOTHING",
                r["tenant"], r["player"], era, d.get("name") or "",
                json.dumps(tiers))
        # the ceremony reaches EVERYONE on their next visit — including
        # climbers offline during the fall.
        d.setdefault("pending_events", []).append(ceremony)
        if not me:
            await conn.execute(
                "UPDATE ascent_players SET doc=$3, updated_at=now() "
                "WHERE tenant=$1 AND player=$2",
                r["tenant"], r["player"], json.dumps(d))

    await conn.execute(
        "INSERT INTO ascent_stone (line) VALUES ($1)",
        f"ERA {era} — Vharuk cast down on day {day}; the final blow "
        f"was {finisher}'s")
    await conn.execute(
        "INSERT INTO ascent_happenings (world_day, kind, line, floor) "
        "VALUES ($1,'war',$2,100)", day,
        f"THE TOWER FALLS — Vharuk is down. Era {era} closes; "
        "the ceremony waits in town")
    return era


async def declare_last_siege(conn, active: int | None) -> None:
    """The frontier just reached 100 — the siege is DECLARED, not
    stumbled into: Crier, Stone, and a letter to every climber (006's
    megaphone, reused)."""
    quorum = economy.milestone_quorum(100, active)
    day = pstate.world_day()
    line = (f"THE LAST FLOOR IS OPEN — Vharuk, the Demon King, waits at "
            f"100. The war party forms at the keep: {quorum} blades "
            "pledged inside two days end the era")
    await conn.execute(
        "INSERT INTO ascent_happenings (world_day, kind, line, floor) "
        "VALUES ($1,'war',$2,100)", day, line)
    await conn.execute(
        "INSERT INTO ascent_stone (line) VALUES ($1)",
        "Floor 100 stands open — the era enters its last siege")
    rows = await conn.fetch(
        "SELECT tenant, player FROM ascent_players "
        "WHERE doc->>'stage'='playing'")
    for r in rows:
        await conn.execute(
            "INSERT INTO ascent_letters (to_tenant, to_player, from_name,"
            " body) VALUES ($1,$2,$3,$4)",
            r["tenant"], r["player"], "the Morning Crier", line + ".")


async def era_reset(conn) -> dict:
    """Wipe the transient world; the permanent tables survive; boot the
    new era (frontier 1, Warden 1 waiting, the Stone's first line names
    the era). DESTRUCTIVE — the caller owns the transaction and the
    decision. tools/era_reset.py wraps this with a dry-run."""
    era = await current_era(conn)
    counts = {}
    for t in TRANSIENT_TABLES:
        counts[t] = int(await conn.fetchval(f"SELECT count(*) FROM {t}"))
        await conn.execute(f"DELETE FROM {t}")
    await conn.execute(
        "INSERT INTO ascent_world (key, value) VALUES ('frontier',"
        " '1'::jsonb)")
    await conn.execute(
        "INSERT INTO ascent_stone (line) VALUES ($1)",
        f"ERA {era} — the tower stands again. Frontier: floor 1. "
        "Vharuk waits at the top.")
    return {"era": era, "wiped": counts}


async def prestige_boot(conn, tenant: str, player: str, doc: dict) -> None:
    """A brand-new doc for a name the reincarnation ledger knows: glyph
    points and the perks. Prestige buys TIME, never power — early doors
    (plugin reads doc['prestige']) and a pre-filled rested pool at the
    level-1 cap (005's law holds: the cap is the cap, prestige included)."""
    rows = await conn.fetch(
        "SELECT era, points, tiers FROM ascent_reincarnation "
        "WHERE tenant=$1 AND player=$2 ORDER BY era", tenant, player)
    if not rows:
        return
    tiers: list[str] = []
    for r in rows:
        for t in json.loads(r["tiers"]):
            if t not in tiers:
                tiers.append(t)
    doc["prestige"] = {"points": sum(int(r["points"]) for r in rows),
                       "eras": [int(r["era"]) for r in rows],
                       "tiers": tiers}
    doc["rested"] = economy.rested_pool_cap(1)
