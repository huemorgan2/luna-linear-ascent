"""World-side social machinery.

`inject_world` fills doc["_world"] before the engine runs;
`execute_effects` applies doc["_effects"] after — same transaction, so a
turn either fully lands or fully rolls back. PvP and boss quorums resolve
here (offline: results are queued into victims'/committers' docs as
pending_events, delivered on their next scene).
"""

from __future__ import annotations

import json

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import state as pstate
from plugin_linear_ascent.engine.scene import Scene


# ── Injection ────────────────────────────────────────────────────────────

async def inject_world(conn, tenant: str, player: str, doc: dict) -> None:
    w: dict = {"social": True}
    day = pstate.world_day()

    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    w["frontier"] = int(json.loads(row["value"])) if row else 1

    w["inbox_count"] = await conn.fetchval(
        "SELECT count(*) FROM ascent_letters "
        "WHERE to_tenant=$1 AND to_player=$2 AND NOT read", tenant, player)

    happ = await conn.fetch(
        "SELECT line FROM ascent_happenings WHERE world_day >= $1 "
        "ORDER BY id DESC LIMIT 5", day - 1)
    w["happenings"] = [r["line"] for r in happ]

    stone = await conn.fetch(
        "SELECT line FROM ascent_stone ORDER BY id DESC LIMIT 8")
    w["stone"] = [r["line"] for r in stone]

    # loaded unconditionally: the upcoming action may move the player into
    # any social scene, and injection happens before the engine runs.
    rows = await conn.fetch(
        "SELECT id, from_name, body, gold FROM ascent_letters "
        "WHERE to_tenant=$1 AND to_player=$2 AND NOT read "
        "ORDER BY id DESC LIMIT 8", tenant, player)
    w["letters"] = [dict(r) for r in rows]
    w["names"] = await _known_names(conn, doc)
    w["pvp_targets"] = await _pvp_targets(conn, tenant, player, doc, day)
    w["grant_targets"] = await _grant_targets(conn, doc)

    w["roster"], w["roster_count"] = await _roster(conn)

    rows = await conn.fetch(
        "SELECT guild FROM ascent_guilds ORDER BY created_at LIMIT 6")
    w["guilds"] = [r["guild"] for r in rows]
    if doc.get("guild"):
        roster = await conn.fetch(
            "SELECT doc->>'name' AS name FROM ascent_players "
            "WHERE doc->>'guild' = $1 AND doc->>'stage' = 'playing'",
            doc["guild"])
        w["guild_roster"] = [r["name"] for r in roster if r["name"]]

    floor = max(1, doc.get("floor", 1))
    if floor in economy.MILESTONES:
        commits = await conn.fetch(
            "SELECT name FROM ascent_boss_commits "
            "WHERE floor=$1 AND world_day >= $2 ORDER BY created_at",
            floor, day - 2)
        ms = economy.MILESTONES[floor]
        w["boss"] = {
            "committed": [r["name"] for r in commits],
            "quorum": ms.quorum,
        }

    doc["_world"] = w


async def _roster(conn) -> tuple[list[dict], int]:
    """The Muster Roll: every playing climber, strongest floors first.
    Banked-wealth rank is over the whole roster; the board shows 12."""
    rows = await conn.fetch(
        "SELECT doc, updated_at FROM ascent_players "
        "WHERE doc->>'stage'='playing'")
    now = pstate.now()
    entries = []
    for r in rows:
        d = json.loads(r["doc"])
        entries.append({
            "name": d.get("name") or "a climber",
            "race": d.get("race") or "?",
            "clazz": d.get("clazz") or "?",
            "level": d.get("level", 1),
            "power": pstate.atk(d) + pstate.dfs(d),
            "floor": d.get("unlocked_floor", 1),
            "bank": d.get("bank", 0),
            "last_seen_days": max(0, (now - r["updated_at"]).days),
        })
    by_bank = sorted(entries, key=lambda e: -e["bank"])
    for rank, e in enumerate(by_bank, 1):
        e["bank_rank"] = rank
        del e["bank"]                      # rank is public, balance is not
    entries.sort(key=lambda e: (-e["floor"], -e["level"]))
    return entries[:12], len(entries)


