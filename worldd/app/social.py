"""World-side social machinery.

`inject_world` fills doc["_world"] before the engine runs;
`execute_effects` applies doc["_effects"] after — same transaction, so a
turn either fully lands or fully rolls back. PvP and boss quorums resolve
here (offline: results are queued into victims'/committers' docs as
pending_events, delivered on their next scene).
"""

from __future__ import annotations

import datetime as dt
import json

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import state as pstate
from plugin_linear_ascent.engine.scene import Scene


# ── Injection ────────────────────────────────────────────────────────────

async def inject_world(conn, tenant: str, player: str, doc: dict) -> None:
    w: dict = {"social": True}
    day = pstate.world_day()

    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier'")
    w["frontier"] = int(json.loads(row["value"])) if row else 1

    # 010: factions are authoritative — the doc's guild string follows the
    # membership table (kicks land on the next load). Runs before the
    # happenings fetch so week-turn news lands in the same request.
    from . import factions
    await factions.sync_doc_guild(conn, tenant, player, doc)
    await factions.maybe_post_week(conn)
    if doc.get("guild"):
        await factions.maybe_resolve(conn, doc["guild"])
        # resolution may have charged THIS player's dues / paid a prize in
        # the DB copy; re-sync the money fields or the final doc save
        # would overwrite them
        fresh = await conn.fetchrow(
            "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
            tenant, player)
        if fresh:
            fd = json.loads(fresh["doc"])
            for k in ("gold", "bank", "faction_buff"):
                if k in fd:
                    doc[k] = fd[k]
                else:
                    doc.pop(k, None)
        w["faction"] = await _faction_panel(conn, tenant, player,
                                            doc["guild"])
        # 007: the shared rack rides in for members — the desk lists
        # it, the pawn scene offers the donate.
        from . import armory
        w["armory"] = await armory.shelf(conn, doc["guild"])
        w["armory_cap"] = armory.ARMORY_CAP
        prior = await conn.fetchval(
            "SELECT take_day FROM ascent_armory_takes "
            "WHERE tenant=$1 AND player=$2", tenant, player)
        w["armory_took_today"] = bool(prior is not None
                                      and int(prior) >= day)
    else:
        w["factions"] = await _faction_hall(conn)
        # 019: the hall's "Join a banner" row carries the true count,
        # not the top-10 window
        w["factions_total"] = await conn.fetchval(
            "SELECT count(*) FROM ascent_factions")
        w["faction_banners"] = factions.banner_slugs()
        # 015: the pending request, so the hall shows the asked state
        w["faction_requested"] = await factions.my_request(
            conn, tenant, player) or ""

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
    # 022/007: the Stone of Eras — permanent, readable in every era.
    eras = await conn.fetch(
        "SELECT era, data FROM ascent_eras ORDER BY era DESC LIMIT 5")
    w["eras"] = [
        (lambda d: f"ERA {r['era']} — fell on day {d.get('world_day', '?')}"
                   f" to {d.get('finisher', '?')} and "
                   f"{max(0, len(d.get('war_party', [])) - 1)} blades")
        (json.loads(r["data"])) for r in eras]

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

    # 007 §4 / 022: the census also sizes the warden pool and quorums
    w["census"] = await _census(conn)
    active = int(w["census"].get("total", 0))

    floor = max(1, doc.get("floor", 1))

    # 022/003: presence — who is on which floor RIGHT NOW. Counts and
    # torches for every floor: injection runs BEFORE the act, so the
    # player may be about to move — the engine picks its own floor.
    w["presence"] = await _presence(conn)
    if floor in economy.MILESTONES:
        commits = await conn.fetch(
            "SELECT name FROM ascent_boss_commits "
            "WHERE floor=$1 AND world_day >= $2 ORDER BY created_at",
            floor, day - 2)
        w["boss"] = {
            "committed": [r["name"] for r in commits],
            # 022/002: the war party rides the N(F) curve, never below
            # the hand-set table
            "quorum": economy.milestone_quorum(floor, active),
        }

    # 007 §3: the ONE live Warden at the world frontier
    w["warden"] = await _world_warden(conn, w["frontier"], active)
    news_floor = doc.get("floor", 0) or w["frontier"]
    gossip = await conn.fetch(
        "SELECT line FROM ascent_happenings "
        "WHERE floor=$1 AND world_day >= $2 ORDER BY id DESC LIMIT 3",
        news_floor, day - 1)
    w["gossip"] = [r["line"] for r in gossip]

    doc["_world"] = w


