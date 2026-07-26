"""Factions (plan 010) — membership, weekly goals, attendance, prizes.

The whole mechanic in one module:

  required   = Σ members min(4, days the member could still play that week)
  attended   = Σ members unique act-days while a member (cap 7 each)
  ratio      = attended / required
  multiplier = 0 if ratio < 0.5 else min(ratio, 7/4)        # cap 175%
  base_pct   = 15% under 4 members, 20% at 4+
  prize      = base_pct × goal × multiplier

Weeks are world_day // 7 (worlddays roll at 06:00 UTC). Resolution is
lazy — the first faction-touching request of a new week resolves the
previous one inside the caller's transaction; the UNIQUE(faction, week)
row in ascent_faction_weeks is the idempotency lock.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re

from .gamepath import ensure_game_importable

ensure_game_importable()

from plugin_linear_ascent.engine import state as pstate  # noqa: E402

WEEK_DAYS = 7
REQUIRED_DAYS = 4          # showing up 4 days = 100% of the prize
MIN_RATIO = 0.5            # below half the required member-days → nothing
MAX_MULT = 7 / 4           # perfect 7-day attendance (confirmed: 175%)
SMALL_FACTION_MAX = 3      # ≤3 members → 15% base; 4+ → 20%
BASE_PCT_SMALL = 0.15
BASE_PCT_FULL = 0.20
FOUND_FEE = 500            # matches the engine's Guildhall fee
GOAL_KINDS = ("hoard", "cull", "climb")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '\-]{2,23}$")

# ── The faction store (plan 010, third directive) ────────────────────────
JOIN_FEE_MAX = 500         # set at founding, immutable
DUES_MIN, DUES_MAX = 1, 50  # per member per world-week
ENTRY_PER_MEMBER = 5       # the weekly challenge entry, paid from the store

_BANNER_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "vendor",
    "plugin_linear_ascent", "content", "art", "banners", "factions")


def banner_slugs() -> list[str]:
    try:
        return sorted(f[:-len("_320x112.png")]
                      for f in os.listdir(_BANNER_DIR)
                      if f.endswith("_320x112.png"))
    except OSError:
        return ["wolf_howl"]


def world_week(day: int | None = None) -> int:
    return (pstate.world_day() if day is None else day) // WEEK_DAYS


def week_bounds_ts(week: int) -> tuple[dt.datetime, dt.datetime]:
    """UTC timestamps covering the week's world_days (for ledger scans)."""
    def day_start(d: int) -> dt.datetime:
        return (pstate._EPOCH.replace(hour=0)
                + dt.timedelta(days=d, hours=pstate.WORLD_DAY_UTC_HOUR))
    return day_start(week * WEEK_DAYS), day_start((week + 1) * WEEK_DAYS)


def base_pct(members: int) -> float:
    return BASE_PCT_SMALL if members <= SMALL_FACTION_MAX else BASE_PCT_FULL


def required_days(joined_day: int, week: int) -> int:
    """4 member-days, prorated for a mid-week join."""
    start = week * WEEK_DAYS
    if joined_day <= start:
        return REQUIRED_DAYS
    remaining = start + WEEK_DAYS - joined_day
    return max(0, min(REQUIRED_DAYS, remaining))


def attendance_multiplier(attended: int, required: int) -> float:
    if required <= 0:
        return 0.0
    ratio = attended / required
    if ratio < MIN_RATIO:
        return 0.0
    return min(ratio, MAX_MULT)


def suggest_targets(members: int, avg_level: int) -> dict:
    """Per-faction challenge targets scaled to the crew."""
    m, lv = max(1, members), max(1, avg_level)
    return {
        "hoard": 300 * lv * m,     # ≈ a solid 4-day hunting week of gold
        "cull": 50 * m,            # kills
        "climb": 200 * lv * m,     # xp
    }


def week_kind(week: int) -> str:
    """The world posts ONE challenge kind per week — every banner chases
    the same thing (rivalry for free, one Crier headline)."""
    return GOAL_KINDS[week % len(GOAL_KINDS)]


def entry_cost(members: int) -> int:
    return ENTRY_PER_MEMBER * max(1, members)


# ── Store ledger (audit — every treasury movement writes a row) ──────────