async def _known_names(conn, doc: dict) -> list[str]:
    rows = await conn.fetch(
        "SELECT doc->>'name' AS name FROM ascent_players "
        "WHERE doc->>'stage'='playing' ORDER BY updated_at DESC LIMIT 12")
    me = doc.get("name")
    return [r["name"] for r in rows if r["name"] and r["name"] != me]


async def _pvp_targets(conn, tenant: str, player: str, doc: dict,
                       day: int) -> list[dict]:
    rows = await conn.fetch(
        "SELECT tenant, player, doc FROM ascent_players "
        "WHERE doc->>'stage'='playing' AND NOT (tenant=$1 AND player=$2) "
        "ORDER BY updated_at DESC LIMIT 30", tenant, player)
    out = []
    for r in rows:
        d = json.loads(r["doc"])
        if d.get("lodged_until_day", -1) >= day + 1:
            continue                     # paid the Lodge — safe tonight
        if d.get("level", 1) <= economy.BEGINNER_PROTECTION_MAX_LEVEL:
            continue
        out.append({"tenant": r["tenant"], "player": r["player"],
                    "name": d.get("name") or r["player"],
                    "level": d.get("level", 1)})
        if len(out) >= 6:
            break
    return out


async def _grant_targets(conn, doc: dict) -> list[str]:
    rows = await conn.fetch(
        "SELECT doc->>'name' AS name, (doc->>'level')::int AS level "
        "FROM ascent_players WHERE doc->>'stage'='playing' "
        "ORDER BY updated_at DESC LIMIT 20")
    me = doc.get("name")
    return [r["name"] for r in rows
            if r["name"] and r["name"] != me
            and r["level"] >= economy.GRANT_MIN_RECEIVER_LEVEL][:6]


# ── Effects ──────────────────────────────────────────────────────────────

async def execute_effects(conn, tenant: str, player: str,
                          doc: dict) -> None:
    effects = doc.pop("_effects", [])
    for e in effects:
        kind = e.get("kind")
        if kind == "send_letter":
            await _fx_send_letter(conn, doc, e)
        elif kind == "collect_letter_gold":
            await _fx_collect_gold(conn, tenant, player, doc)
        elif kind == "grant":
            await _fx_grant(conn, doc, e)
        elif kind == "pvp_attack":
            await _fx_pvp(conn, tenant, player, doc, e)
        elif kind == "boss_commit":
            await _fx_boss_commit(conn, tenant, player, doc, e)
        elif kind == "letters_seen":
            await conn.execute(
                "UPDATE ascent_letters SET read=TRUE "
                "WHERE id = ANY($1::bigint[]) AND gold=0", e.get("ids", []))
        elif kind == "guild_found":
            await conn.execute(
                "INSERT INTO ascent_guilds (guild, founder) VALUES ($1,$2) "
                "ON CONFLICT DO NOTHING", e["guild"], doc.get("name") or player)
        elif kind == "happening":
            # engine-reported world news: deaths, warden first clears
            await conn.execute(
                "INSERT INTO ascent_happenings (world_day, kind, line) "
                "VALUES ($1,'climb',$2)", pstate.world_day(),
                str(e.get("line", ""))[:200])
        # guild_join / guild_leave live entirely in the doc


async def _find_player_by_name(conn, name: str):
    return await conn.fetchrow(
        "SELECT tenant, player, doc FROM ascent_players "
        "WHERE doc->>'name' = $1 AND doc->>'stage'='playing' "
        "ORDER BY updated_at DESC LIMIT 1", name)


async def _fx_send_letter(conn, doc: dict, e: dict) -> None:
    row = await _find_player_by_name(conn, e["to_name"])
    if row is None:
        return
    await conn.execute(
        "INSERT INTO ascent_letters (to_tenant, to_player, from_name, body)"
        " VALUES ($1,$2,$3,$4)",
        row["tenant"], row["player"], doc.get("name") or "a climber",
        e["body"])


async def _fx_collect_gold(conn, tenant: str, player: str,
                           doc: dict) -> None:
    rows = await conn.fetch(
        "SELECT id, gold FROM ascent_letters "
        "WHERE to_tenant=$1 AND to_player=$2 AND NOT read AND gold > 0",
        tenant, player)
    total = sum(r["gold"] for r in rows)
    if total:
        doc["gold"] += total
        await conn.execute(
            "UPDATE ascent_letters SET read=TRUE, gold=0 "
            "WHERE id = ANY($1::bigint[])", [r["id"] for r in rows])
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note)"
            " VALUES ($1,$2,'letter_gold',$3,'collected')",
            tenant, player, total)