async def _faction_hall(conn) -> list[dict]:
    """The Guildhall list for the unbannered: fee + dues up front.
    015: top 10 by table size (the ledger)."""
    rows = await conn.fetch(
        "SELECT f.name, f.banner, f.join_fee, f.weekly_dues, "
        "count(m.player) AS members FROM ascent_factions f "
        "LEFT JOIN ascent_faction_members m ON m.faction=f.name "
        "GROUP BY f.name, f.banner, f.join_fee, f.weekly_dues "
        "ORDER BY members DESC, f.name LIMIT 10")
    return [dict(r) for r in rows]


async def _faction_panel(conn, tenant: str, player: str,
                         name: str) -> dict:
    """The member's Guildhall panel: store, dues, roster with attendance
    pips + arrears, this week's world challenge, the store ledger."""
    from . import factions
    fac = await conn.fetchrow(
        "SELECT banner, join_fee, weekly_dues, treasury,"
        " founder_tenant, founder_player "
        "FROM ascent_factions WHERE name=$1", name)
    if fac is None:
        return {}
    members = await factions.members_of(conn, name)
    week = factions.world_week()
    attend = await factions.week_attendance(conn, name, week)
    required = sum(factions.required_days(m["joined_day"], week)
                   for m in members)
    attended = sum(attend.get((m["tenant"], m["player"]), 0)
                   for m in members)
    kind = factions.week_kind(week)
    wrow = await factions.current_week_row(conn, name)
    entered = bool(wrow and wrow["entered"])
    avg_level = round(sum(m["level"] for m in members)
                      / max(1, len(members)))
    target = (int(wrow["goal_target"]) if entered else
              factions.suggest_targets(len(members), avg_level)[kind])
    progress = (await factions._progress(conn, name, kind, week)
                if entered else 0)
    my_role = next((m["role"] for m in members
                    if m["tenant"] == tenant and m["player"] == player),
                   "member")
    founder_key = (fac["founder_tenant"], fac["founder_player"])
    # 015: admins see the request queue size right in the Guildhall
    pending = 0
    if my_role == "steward":
        pending = int(await conn.fetchval(
            "SELECT count(*) FROM ascent_faction_requests "
            "WHERE faction=$1", name) or 0)
    ledger = await conn.fetch(
        "SELECT kind, amount, note FROM ascent_faction_ledger "
        "WHERE faction=$1 ORDER BY id DESC LIMIT 8", name)
    last = await conn.fetchrow(
        "SELECT prize_note FROM ascent_faction_weeks "
        "WHERE faction=$1 AND resolved ORDER BY week DESC LIMIT 1", name)
    return {
        "name": name, "banner": fac["banner"],
        "join_fee": int(fac["join_fee"]), "dues": int(fac["weekly_dues"]),
        "store": int(fac["treasury"]), "role": my_role,
        "pending_requests": pending,
        "members": [{
            "name": m["name"] or m["player"], "role": m["role"],
            "founder": (m["tenant"], m["player"]) == founder_key,
            "level": m["level"], "arrears": bool(m["arrears"]),
            "days": attend.get((m["tenant"], m["player"]), 0),
            "required": factions.required_days(m["joined_day"], week),
        } for m in members],
        "week": {
            "kind": kind, "target": target, "entered": entered,
            "progress": progress,
            "entry_cost": factions.entry_cost(len(members)),
            "attended": attended, "required": required,
            "multiplier": factions.attendance_multiplier(attended,
                                                         required),
            "base_pct": factions.base_pct(len(members)),
        },
        "ledger": [dict(r) for r in ledger],
        "last_week": (last["prize_note"] if last else ""),
    }


async def _census(conn) -> dict:
    """Climbers by current floor (town counts as floor 1 — Roothollow)."""
    rows = await conn.fetch(
        "SELECT greatest(coalesce((doc->>'floor')::int, 0), 1) AS fl, "
        "count(*) AS n FROM ascent_players "
        "WHERE doc->>'stage'='playing' GROUP BY 1")
    by_floor = {int(r["fl"]): int(r["n"]) for r in rows}
    return {"total": sum(by_floor.values()), "by_floor": by_floor}