async def store_ledger(conn, faction: str, week: int, kind: str,
                       amount: int, tenant: str = "", player: str = "",
                       note: str = "") -> None:
    await conn.execute(
        "INSERT INTO ascent_faction_ledger (faction, week, kind, amount,"
        " tenant, player, note) VALUES ($1,$2,$3,$4,$5,$6,$7)",
        faction, week, kind, amount, tenant, player, note[:120])


async def _load_doc(conn, tenant: str, player: str) -> dict | None:
    row = await conn.fetchrow(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
        tenant, player)
    return json.loads(row["doc"]) if row else None


async def _save_doc(conn, tenant: str, player: str, doc: dict) -> None:
    await conn.execute(
        "UPDATE ascent_players SET doc=$3, updated_at=now() "
        "WHERE tenant=$1 AND player=$2", tenant, player, json.dumps(doc))


def take_gold(doc: dict, amount: int) -> bool:
    """Charge carried gold first, then the bank. False = can't cover."""
    gold, bank = int(doc.get("gold", 0)), int(doc.get("bank", 0))
    if gold + bank < amount:
        return False
    take = min(gold, amount)
    doc["gold"] = gold - take
    doc["bank"] = bank - (amount - take)
    return True


# ── Attendance ────────────────────────────────────────────────────────────

async def record_attendance(conn, tenant: str, player: str) -> None:
    await conn.execute(
        "INSERT INTO ascent_attendance (tenant, player, world_day) "
        "VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
        tenant, player, pstate.world_day())


# ── Membership helpers ───────────────────────────────────────────────────

async def member_row(conn, tenant: str, player: str):
    return await conn.fetchrow(
        "SELECT faction, role, joined_day FROM ascent_faction_members "
        "WHERE tenant=$1 AND player=$2", tenant, player)


async def members_of(conn, faction: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT m.tenant, m.player, m.role, m.joined_day, m.arrears,"
        "       p.doc->>'name' AS name,"
        "       coalesce((p.doc->>'level')::int, 1) AS level "
        "FROM ascent_faction_members m "
        "LEFT JOIN ascent_players p ON p.tenant=m.tenant "
        "  AND p.player=m.player "
        "WHERE m.faction=$1 ORDER BY m.joined_day, m.player", faction)
    return [dict(r) for r in rows]


async def week_attendance(conn, faction: str, week: int) -> dict:
    """{(tenant, player): unique days attended this week while a member}."""
    lo, hi = week * WEEK_DAYS, (week + 1) * WEEK_DAYS
    rows = await conn.fetch(
        "SELECT a.tenant, a.player, count(DISTINCT a.world_day) AS days "
        "FROM ascent_attendance a "
        "JOIN ascent_faction_members m ON m.tenant=a.tenant "
        "  AND m.player=a.player AND m.faction=$1 "
        "WHERE a.world_day >= $2 AND a.world_day < $3 "
        "  AND a.world_day >= m.joined_day "
        "GROUP BY a.tenant, a.player", faction, lo, hi)
    return {(r["tenant"], r["player"]): min(WEEK_DAYS, r["days"])
            for r in rows}


# ── Weekly resolution (lazy, idempotent) ─────────────────────────────────

async def maybe_post_week(conn) -> None:
    """Once per world-week: the world announces the new challenge. The
    ascent_world kv row is the idempotency lock."""
    week = world_week()
    changed = await conn.fetchval(
        "INSERT INTO ascent_world (key, value) VALUES ('challenge_week',$1) "
        "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value "
        "WHERE ascent_world.value <> EXCLUDED.value RETURNING value",
        json.dumps(week))
    if changed is not None:
        kind = week_kind(week)
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'faction',$2)", pstate.world_day(),
            f"This week the Ascent demands a {kind.upper()} — banners "
            f"enter at the Guildhall (◈ {ENTRY_PER_MEMBER} a head, from "
            "the store)")