async def _fx_grant(conn, doc: dict, e: dict) -> None:
    row = await _find_player_by_name(conn, e["to_name"])
    if row is None:
        # refund — receiver vanished between scene and act
        doc["gold"] += e["gross"]
        return
    await conn.execute(
        "INSERT INTO ascent_letters (to_tenant, to_player, from_name, body,"
        " gold) VALUES ($1,$2,$3,$4,$5)",
        row["tenant"], row["player"], doc.get("name") or "a climber",
        f"A grant of ◈ {e['net']:,} — collected at the Relay Office.",
        e["net"])
    await conn.execute(
        "INSERT INTO ascent_ledger (tenant, player, kind, gold, note)"
        " VALUES ($1,$2,'grant_in',$3,$4)",
        row["tenant"], row["player"], e["net"],
        f"from {doc.get('name') or 'unknown'}")


def _power(d: dict) -> int:
    return (pstate.atk(d) * 2 + pstate.dfs(d)
            + d.get("hp", 1) // 4)


async def _fx_pvp(conn, tenant: str, player: str, doc: dict,
                  e: dict) -> None:
    row = await _find_player_by_name(conn, e["target_name"])
    if row is None:
        return
    victim = json.loads(row["doc"])
    day = pstate.world_day()
    # deterministic swing from the attacker's stream
    swing = 0.8 + 0.4 * (pstate.rng_int(doc, 0, 1000) / 1000.0)
    attacker_wins = _power(doc) * swing >= _power(victim)
    a_name = doc.get("name") or "a climber"
    v_name = victim.get("name") or "a climber"

    if attacker_wins:
        loot = victim.get("gold", 0)
        victim["gold"] = 0
        victim["hp"] = max(1, pstate.max_hp(victim) // 4)
        doc["gold"] += loot
        bounty = int(economy.xp_need(victim.get("level", 1))
                     * economy.PVP_XP_BOUNTY_PCT)
        doc["xp"] += bounty
        victim.setdefault("pending_events", []).append(_death_report(
            v_name, a_name, loot).to_dict())
        line = f"{a_name} ambushed {v_name} in the fields (◈ {loot:,} taken)"
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, xp, note)"
            " VALUES ($1,$2,'pvp_win',$3,$4,$5)",
            tenant, player, loot, bounty, f"vs {v_name}")
    else:
        loot = doc.get("gold", 0)
        doc["gold"] = 0
        doc["hp"] = max(1, pstate.max_hp(doc) // 4)
        victim["gold"] = victim.get("gold", 0) + loot
        victim.setdefault("pending_events", []).append(Scene(
            eyebrow="ROOTHOLLOW · WORD FROM THE FIELDS",
            headline=f"{a_name} came for you in the night — and lost",
            support="You fought half-asleep and won anyway.",
            body_lines=[f"+ ◈ {loot:,} pried from their pack"],
            event_kind="loot",
        ).to_dict())
        line = f"{a_name} tried {v_name} in the fields and crawled home"
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note)"
            " VALUES ($1,$2,'pvp_loss',$3,$4)",
            tenant, player, -loot, f"vs {v_name}")

    await conn.execute(
        "UPDATE ascent_players SET doc=$3, updated_at=now() "
        "WHERE tenant=$1 AND player=$2",
        row["tenant"], row["player"], json.dumps(victim))
    await conn.execute(
        "INSERT INTO ascent_happenings (world_day, kind, line) "
        "VALUES ($1,'pvp',$2)", day, line)
    # attacker sees the outcome immediately as a pending event
    doc.setdefault("pending_events", []).insert(0, Scene(
        eyebrow="THE FIELDS · AFTER",
        headline=("You took them in their sleep" if attacker_wins
                  else "They were waiting for you"),
        support=line,
        body_lines=([f"+ ◈ {loot:,} carried gold seized"] if attacker_wins
                    else [f"− ◈ {loot:,} carried gold lost"]),
        event_kind="loot" if attacker_wins else "death",
    ).to_dict())


def _death_report(victim: str, attacker: str, loot: int) -> Scene:
    return Scene(
        eyebrow="ROOTHOLLOW · A BAD MORNING",
        headline=f"{attacker} found you in the fields",
        support="You skipped the Lodge. The fields keep no one's secrets.",
        body_lines=[
            "You wake bruised at the foot of the Stone.",
            f"− ◈ {loot:,} carried gold, taken",
            "Banked gold untouched. The Vault keeps its word.",
        ],
        event_kind="death",
        banner="death",
    )