# ── Presence (022 §003) ──────────────────────────────────────────────────
# Roy's rule: HOT = acted on this floor within 3 minutes — the only tier
# that counts as "with you"; CAMPED = within the hour — texture, never
# company. A stale count is worse than a small one, so the cache TTL
# must stay strictly under the hot window (gated in tests).

PRESENCE_HOT_MIN = 3
PRESENCE_CAMP_MIN = 60
PRESENCE_TTL_S = 30.0
_TORCH_LIMIT = 6
# only these locations put a body ON a floor — a climber idling in
# Roothollow keeps a floor number in the doc but is not "with you"
_FIELD_LOCATIONS = ("gate_town", "warden_keep", "boss_keep")

_presence_cache: dict = {"at": None, "data": None}


def _torch_status(d: dict) -> str:
    """One word, derived — never asked for."""
    try:
        hurt = d.get("hp", 0) < 0.4 * pstate.max_hp(d)
    except Exception:
        hurt = False
    if hurt:
        return "hurt"
    if d.get("location") in ("warden_keep", "boss_keep") or \
            (d.get("encounter") or {}).get("kind") == "warden":
        return "at the keep"
    if d.get("encounter"):
        return "hunting"
    return "at the fire"


async def _presence(conn) -> dict:
    """{"by_floor": {floor: {"hot": n, "camped": n}},
        "torches": {floor: [{"name", "status"}, ...]}} — cached 30s."""
    now = pstate.now()
    cached_at = _presence_cache["at"]
    if _presence_cache["data"] is not None and cached_at is not None \
            and (now - cached_at).total_seconds() < PRESENCE_TTL_S:
        return _presence_cache["data"]
    rows = await conn.fetch(
        "SELECT doc, updated_at FROM ascent_players "
        "WHERE doc->>'stage'='playing' "
        "AND updated_at > now() - make_interval(mins => $1)",
        PRESENCE_CAMP_MIN)
    by_floor: dict[int, dict] = {}
    torches: dict[int, list] = {}
    for r in rows:
        d = json.loads(r["doc"])
        if d.get("location") not in _FIELD_LOCATIONS \
                and not d.get("encounter"):
            continue
        fl = max(1, int(d.get("floor") or 1))
        age_min = (now - r["updated_at"]).total_seconds() / 60
        slot = by_floor.setdefault(fl, {"hot": 0, "camped": 0})
        if age_min <= PRESENCE_HOT_MIN:
            slot["hot"] += 1
            t = torches.setdefault(fl, [])
            if len(t) < _TORCH_LIMIT:
                t.append({"name": d.get("name") or "a climber",
                          "status": _torch_status(d)})
        else:
            slot["camped"] += 1
    data = {"by_floor": by_floor, "torches": torches}
    _presence_cache.update(at=now, data=data)
    return data


# ── The shared frontier Warden (007 §3, curves by 022 §002) ──────────────

def _warden_now(v: dict, floor: int, active: int | None) -> dict:
    """The warden's TRUE current state from a stored row: lazy regen,
    the silence window (F > 30: quiet for W hours closes the wound
    fully), and the pity ramp (each fully-closed wound takes 3% off the
    max, forever). Pure — never persisted on read; only strikes write.

    Returns {hp, hp_max, pity, strikers, closed} where closed means the
    wound fully closed since the last write (the next write must record
    the pity and reset the siege)."""
    pity = int(v.get("pity", 0))

    def _max(k: int) -> int:
        base = int(v.get("hp_max", 0)) or economy.world_warden_hp(
            floor, active)
        return max(1, round(base * (1 - economy.WARDEN_PITY_PCT) ** k))

    hp_max = _max(pity)
    hp = int(v.get("hp", hp_max))
    try:
        ts = dt.datetime.fromisoformat(v["ts"])
        hours = max(0.0, (pstate.now() - ts).total_seconds() / 3600)
    except Exception:
        hours = 0.0
    w = economy.warden_silence_hours(floor)
    closed = hp < hp_max and (
        (w is not None and hours >= w)
        or hp + hp_max * economy.world_warden_regen_hourly(floor) * hours
        >= hp_max)
    if closed:
        pity += 1
        hp_max = _max(pity)
        return {"hp": hp_max, "hp_max": hp_max, "pity": pity,
                "strikers": [], "closed": True, "closes_in_s": None}
    rate = hp_max * economy.world_warden_regen_hourly(floor)
    hp = min(hp_max, round(hp + rate * hours))
    # 022/006: the countdown the card shows — the wound closes at the
    # silence deadline or at full regen, whichever lands first. Zero
    # extra state; pure arithmetic off the same ts the close law reads.
    closes_in_s = None
    if hp < hp_max:
        cands = []
        if w is not None:
            cands.append(max(0.0, w - hours))
        if rate > 0:
            cands.append((hp_max - hp) / rate)
        if cands:
            closes_in_s = max(0, round(min(cands) * 3600))
    return {"hp": hp, "hp_max": hp_max, "pity": pity,
            "strikers": v.get("strikers", []), "closed": False,
            "closes_in_s": closes_in_s}