async def maybe_resolve(conn, faction: str) -> None:
    """Resolve the faction's previous week if it hasn't been yet: collect
    dues from every member (arrears for those who can't pay), then score
    the challenge IF the faction had entered it."""
    week = world_week() - 1
    if week < 0:
        return
    fac = await conn.fetchrow(
        "SELECT name, banner, created_week, join_fee, weekly_dues, treasury "
        "FROM ascent_factions WHERE name=$1 FOR UPDATE", faction)
    if fac is None or fac["created_week"] > week:
        return
    # claim the week exactly once (the faction row lock serializes us)
    row = await conn.fetchrow(
        "SELECT id, entered, resolved, goal_kind, goal_target, entry_paid "
        "FROM ascent_faction_weeks WHERE faction=$1 AND week=$2",
        faction, week)
    if row is not None and row["resolved"]:
        return
    if row is None:
        row = await conn.fetchrow(
            "INSERT INTO ascent_faction_weeks (faction, week, goal_kind,"
            " goal_target, entered, resolved) "
            "VALUES ($1,$2,$3,0,false,true) "
            "ON CONFLICT (faction, week) DO NOTHING "
            "RETURNING id, entered, resolved, goal_kind, goal_target,"
            " entry_paid", faction, week, week_kind(week))
        if row is None:
            return
    else:
        await conn.execute(
            "UPDATE ascent_faction_weeks SET resolved=true WHERE id=$1",
            row["id"])
    members = await members_of(conn, faction)
    await _collect_dues(conn, dict(fac), members, week)
    if row["entered"]:
        await _resolve(conn, dict(fac), members, week, dict(row))
    else:
        await conn.execute(
            "UPDATE ascent_faction_weeks SET prize_note=$2 WHERE id=$1",
            row["id"], "sat the week out — no entry, no prize")


async def _collect_dues(conn, fac: dict, members: list[dict],
                        week: int) -> int:
    """Weekly dues, gold first then bank. Can't pay → arrears: stays at
    the table, skipped from that week's prize split. Clears the first
    week they can pay again. Members who joined after the week owe
    nothing for it."""
    dues, name = int(fac["weekly_dues"]), fac["name"]
    collected = 0
    for m in members:
        if m["joined_day"] >= (week + 1) * WEEK_DAYS:
            continue
        doc = await _load_doc(conn, m["tenant"], m["player"])
        if doc is None:
            continue
        if take_gold(doc, dues):
            await _save_doc(conn, m["tenant"], m["player"], doc)
            collected += dues
            m["arrears"] = False
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " note) VALUES ($1,$2,'faction_dues',$3,$4)",
                m["tenant"], m["player"], -dues, f"{name} · week {week}")
            await store_ledger(conn, name, week, "dues", dues,
                               m["tenant"], m["player"],
                               m.get("name") or m["player"])
        else:
            m["arrears"] = True
        await conn.execute(
            "UPDATE ascent_faction_members SET arrears=$3 "
            "WHERE tenant=$1 AND player=$2",
            m["tenant"], m["player"], m["arrears"])
    if collected:
        await conn.execute(
            "UPDATE ascent_factions SET treasury = treasury + $2 "
            "WHERE name=$1", name, collected)
    return collected


async def _progress(conn, faction: str, kind: str, week: int) -> int:
    lo, hi = week_bounds_ts(week)
    if kind == "cull":
        q = ("SELECT count(*) FROM ascent_ledger l "
             "JOIN ascent_faction_members m ON m.tenant=l.tenant "
             "  AND m.player=l.player AND m.faction=$1 "
             "WHERE l.kind='kill' AND l.created_at >= $2 "
             "  AND l.created_at < $3")
    elif kind == "climb":
        q = ("SELECT coalesce(sum(l.xp),0) FROM ascent_ledger l "
             "JOIN ascent_faction_members m ON m.tenant=l.tenant "
             "  AND m.player=l.player AND m.faction=$1 "
             "WHERE l.xp > 0 AND l.created_at >= $2 AND l.created_at < $3")
    else:  # hoard
        q = ("SELECT coalesce(sum(l.gold),0) FROM ascent_ledger l "
             "JOIN ascent_faction_members m ON m.tenant=l.tenant "
             "  AND m.player=l.player AND m.faction=$1 "
             "WHERE l.gold > 0 AND l.created_at >= $2 "
             "  AND l.created_at < $3")
    return int(await conn.fetchval(q, faction, lo, hi) or 0)