async def _fx_boss_commit(conn, tenant: str, player: str, doc: dict,
                          e: dict) -> None:
    floor = int(e["floor"])
    day = pstate.world_day()
    name = doc.get("name") or player
    await conn.execute(
        "INSERT INTO ascent_boss_commits (floor, tenant, player, name,"
        " world_day) VALUES ($1,$2,$3,$4,$5) ON CONFLICT DO NOTHING",
        floor, tenant, player, name, day)
    ms = economy.MILESTONES.get(floor)
    if ms is None:
        return
    commits = await conn.fetch(
        "SELECT tenant, player, name FROM ascent_boss_commits "
        "WHERE floor=$1 AND world_day >= $2", floor, day - 2)
    if len(commits) < ms.quorum:
        return
    await _resolve_boss(conn, tenant, player, doc, ms, commits)


async def _resolve_boss(conn, tenant: str, player: str, doc: dict,
                        ms, commits) -> None:
    day = pstate.world_day()
    party_power = 0
    docs: list[tuple[str, str, dict]] = []
    for c in commits:
        if c["tenant"] == tenant and c["player"] == player:
            d = doc
        else:
            row = await conn.fetchrow(
                "SELECT doc FROM ascent_players WHERE tenant=$1 AND "
                "player=$2 FOR UPDATE", c["tenant"], c["player"])
            if row is None:
                continue
            d = json.loads(row["doc"])
        docs.append((c["tenant"], c["player"], d))
        party_power += _power(d)

    boss_power = ms.atk * 2 + ms.dfs + ms.hp // 4
    swing = 0.9 + 0.2 * (pstate.rng_int(doc, 0, 1000) / 1000.0)
    victory = party_power * swing >= boss_power * 0.75

    names = ", ".join(c["name"] for c in commits)
    for t, pl, d in docs:
        if victory:
            d["xp"] = d.get("xp", 0) + ms.xp
            d["gold"] = d.get("gold", 0) + ms.gold
            if d.get("unlocked_floor", 1) <= ms.floor:
                d["unlocked_floor"] = ms.floor + 1
            ev = Scene(
                eyebrow=f"FLOOR {ms.floor} · THE KEEP · AFTER",
                headline=f"{ms.name} has fallen",
                support=f"The war party held: {names}.",
                body_lines=[f"+ {ms.xp:,} experience",
                            f"+ ◈ {ms.gold:,} from the hoard",
                            f"FLOOR {ms.floor + 1} stands open for everyone."],
                event_kind="boss",
            )
        else:
            ev = Scene(
                eyebrow=f"FLOOR {ms.floor} · THE KEEP · AFTER",
                headline=f"{ms.name} holds the keep",
                support="The party broke against it. Pledges refunded.",
                body_lines=["Regroup. Stronger blades, better steel."],
                event_kind="boss",
            )
            pstate.gain_energy(d, economy.COST_BOSS_COMMIT)
        d.setdefault("pending_events", []).append(ev.to_dict())
        if not (t == tenant and pl == player):
            await conn.execute(
                "UPDATE ascent_players SET doc=$3, updated_at=now() "
                "WHERE tenant=$1 AND player=$2", t, pl, json.dumps(d))
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, xp,"
            " note) VALUES ($1,$2,$3,$4,$5,$6)",
            t, pl, "boss_win" if victory else "boss_loss",
            ms.gold if victory else 0, ms.xp if victory else 0, ms.name)

    await conn.execute(
        "DELETE FROM ascent_boss_commits WHERE floor=$1", ms.floor)
    if victory:
        await conn.execute(
            "UPDATE ascent_world SET value=$1::jsonb "
            "WHERE key='frontier' AND (value)::int < $2",
            json.dumps(ms.floor + 1), ms.floor + 1)
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'boss',$2)", day,
            f"{ms.name} fell to {names} — floor {ms.floor + 1} is open")
        await conn.execute(
            "INSERT INTO ascent_stone (line) VALUES ($1)",
            f"Floor {ms.floor} — {ms.name} cast down by {names}")
    else:
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'boss',$2)", day,
            f"{ms.name} broke a war party at the keep ({names})")