async def _world_warden(conn, frontier: int,
                        active: int = 0) -> dict | None:
    if frontier in economy.MILESTONES or \
            frontier > schema.max_content_floor():
        return None                    # milestone quorum / end of content
    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key=$1", f"warden:{frontier}")
    if row is None:
        hp_max = economy.world_warden_hp(frontier, active or None)
        return {"floor": frontier, "hp": hp_max, "hp_max": hp_max,
                "strikers": [], "pity": 0, "closes_in_s": None}
    st = _warden_now(json.loads(row["value"]), frontier, active or None)
    return {"floor": frontier, "hp": st["hp"], "hp_max": st["hp_max"],
            "strikers": st["strikers"], "pity": st["pity"],
            "closes_in_s": st["closes_in_s"]}


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
        # 022/007: reincarnation glyphs ride every social surface
        pts = int((d.get("prestige") or {}).get("points", 0))
        glyph = " " + "✦" * min(pts, 3) if pts else ""
        entries.append({
            "name": (d.get("name") or "a climber") + glyph,
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
        elif kind == "warden_strike":
            await _fx_warden_strike(conn, tenant, player, doc, e)
        elif kind == "horn":
            await _fx_horn(conn, tenant, player, doc, e)
        elif kind == "letters_seen":
            await conn.execute(
                "UPDATE ascent_letters SET read=TRUE "
                "WHERE id = ANY($1::bigint[]) AND gold=0", e.get("ids", []))
        elif kind == "guild_found":
            # legacy table kept in sync for audit; factions are the system
            await conn.execute(
                "INSERT INTO ascent_guilds (guild, founder) VALUES ($1,$2) "
                "ON CONFLICT DO NOTHING", e["guild"], doc.get("name") or player)
            await _fx_faction_found(conn, tenant, player, doc, e)
        elif kind == "guild_join":
            from . import factions
            err = await factions.join_faction(conn, tenant, player,
                                              e["guild"], doc)
            if err:
                doc.pop("guild", None)   # optimistic colors come down
        elif kind == "faction_request":
            # 015: joining is a request an admin accepts at the desk
            from . import factions
            await factions.request_join(conn, tenant, player, e["guild"])
        elif kind == "guild_leave":
            from . import factions
            await factions.leave_faction(conn, tenant, player)
        elif kind == "faction_donate":
            from . import factions
            await factions.donate(conn, tenant, player,
                                  int(e.get("amount", 0)), doc,
                                  payer_name=doc.get("name") or player)
        elif kind == "faction_enter":
            from . import factions
            await factions.enter_week(conn, tenant, player)
        elif kind == "faction_kick":
            await _fx_faction_kick(conn, tenant, player, e)
        elif kind == "happening":
            # engine-reported world news: deaths, warden first clears
            await conn.execute(
                "INSERT INTO ascent_happenings (world_day, kind, line,"
                " floor) VALUES ($1,'climb',$2,$3)", pstate.world_day(),
                str(e.get("line", ""))[:200], int(e.get("floor", 0)))
        elif kind == "armory_deposit":
            # 007: the engine already lifted the piece (and its wear
            # stash) out of the doc; a refusal hands it straight back
            # and says so by letter — never a silent vanish (003 law).
            from . import armory
            uses = e.get("uses_left")
            err = await armory.deposit(
                conn, tenant, player, doc, str(e.get("slug", "")),
                int(uses) if uses is not None else None)
            if err:
                slug = str(e.get("slug", ""))
                inv = doc.setdefault("inventory", {})
                inv[slug] = int(inv.get(slug, 0)) + 1
                if uses is not None:
                    doc.setdefault("durability_pack", {})[slug] = int(uses)
                await conn.execute(
                    "INSERT INTO ascent_letters (to_tenant, to_player,"
                    " from_name, body) VALUES ($1,$2,$3,$4)",
                    tenant, player, "the armory keeper",
                    f"Your donation came back — {err}.")
        elif kind == "armory_take":
            # 007: the engine already validated against the injected
            # shelf; a race (row gone, cooldown) gets a letter, never
            # a silent vanish.
            from . import armory
            err = await armory.take(conn, tenant, player, doc,
                                    int(e.get("item_id", 0)))
            if err:
                await conn.execute(
                    "INSERT INTO ascent_letters (to_tenant, to_player,"
                    " from_name, body) VALUES ($1,$2,$3,$4)",
                    tenant, player, "the armory keeper",
                    f"The piece never left the rack — {err}.")
        # guild_join / guild_leave live entirely in the doc


async def _fx_faction_found(conn, tenant: str, player: str, doc: dict,
                            e: dict) -> None:
    """Engine-side founding (the Guildhall flow) — the ◈500 fee was
    already charged in the doc. The creation flow supplies banner, join
    fee and dues; a bare legacy effect gets a deterministic sigil."""
    from . import factions
    name = str(e["guild"])[:24]
    taken = await conn.fetchval(
        "SELECT 1 FROM ascent_factions WHERE name=$1", name)
    if taken:
        return                       # name raced — membership via join path
    slugs = factions.banner_slugs()
    banner = str(e.get("banner", "")) or slugs[sum(name.encode())
                                               % len(slugs)]
    if banner not in slugs:
        banner = slugs[sum(name.encode()) % len(slugs)]
    await factions.create_faction(
        conn, tenant, player, name, banner, doc.get("name") or player,
        join_fee=int(e.get("join_fee", 0)),
        weekly_dues=int(e.get("weekly_dues", 5)))


async def _fx_faction_kick(conn, tenant: str, player: str,
                           e: dict) -> None:
    """Steward removes a member by character name (the Guildhall list)."""
    from . import factions
    me = await factions.member_row(conn, tenant, player)
    if me is None or me["role"] != "steward":
        return
    target = str(e.get("name", ""))
    members = await factions.members_of(conn, me["faction"])
    for m in members:
        if (m["name"] or m["player"]) == target and \
                (m["tenant"], m["player"]) != (tenant, player):
            await conn.execute(
                "DELETE FROM ascent_faction_members "
                "WHERE tenant=$1 AND player=$2", m["tenant"], m["player"])
            break


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


# ── Shared frontier Warden strikes (007 §3) ──────────────────────────────

async def _fx_warden_strike(conn, tenant: str, player: str, doc: dict,
                            e: dict) -> None:
    """Land a strike on the world Warden. HP pool lives in ascent_world
    under warden:{floor}; the kill raises the frontier for everyone and
    splits the reward pool by damage dealt."""
    floor = int(e.get("floor", 0))
    dmg = max(0, int(e.get("damage", 0)))
    if dmg <= 0:
        return
    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key='frontier' FOR UPDATE")
    frontier = int(json.loads(row["value"])) if row else 1
    if floor != frontier or floor in economy.MILESTONES:
        # the world moved on between scene and click — refund the ⚡
        pstate.gain_energy(doc, economy.COST_WARDEN_ATTEMPT)
        return
    key = f"warden:{floor}"
    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key=$1 FOR UPDATE", key)
    active = await conn.fetchval(
        "SELECT count(*) FROM ascent_players WHERE doc->>'stage'='playing'")
    active = int(active or 0)
    warden_name = schema.get_floor(floor).warden_name
    name = doc.get("name") or player
    called: list[int] = []
    horns: list[str] = []
    if row is None:
        # first blood materialises the row — the pool is sized to the
        # world it faces and FROZEN there (022/002). 006: the Stone
        # remembers who cut first.
        base = economy.world_warden_hp(floor, active or None)
        st = {"hp": base, "hp_max": base, "pity": 0, "strikers": []}
        eff_max = base
        await conn.execute(
            "INSERT INTO ascent_stone (line) VALUES ($1)",
            f"Floor {floor} — {name} drew first blood on {warden_name}")
    else:
        v = json.loads(row["value"])
        st = _warden_now(v, floor, active or None)
        eff_max = st["hp_max"]              # post-pity, what fights see
        if not st["closed"]:
            # a NEW wound resets the once-per-wound slates
            called = [int(t) for t in v.get("called", [])]
            horns = list(v.get("horns", []))
        st["hp_max"] = int(v.get("hp_max", 0)) or economy.world_warden_hp(
            floor, active or None)          # the PRE-pity base, frozen
    strikers = list(st["strikers"])
    for s in strikers:
        if s.get("tenant") == tenant and s.get("player") == player:
            s["dmg"] = int(s.get("dmg", 0)) + dmg
            s["name"] = name
            s["ts"] = pstate.now().isoformat()      # 006: the hour roll
            s["guild"] = doc.get("guild") or ""     # 006: standings
            break
    else:
        strikers.append({"tenant": tenant, "player": player,
                         "name": name, "dmg": dmg,
                         "ts": pstate.now().isoformat(),
                         "guild": doc.get("guild") or ""})
    hp = st["hp"] - dmg
    if hp > 0:
        # 022/006: the Crier calls the wound at 75/50/25% — once per
        # wound, tower-wide (the `called` slate rides the row).
        before = 100 * st["hp"] / max(1, eff_max)
        after = 100 * hp / max(1, eff_max)
        for t in (75, 50, 25):
            if t not in called and before > t >= after:
                called.append(t)
                await conn.execute(
                    "INSERT INTO ascent_happenings (world_day, kind, line,"
                    " floor) VALUES ($1,'war',$2,$3)", pstate.world_day(),
                    f"{warden_name} is cut to {t}% on floor {floor} — "
                    "the wound is open, every blade counts", floor)
        await conn.execute(
            "INSERT INTO ascent_world (key, value) VALUES ($1,$2::jsonb) "
            "ON CONFLICT (key) DO UPDATE SET value=excluded.value",
            key, json.dumps({"hp": hp, "hp_max": st["hp_max"],
                             "pity": st["pity"],
                             "ts": pstate.now().isoformat(),
                             "called": called, "horns": horns,
                             "strikers": strikers[-40:]}))
        return
    await _warden_fall(conn, tenant, player, doc, floor, strikers,
                       active or None)


def _fmt_countdown(seconds: int | None) -> str:
    if seconds is None:
        return "when the tower forgets"
    h, m = int(seconds) // 3600, (int(seconds) % 3600) // 60
    return f"{h}h {m:02d}m" if h else f"{m}m"


async def _fx_horn(conn, tenant: str, player: str, doc: dict,
                   e: dict) -> None:
    """022/006: Sound the horn — one tap letters every guildmate with
    the floor and the countdown. Once per BANNER per wound (the horns
    slate rides the warden row and resets when the wound does); the
    write never touches ts — a horn must not feed the silence clock."""
    floor = int(e.get("floor", 0))
    guild = doc.get("guild")
    if not guild:
        return
    row = await conn.fetchrow(
        "SELECT value FROM ascent_world WHERE key=$1 FOR UPDATE",
        f"warden:{floor}")
    if row is None:
        return                              # no wound — nothing to call
    v = json.loads(row["value"])
    st = _warden_now(v, floor, None)
    if st["closed"] or st["hp"] >= st["hp_max"]:
        return
    horns = list(v.get("horns", []))
    if guild in horns:
        return
    horns.append(guild)
    v["horns"] = horns
    await conn.execute(
        "UPDATE ascent_world SET value=$1::jsonb WHERE key=$2",
        json.dumps(v), f"warden:{floor}")
    warden_name = schema.get_floor(floor).warden_name
    pct = max(0, round(100 * st["hp"] / max(1, st["hp_max"])))
    body = (f"The horn: {warden_name} stands at {pct}% on floor {floor}. "
            f"The wound closes in {_fmt_countdown(st['closes_in_s'])} — "
            "come cut.")
    rows = await conn.fetch(
        "SELECT tenant, player FROM ascent_players "
        "WHERE doc->>'guild' = $1 AND doc->>'stage' = 'playing'", guild)
    sounder = doc.get("name") or player
    for r in rows:
        if r["tenant"] == tenant and r["player"] == player:
            continue
        await conn.execute(
            "INSERT INTO ascent_letters (to_tenant, to_player, from_name,"
            " body) VALUES ($1,$2,$3,$4)",
            r["tenant"], r["player"], sounder, body)


async def _warden_fall(conn, tenant: str, player: str, doc: dict,
                       floor: int, strikers: list[dict],
                       active: int | None = None) -> None:
    day = pstate.world_day()
    warden_name = schema.get_floor(floor).warden_name
    await conn.execute("DELETE FROM ascent_world WHERE key=$1",
                       f"warden:{floor}")
    await conn.execute(
        "UPDATE ascent_world SET value=$1::jsonb "
        "WHERE key='frontier' AND (value)::int < $2",
        json.dumps(floor + 1), floor + 1)

    if floor + 1 == 100:
        # 022/007: the last floor just opened — the siege is DECLARED,
        # not stumbled into.
        from . import era
        await era.declare_last_siege(conn, active)
    total = max(1, sum(int(s.get("dmg", 0)) for s in strikers))
    mult = economy.world_warden_reward_mult(floor, active)
    xp_pool = round(economy.warden_xp(floor) * mult)
    gold_pool = round(economy.warden_gold(floor) * mult)
    # 022/006: the finisher is named FIRST — the clearing-group fame
    # line — then everyone else by damage dealt.
    def _is_finisher(s):
        return s.get("tenant") == tenant and s.get("player") == player
    roll = sorted(strikers,
                  key=lambda s: (not _is_finisher(s),
                                 -int(s.get("dmg", 0))))
    names = ", ".join(s.get("name") or "?" for s in roll)

    for s in strikers:
        finisher = s.get("tenant") == tenant and s.get("player") == player
        if finisher:
            d = doc
        else:
            row = await conn.fetchrow(
                "SELECT doc FROM ascent_players WHERE tenant=$1 AND "
                "player=$2 FOR UPDATE", s.get("tenant"), s.get("player"))
            if row is None:
                continue
            d = json.loads(row["doc"])
        share = int(s.get("dmg", 0)) / total
        xp_i = round(xp_pool * share)
        gold_i = round(gold_pool * share)
        d["xp"] = d.get("xp", 0) + xp_i
        d["gold"] = d.get("gold", 0) + gold_i
        if d.get("unlocked_floor", 1) <= floor:
            d["unlocked_floor"] = floor + 1
        body = [f"+ {xp_i:,} XP — your share of the kill",
                f"+ ◈ {gold_i:,} from the Warden's hoard"]
        if finisher:
            loot = pstate.rng_pick(
                d, [(60, "trollblood_tonic"), (40, "luck_charm")])
            inv = d.setdefault("inventory", {})
            inv[loot] = inv.get(loot, 0) + 1
            body.append("▪ the killing blow was yours — rare loot: "
                        f"{economy.APOTHECARY[loot].name}")
        body.append(f"FLOOR {floor + 1} stands open for everyone.")
        d.setdefault("pending_events", []).insert(0, Scene(
            eyebrow=f"FLOOR {floor} · THE KEEP · AFTER",
            headline=f"{warden_name} has fallen",
            support=f"Struck down by {names}.",
            body_lines=body,
            event_kind="boss",
        ).to_dict())
        if not finisher:
            await conn.execute(
                "UPDATE ascent_players SET doc=$3, updated_at=now() "
                "WHERE tenant=$1 AND player=$2",
                s.get("tenant"), s.get("player"), json.dumps(d))
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, xp,"
            " note) VALUES ($1,$2,'warden_kill',$3,$4,$5)",
            s.get("tenant"), s.get("player"), gold_i, xp_i, warden_name)

    await conn.execute(
        "INSERT INTO ascent_happenings (world_day, kind, line, floor) "
        "VALUES ($1,'boss',$2,$3)", day,
        f"{warden_name} fell to {names} — floor {floor + 1} is open "
        "for everyone", floor)
    top = max(strikers, key=lambda s: int(s.get("dmg", 0)))
    await conn.execute(
        "INSERT INTO ascent_stone (line) VALUES ($1)",
        f"Floor {floor} — the deepest cut in {warden_name} was "
        f"{top.get('name') or '?'}'s ({int(top.get('dmg', 0)):,})")
    await conn.execute(
        "INSERT INTO ascent_stone (line) VALUES ($1)",
        f"Floor {floor} — {warden_name} cast down by {names}")


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
    active = await conn.fetchval(
        "SELECT count(*) FROM ascent_players WHERE doc->>'stage'='playing'")
    if len(commits) < economy.milestone_quorum(floor, int(active or 0)
                                               or None):
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
        if ms.floor == 100:
            # 022/007: the era ends, together, on purpose.
            from . import era
            await era.close_era(conn, tenant, player, doc, commits)
    else:
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'boss',$2)", day,
            f"{ms.name} broke a war party at the keep ({names})")