async def _resolve(conn, fac: dict, members: list[dict], week: int,
                   row: dict) -> None:
    """Score an ENTERED week. Members in arrears are skipped from the
    prize (their share stays in the pool for the others)."""
    name, kind, target = fac["name"], row["goal_kind"], int(row["goal_target"])
    eligible = [m for m in members if not m.get("arrears")]
    attend = await week_attendance(conn, name, week)
    required = sum(required_days(m["joined_day"], week) for m in members)
    attended = sum(attend.get((m["tenant"], m["player"]), 0)
                   for m in members)
    mult = attendance_multiplier(attended, required)
    progress = await _progress(conn, name, kind, week)
    reached = progress >= target
    won = bool(reached and mult > 0 and eligible)
    pct = base_pct(len(members))
    note = ""

    if won:
        if kind == "hoard":
            pool = round(pct * target * mult)
            note = await _pay_gold(conn, name, eligible, attend, pool)
        else:
            buff_kind = "hp" if kind == "cull" else "xp"
            buff_pct = round(pct * mult * 100)
            note = await _bless(conn, eligible, buff_kind, buff_pct,
                                week + 1)
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'faction',$2)", pstate.world_day(),
            f"The {name} banner won the week's {kind.upper()} — {note}")
    elif reached:
        note = "goal met, but the hall stood empty — no prize "
        note += f"(attendance {attended}/{required})"
    else:
        note = f"fell short ({progress:,}/{target:,})"
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'faction',$2)", pstate.world_day(),
            f"The {name} banner {note} on the week's {kind.upper()}")

    await conn.execute(
        "UPDATE ascent_faction_weeks SET progress=$2, ratio=$3, "
        "multiplier=$4, prize_note=$5, won=$6 WHERE id=$1",
        row["id"], progress,
        (attended / required) if required else 0.0, mult, note[:200], won)


async def _pay_gold(conn, faction: str, members: list[dict],
                    attend: dict, pool: int) -> str:
    """Split ∝ attendance days. Floor shares + remainder to the best
    attender so the pool pays out exactly — never a coin more."""
    total_days = sum(attend.get((m["tenant"], m["player"]), 0)
                     for m in members) or 1
    shares = {}
    for m in members:
        days = attend.get((m["tenant"], m["player"]), 0)
        shares[(m["tenant"], m["player"])] = pool * days // total_days
    leftover = pool - sum(shares.values())
    if leftover and any(shares.values()):
        best = max(members, key=lambda m: attend.get(
            (m["tenant"], m["player"]), 0))
        shares[(best["tenant"], best["player"])] += leftover
    for m in members:
        share = shares[(m["tenant"], m["player"])]
        if share <= 0:
            continue
        await conn.execute(
            "UPDATE ascent_players SET doc = jsonb_set(doc, '{gold}', "
            "  to_jsonb(coalesce((doc->>'gold')::bigint, 0) + $3)) "
            "WHERE tenant=$1 AND player=$2", m["tenant"], m["player"], share)
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note) "
            "VALUES ($1,$2,'faction_prize',$3,$4)",
            m["tenant"], m["player"], share, f"{faction} weekly hoard")
    return f"◈ {pool:,} split across the table"


async def _bless(conn, members: list[dict], kind: str, pct: int,
                 week: int) -> str:
    buff = {"kind": kind, "pct": pct, "week": week}
    for m in members:
        await conn.execute(
            "UPDATE ascent_players SET doc = jsonb_set(doc, "
            "'{faction_buff}', $3::jsonb) WHERE tenant=$1 AND player=$2",
            m["tenant"], m["player"], json.dumps(buff))
    what = "hardier hides" if kind == "hp" else "sharper minds"
    return f"+{pct}% {what} for the coming week"


# ── Membership mutations (shared by API + engine effects) ───────────────

async def create_faction(conn, tenant: str, player: str, name: str,
                         banner: str, founder_name: str,
                         join_fee: int = 0, weekly_dues: int = 5) -> None:
    """The founder pays no join fee (the ◈500 founding price is their
    buy-in) but pays dues like everyone else. Fee and dues are immutable
    after founding — the social contract stays readable."""
    week = world_week()
    join_fee = max(0, min(JOIN_FEE_MAX, int(join_fee)))
    weekly_dues = max(DUES_MIN, min(DUES_MAX, int(weekly_dues)))
    await conn.execute(
        "INSERT INTO ascent_factions (name, banner, founder_tenant,"
        " founder_player, created_week, join_fee, weekly_dues) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7)",
        name, banner, tenant, player, week, join_fee, weekly_dues)
    await conn.execute(
        "INSERT INTO ascent_faction_members (tenant, player, faction,"
        " role, joined_day) VALUES ($1,$2,$3,'steward',$4)",
        tenant, player, name, pstate.world_day())


async def join_faction(conn, tenant: str, player: str, name: str,
                       doc: dict | None = None) -> str | None:
    """Join = pay the fee (gold then bank) into the store.

    Effect path (doc passed): the engine already charged the doc — this
    only lands the world-side half; a failure refunds the doc, which the
    caller saves. HTTP path (doc=None): load, charge, save here.
    Returns an error string or None."""
    fac = await conn.fetchrow(
        "SELECT name, join_fee FROM ascent_factions WHERE name=$1 "
        "FOR UPDATE", name)
    fee = int(fac["join_fee"]) if fac else 0
    engine_paid = doc is not None

    def refund() -> None:
        if engine_paid and fee:
            doc["gold"] = int(doc.get("gold", 0)) + fee
    if fac is None:
        refund()
        return "that banner no longer flies"
    if await member_row(conn, tenant, player):
        refund()
        return "you already sit at a table — leave it first"
    if not engine_paid:
        doc = await _load_doc(conn, tenant, player)
        if doc is None:
            return "no character"
        if fee and not take_gold(doc, fee):
            return f"the join fee is ◈ {fee} — you can't cover it"
        await _save_doc(conn, tenant, player, doc)
        if fee:
            # engine path audits via doc["_ledger"]; HTTP path does it here
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " note) VALUES ($1,$2,'faction_join',$3,$4)",
                tenant, player, -fee, name)
    if fee:
        await conn.execute(
            "UPDATE ascent_factions SET treasury = treasury + $2 "
            "WHERE name=$1", name, fee)
        await store_ledger(conn, name, world_week(), "join_fee", fee,
                           tenant, player, doc.get("name") or player)
    await conn.execute(
        "INSERT INTO ascent_faction_members (tenant, player, faction,"
        " role, joined_day) VALUES ($1,$2,$3,'member',$4) "
        "ON CONFLICT (tenant, player) DO NOTHING",
        tenant, player, name, pstate.world_day())
    return None


async def donate(conn, tenant: str, player: str, amount: int,
                 doc: dict | None = None,
                 payer_name: str = "") -> str | None:
    """Any member, any time, carried gold only (the bank is the safe
    place — donating is a deliberate act). Effect path (doc passed): the
    engine already charged the doc; failure refunds it. HTTP path
    (doc=None): load, charge, save here."""
    amount = int(amount)
    engine_paid = doc is not None
    me = await member_row(conn, tenant, player)
    if me is None:
        if engine_paid and amount > 0:
            doc["gold"] = int(doc.get("gold", 0)) + amount
        return "you have no banner"
    if amount <= 0:
        return "a donation needs a number above zero"
    if not engine_paid:
        doc = await _load_doc(conn, tenant, player)
        if doc is None:
            return "no character"
        if int(doc.get("gold", 0)) < amount:
            return (f"you carry ◈ {doc.get('gold', 0):,} — "
                    f"not ◈ {amount:,}")
        doc["gold"] = int(doc["gold"]) - amount
        await _save_doc(conn, tenant, player, doc)
        # engine path audits via doc["_ledger"]; HTTP path does it here
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note) "
            "VALUES ($1,$2,'faction_donation',$3,$4)",
            tenant, player, -amount, me["faction"])
    await conn.execute(
        "UPDATE ascent_factions SET treasury = treasury + $2 WHERE name=$1",
        me["faction"], amount)
    await store_ledger(conn, me["faction"], world_week(), "donation",
                       amount, tenant, player,
                       payer_name or (doc or {}).get("name") or player)
    return None


async def enter_week(conn, tenant: str, player: str) -> str | None:
    """Steward enters THIS week's world challenge — ◈5 × members, paid
    from the store; refused with the shortfall shown when it can't."""
    me = await member_row(conn, tenant, player)
    if me is None:
        return "you have no banner"
    if me["role"] != "steward":
        return "only the steward signs the entry"
    name = me["faction"]
    await maybe_resolve(conn, name)
    week = world_week()
    members = await members_of(conn, name)
    cost = entry_cost(len(members))
    treasury = int(await conn.fetchval(
        "SELECT treasury FROM ascent_factions WHERE name=$1 FOR UPDATE",
        name))
    if treasury < cost:
        short = cost - treasury
        return (f"the entry is ◈ {cost} and the store holds ◈ {treasury} "
                f"— ◈ {short} short. Dues land at week's turn, or pass "
                "the hat")
    kind = week_kind(week)
    avg_level = round(sum(m["level"] for m in members)
                      / max(1, len(members)))
    target = suggest_targets(len(members), avg_level)[kind]
    claimed = await conn.fetchrow(
        "INSERT INTO ascent_faction_weeks (faction, week, goal_kind,"
        " goal_target, entered, entry_paid, resolved) "
        "VALUES ($1,$2,$3,$4,true,$5,false) "
        "ON CONFLICT (faction, week) DO NOTHING RETURNING id",
        name, week, kind, target, cost)
    if claimed is None:
        return "your banner is already in this week's lists"
    await conn.execute(
        "UPDATE ascent_factions SET treasury = treasury - $2 WHERE name=$1",
        name, cost)
    await store_ledger(conn, name, week, "entry", -cost, tenant, player,
                       f"{kind} · target {target:,}")
    return None


async def current_week_row(conn, faction: str):
    return await conn.fetchrow(
        "SELECT goal_kind, goal_target, entered, entry_paid, resolved "
        "FROM ascent_faction_weeks WHERE faction=$1 AND week=$2",
        faction, world_week())


# ── The news board (COMMUNITY tab — read-only, any tenant) ───────────────

async def board(conn) -> dict:
    week = world_week()
    last = await conn.fetch(
        "SELECT faction, goal_kind, goal_target, progress, won, prize_note "
        "FROM ascent_faction_weeks WHERE week=$1 AND entered "
        "ORDER BY won DESC, progress DESC LIMIT 8", week - 1)
    wins = await conn.fetch(
        "SELECT faction, count(*) AS wins FROM ascent_faction_weeks "
        "WHERE won GROUP BY faction ORDER BY wins DESC, faction LIMIT 8")
    stats = await conn.fetch(
        "SELECT f.name, f.banner, f.treasury, count(m.player) AS members, "
        "  round(coalesce(avg(coalesce((p.doc->>'level')::int,1)),0)) "
        "    AS avg_level "
        "FROM ascent_factions f "
        "LEFT JOIN ascent_faction_members m ON m.faction=f.name "
        "LEFT JOIN ascent_players p ON p.tenant=m.tenant "
        "  AND p.player=m.player "
        "GROUP BY f.name, f.banner, f.treasury")
    ticker = await conn.fetch(
        "SELECT line FROM ascent_happenings WHERE kind='faction' "
        "ORDER BY id DESC LIMIT 8")
    rows = [dict(r) for r in stats]
    banners = {r["name"]: r["banner"] for r in rows}
    peopled = [r for r in rows if r["members"] > 0]
    return {
        "week": week,
        "challenge": {"kind": week_kind(week),
                      "entry_per_member": ENTRY_PER_MEMBER},
        "last_week": [dict(r) for r in last],
        "wins": [dict(r) for r in wins],
        "most_members": sorted(peopled, key=lambda r: (-r["members"],
                                                       r["name"]))[:5],
        "richest": sorted(rows, key=lambda r: (-r["treasury"],
                                               r["name"]))[:5],
        "highest": sorted(peopled, key=lambda r: (-r["avg_level"],
                                                  r["name"]))[:5],
        "banners": banners,
        "ticker": [r["line"] for r in ticker],
    }


async def leave_faction(conn, tenant: str, player: str) -> None:
    row = await member_row(conn, tenant, player)
    if row is None:
        return
    await conn.execute(
        "DELETE FROM ascent_faction_members WHERE tenant=$1 AND player=$2",
        tenant, player)
    if row["role"] == "steward":
        # promote the oldest remaining member; empty factions dissolve
        heir = await conn.fetchrow(
            "SELECT tenant, player FROM ascent_faction_members "
            "WHERE faction=$1 ORDER BY joined_day, player LIMIT 1",
            row["faction"])
        if heir:
            await conn.execute(
                "UPDATE ascent_faction_members SET role='steward' "
                "WHERE tenant=$1 AND player=$2",
                heir["tenant"], heir["player"])
        else:
            await conn.execute(
                "DELETE FROM ascent_factions WHERE name=$1", row["faction"])


async def sync_doc_guild(conn, tenant: str, player: str, doc: dict) -> None:
    """Membership table is authoritative — the doc's guild string follows
    it (a kicked player sees their colors gone on the next load)."""
    row = await member_row(conn, tenant, player)
    if row is None:
        doc.pop("guild", None)
    else:
        doc["guild"] = row["faction"]
