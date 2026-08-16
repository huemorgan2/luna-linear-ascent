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
FOUND_FEE = 300            # matches the engine's Guildhall fee (019)
FOUND_MIN_LEVEL = 4        # 015: founding is a rank privilege
ONLINE_WINDOW_MIN = 5      # 059: a member is "online" inside this window
                           # (mirrors social.ONLINE_WINDOW_MIN)
GOAL_KINDS = ("hoard", "cull", "climb")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 '\-]{2,23}$")

# ── The faction store (plan 010, third directive) ────────────────────────
JOIN_FEE_MAX = 500         # set at founding, immutable
DUES_MIN, DUES_MAX = 1, 50  # per member per world-week
ENTRY_PER_MEMBER = 5       # the weekly challenge entry, paid from the store

# ── The banner hall (plan 032) — every price and cap in ONE place ────────
# All hall prices are coffer-paid and world-bound (burned): the 010 law
# that no player can ever draw faction gold back out stands untouched.
ROOM_NAMES = {1: "the back room", 2: "a hall of your own",
              3: "the long hall", 4: "the high hall"}
ROOM_PRICES = {2: 500, 3: 2000, 4: 6000}     # tier bought, one at a time
COFFER_CAPS = {1: 200, 2: 600, 3: 2500, 4: 8000}
COFFER_PRICES = {2: 120, 3: 400, 4: 1200}
CHEST_SLOTS = {1: 4, 2: 8, 3: 16, 4: 32}
CHEST_PRICES = {2: 150, 3: 400, 4: 1000}
BED_PRICE = 250
BEDS_BY_ROOM = {1: 0, 2: 2, 3: 6, 4: 10}     # beds fit from room 2 up
NOTE_MAX_CHARS = 64        # one bulletin line, plain text
NOTES_KEPT = 20            # the board shows the last 20, newest first


def tier_to_fit(value: int, caps: dict[int, int]) -> int:
    """The smallest tier whose cap covers `value` — the migration 011
    grandfathering rule (existing balances/racks are never truncated,
    so anything over the top cap still lands on the top tier)."""
    for tier in sorted(caps):
        if value <= caps[tier]:
            return tier
    return max(caps)


def coffer_take(treasury: int, coffer_tier: int, amount: int) -> int:
    """Clip a coffer inflow to the space left under the cap — nothing is
    ever burned out of a member's pocket by a full coffer."""
    cap = COFFER_CAPS.get(int(coffer_tier), COFFER_CAPS[1])
    return max(0, min(int(amount), cap - int(treasury)))

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


# ── 010: the faction color roster — slugs only, the plugin's colors.py
# owns the display names and the hexes. Mirror both when it changes.
COLOR_SLUGS = ["mouse-grey", "rag-silver", "bone-white", "coin-gold",
               "aether-teal", "warden-violet", "ember-red",
               "orchard-green", "root-brown"]
DEFAULT_COLOR = "warden-violet"


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

async def record_attendance(conn, tenant: str, player: str) -> bool:
    """True on the first act of the day (056: the Playing feed's
    'entered the tower' line hangs on this)."""
    got = await conn.fetchval(
        "INSERT INTO ascent_attendance (tenant, player, world_day) "
        "VALUES ($1,$2,$3) ON CONFLICT DO NOTHING RETURNING 1",
        tenant, player, pstate.world_day())
    return got is not None


# ── Membership helpers ───────────────────────────────────────────────────

async def member_row(conn, tenant: str, player: str):
    return await conn.fetchrow(
        "SELECT faction, role, joined_day FROM ascent_faction_members "
        "WHERE tenant=$1 AND player=$2", tenant, player)


async def members_of(conn, faction: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT m.tenant, m.player, m.role, m.joined_day, m.arrears,"
        "       p.doc->>'name' AS name,"
        "       coalesce((p.doc->>'level')::int, 1) AS level,"
        "       p.doc->>'training' AS training,"
        "       p.doc->>'mastery' AS mastery,"
        # 059: online = acted inside the presence window while playing —
        # the same rule as social.online_count, per member
        "       (p.doc->>'stage'='playing' AND p.updated_at >"
        "        now() - make_interval(mins => $2)) AS online "
        "FROM ascent_faction_members m "
        "LEFT JOIN ascent_players p ON p.tenant=m.tenant "
        "  AND p.player=m.player "
        "WHERE m.faction=$1 ORDER BY m.joined_day, m.player",
        faction, ONLINE_WINDOW_MIN)
    out = []
    for r in rows:
        d = dict(r)
        d["online"] = bool(d.get("online"))
        # 048: the trained hands ride the member row — the banner hall
        # toasts its tenth ranks and masters by name
        for k in ("training", "mastery"):
            try:
                d[k] = json.loads(d[k]) if d[k] else {}
            except (TypeError, ValueError):
                d[k] = {}
        out.append(d)
    return out


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
        from . import social
        await social.add_happening(
            conn, kind="faction",
            line=f"This week the Ascent demands a {kind.upper()} — factions "
                 f"enter at the Guildhall (◈ {ENTRY_PER_MEMBER} a head, from "
                 "the coffer)")


async def maybe_resolve(conn, faction: str) -> None:
    """Resolve the faction's previous week if it hasn't been yet: collect
    dues from every member (arrears for those who can't pay), then score
    the challenge IF the faction had entered it."""
    week = world_week() - 1
    if week < 0:
        return
    fac = await conn.fetchrow(
        "SELECT name, banner, created_week, join_fee, weekly_dues, treasury,"
        " coffer_tier FROM ascent_factions WHERE name=$1 FOR UPDATE",
        faction)
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
    nothing for it. 032: every inflow clips to the coffer's cap — dues
    that don't fit are simply not charged (a full coffer is never the
    member's debt, so no arrears either)."""
    dues, name = int(fac["weekly_dues"]), fac["name"]
    room_left = coffer_take(int(fac["treasury"]),
                            int(fac.get("coffer_tier", 1)), 10 ** 9)
    collected = 0
    for m in members:
        if m["joined_day"] >= (week + 1) * WEEK_DAYS:
            continue
        doc = await _load_doc(conn, m["tenant"], m["player"])
        if doc is None:
            continue
        charge = min(dues, room_left - collected)
        if charge <= 0:
            m["arrears"] = False
        elif take_gold(doc, charge):
            await _save_doc(conn, m["tenant"], m["player"], doc)
            collected += charge
            m["arrears"] = False
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " note) VALUES ($1,$2,'faction_dues',$3,$4)",
                m["tenant"], m["player"], -charge, f"{name} · week {week}")
            await store_ledger(conn, name, week, "dues", charge,
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
        from . import social
        await social.add_happening(
            conn, kind="faction", faction=name,
            line=f"The {name} faction won the week's {kind.upper()} — {note}")
    elif reached:
        note = "goal met, but the hall stood empty — no prize "
        note += f"(attendance {attended}/{required})"
    else:
        note = f"fell short ({progress:,}/{target:,})"
        from . import social
        await social.add_happening(
            conn, kind="faction", faction=name,
            line=f"The {name} faction {note} on the week's {kind.upper()}")

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

async def found_faction(conn, tenant: str, player: str, name: str,
                        banner: str, join_fee: int,
                        weekly_dues: int,
                        color: str = "") -> tuple[int, str]:
    """The whole founding transaction — the checks, the fee, the ledger
    line and the row — shared by the v1 API and the pane's desk (061).
    Returns (http_code, error) — (0, "") on success."""
    name = name.strip()
    if not NAME_RE.match(name):
        return 422, "3–24 letters, numbers, spaces, - or '"
    if banner not in banner_slugs():
        return 422, "unknown banner"
    if color and color not in COLOR_SLUGS:
        return 422, "unknown color"
    if not 0 <= int(join_fee) <= JOIN_FEE_MAX:
        return 422, f"the join fee is ◈ 0 to {JOIN_FEE_MAX}"
    if not DUES_MIN <= int(weekly_dues) <= DUES_MAX:
        return 422, f"weekly dues are ◈ {DUES_MIN} to {DUES_MAX}"
    if await member_row(conn, tenant, player):
        return 409, "you already sit at a table — leave it first"
    row = await conn.fetchrow(
        "SELECT doc FROM ascent_players WHERE tenant=$1 AND "
        "player=$2 FOR UPDATE", tenant, player)
    if row is None:
        return 404, "no character"
    doc = json.loads(row["doc"])
    if doc.get("stage") != "playing":
        return 409, "finish character creation first"
    if int(doc.get("level", 1)) < FOUND_MIN_LEVEL:
        return 403, ("the hall charters banners for level "
                     f"{FOUND_MIN_LEVEL}+ climbers")
    if doc.get("gold", 0) < FOUND_FEE:
        return 402, f"founding a banner costs ◈ {FOUND_FEE}"
    taken = await conn.fetchval(
        "SELECT 1 FROM ascent_factions WHERE name=$1", name)
    if taken:
        return 409, "that banner already flies"
    doc["gold"] -= FOUND_FEE
    await conn.execute(
        "UPDATE ascent_players SET doc=$3, updated_at=now() "
        "WHERE tenant=$1 AND player=$2",
        tenant, player, json.dumps(doc))
    await conn.execute(
        "INSERT INTO ascent_ledger (tenant, player, kind, gold, note) "
        "VALUES ($1,$2,'faction_found',$3,$4)",
        tenant, player, -FOUND_FEE, name)
    await create_faction(conn, tenant, player, name, banner,
                         doc.get("name") or player,
                         join_fee=int(join_fee), weekly_dues=int(weekly_dues),
                         color=color)
    return 0, ""


async def create_faction(conn, tenant: str, player: str, name: str,
                         banner: str, founder_name: str,
                         join_fee: int = 0, weekly_dues: int = 5,
                         color: str = "") -> None:
    """The founder pays no join fee (the ◈500 founding price is their
    buy-in) but pays dues like everyone else. Fee and dues are immutable
    after founding — the social contract stays readable."""
    week = world_week()
    join_fee = max(0, min(JOIN_FEE_MAX, int(join_fee)))
    weekly_dues = max(DUES_MIN, min(DUES_MAX, int(weekly_dues)))
    if color not in COLOR_SLUGS:
        color = DEFAULT_COLOR
    await conn.execute(
        "INSERT INTO ascent_factions (name, banner, founder_tenant,"
        " founder_player, created_week, join_fee, weekly_dues, color) "
        "VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
        name, banner, tenant, player, week, join_fee, weekly_dues, color)
    await conn.execute(
        "INSERT INTO ascent_faction_members (tenant, player, faction,"
        " role, joined_day) VALUES ($1,$2,$3,'steward',$4)",
        tenant, player, name, pstate.world_day())


def parse_requirements(raw) -> dict:
    """042: the door rules column — jsonb text or dict, always a dict."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = {}
    return raw if isinstance(raw, dict) else {}


async def _door_gate(conn, fac, tenant: str, player: str,
                     doc: dict | None, via_request: bool) -> str | None:
    """042: why this banner's door refuses the joiner — None when open.
    The server is authoritative; the engine's copy of the same checks
    only shapes the card."""
    req = parse_requirements(fac["requirements"])
    if req.get("invite_only") and not via_request:
        return "that table seats by invitation — ask at their desk"
    cap = int(req.get("member_cap", 0) or 0)
    if cap:
        n = int(await conn.fetchval(
            "SELECT count(*) FROM ascent_faction_members WHERE faction=$1",
            fac["name"]) or 0)
        if n >= cap:
            return "no chair left at that table"
    min_level = int(req.get("min_level", 0) or 0)
    if min_level:
        if doc is None:
            doc = await _load_doc(conn, tenant, player)
        if int((doc or {}).get("level", 1)) < min_level:
            return f"their door reads: level {min_level}+"
    return None


async def join_faction(conn, tenant: str, player: str, name: str,
                       doc: dict | None = None,
                       via_request: bool = False) -> str | None:
    """Join = pay the fee (gold then bank) into the store.

    Effect path (doc passed): the engine already charged the doc — this
    only lands the world-side half; a failure refunds the doc, which the
    caller saves. HTTP path (doc=None): load, charge, save here.
    032: the fee clips to the coffer's cap — the joiner is only ever
    charged what fits (nothing is burned by a full coffer).
    042: the door rules gate here, authoritatively; an admin's approve
    passes via_request=True and walks past invite_only.
    Returns an error string or None."""
    fac = await conn.fetchrow(
        "SELECT name, join_fee, treasury, coffer_tier, requirements "
        "FROM ascent_factions WHERE name=$1 FOR UPDATE", name)
    fee = int(fac["join_fee"]) if fac else 0
    take = (coffer_take(fac["treasury"], fac["coffer_tier"], fee)
            if fac else 0)
    engine_paid = doc is not None

    def refund(n: int) -> None:
        if engine_paid and n > 0:
            doc["gold"] = int(doc.get("gold", 0)) + n
    if fac is None:
        refund(fee)
        return "that faction no longer flies"
    if await member_row(conn, tenant, player):
        refund(fee)
        return "you already sit at a table — leave it first"
    gate = await _door_gate(conn, fac, tenant, player, doc, via_request)
    if gate:
        refund(fee)
        return gate
    if engine_paid and take < fee:
        # the engine charged the posted fee; the brim hands the rest back
        refund(fee - take)
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note)"
            " VALUES ($1,$2,'faction_join',$3,$4)",
            tenant, player, fee - take,
            f"{name} — the coffer was full, part returned")
    if not engine_paid:
        doc = await _load_doc(conn, tenant, player)
        if doc is None:
            return "no character"
        if fee and int(doc.get("gold", 0)) + int(doc.get("bank", 0)) < fee:
            return f"the join fee is ◈ {fee} — you can't cover it"
        if take:
            take_gold(doc, take)
        await _save_doc(conn, tenant, player, doc)
        if take:
            # engine path audits via doc["_ledger"]; HTTP path does it here
            await conn.execute(
                "INSERT INTO ascent_ledger (tenant, player, kind, gold,"
                " note) VALUES ($1,$2,'faction_join',$3,$4)",
                tenant, player, -take, name)
    if take:
        await conn.execute(
            "UPDATE ascent_factions SET treasury = treasury + $2 "
            "WHERE name=$1", name, take)
        await store_ledger(conn, name, world_week(), "join_fee", take,
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
    (doc=None): load, charge, save here. 032: the donation clips to the
    coffer's cap — only what fits leaves the donor's pocket."""
    amount = int(amount)
    engine_paid = doc is not None
    me = await member_row(conn, tenant, player)

    def refund(n: int) -> None:
        if engine_paid and n > 0:
            doc["gold"] = int(doc.get("gold", 0)) + n
    if me is None:
        refund(amount)
        return "you have no faction"
    if amount <= 0:
        return "a donation needs a number above zero"
    fac = await conn.fetchrow(
        "SELECT treasury, coffer_tier FROM ascent_factions WHERE name=$1 "
        "FOR UPDATE", me["faction"])
    if fac is None:
        refund(amount)
        return "that faction no longer flies"
    take = coffer_take(fac["treasury"], fac["coffer_tier"], amount)
    if take <= 0:
        refund(amount)
        cap = COFFER_CAPS.get(int(fac["coffer_tier"]), COFFER_CAPS[1])
        return f"the coffer is full — ◈ {cap:,} is its brim"
    if not engine_paid:
        doc = await _load_doc(conn, tenant, player)
        if doc is None:
            return "no character"
        if int(doc.get("gold", 0)) < amount:
            return (f"you carry ◈ {doc.get('gold', 0):,} — "
                    f"not ◈ {amount:,}")
        doc["gold"] = int(doc["gold"]) - take
        await _save_doc(conn, tenant, player, doc)
        # engine path audits via doc["_ledger"]; HTTP path does it here
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note) "
            "VALUES ($1,$2,'faction_donation',$3,$4)",
            tenant, player, -take, me["faction"])
    elif take < amount:
        # the engine charged the full ask; the brim hands the rest back
        refund(amount - take)
        await conn.execute(
            "INSERT INTO ascent_ledger (tenant, player, kind, gold, note) "
            "VALUES ($1,$2,'faction_donation',$3,$4)",
            tenant, player, amount - take,
            f"{me['faction']} — the coffer took ◈ {take:,}, rest returned")
    await conn.execute(
        "UPDATE ascent_factions SET treasury = treasury + $2 WHERE name=$1",
        me["faction"], take)
    await store_ledger(conn, me["faction"], world_week(), "donation",
                       take, tenant, player,
                       payer_name or (doc or {}).get("name") or player)
    return None


async def enter_week(conn, tenant: str, player: str) -> str | None:
    """Steward enters THIS week's world challenge — ◈5 × members, paid
    from the store; refused with the shortfall shown when it can't."""
    me = await member_row(conn, tenant, player)
    if me is None:
        return "you have no faction"
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
        return (f"the entry is ◈ {cost} and the coffer holds ◈ {treasury} "
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
        return "your faction is already in this week's lists"
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


# ── The banner hall (plan 032) — the works, the bunks, the board ─────────
# Buying up is a steward action, paid from the coffer, one tier at a
# time, never automatic, never downgraded. Every purchase is burned out
# of the world (ledger kinds works_*) — nobody pockets the coffer.

async def _works_faction(conn, tenant: str,
                         player: str) -> tuple[dict | None, str | None]:
    """Steward gate + the locked faction row a works purchase needs."""
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return None, "only the steward orders the works"
    fac = await conn.fetchrow(
        "SELECT name, room_tier, coffer_tier, chest_tier, beds, treasury "
        "FROM ascent_factions WHERE name=$1 FOR UPDATE", faction)
    if fac is None:
        return None, "that faction no longer flies"
    return dict(fac), None


async def _pay_works(conn, fac: dict, tenant: str, player: str,
                     price: int, kind: str, note: str) -> str | None:
    treasury = int(fac["treasury"])
    if treasury < price:
        short = price - treasury
        return (f"the works want ◈ {price:,} and the coffer holds "
                f"◈ {treasury:,} — ◈ {short:,} short")
    await conn.execute(
        "UPDATE ascent_factions SET treasury = treasury - $2 WHERE name=$1",
        fac["name"], price)
    await store_ledger(conn, fac["name"], world_week(), kind, -price,
                       tenant, player, note)
    return None


async def buy_room(conn, tenant: str, player: str,
                   tier: int | None = None) -> str | None:
    """Steward buys the hall up one room tier, from the coffer."""
    fac, err = await _works_faction(conn, tenant, player)
    if err:
        return err
    nxt = int(fac["room_tier"]) + 1
    if tier is not None and int(tier) != nxt:
        return "one tier at a time — the hall is built, not conjured"
    if nxt not in ROOM_PRICES:
        return "the high hall is already yours — nothing grander is sold"
    err = await _pay_works(conn, fac, tenant, player, ROOM_PRICES[nxt],
                           "works_room", ROOM_NAMES[nxt])
    if err:
        return err
    await conn.execute(
        "UPDATE ascent_factions SET room_tier=$2 WHERE name=$1",
        fac["name"], nxt)
    return None


async def buy_coffer(conn, tenant: str, player: str,
                     tier: int | None = None) -> str | None:
    fac, err = await _works_faction(conn, tenant, player)
    if err:
        return err
    nxt = int(fac["coffer_tier"]) + 1
    if tier is not None and int(tier) != nxt:
        return "one tier at a time — the hall is built, not conjured"
    if nxt not in COFFER_PRICES:
        return "the coffer is as deep as they are made"
    err = await _pay_works(conn, fac, tenant, player, COFFER_PRICES[nxt],
                           "works_coffer",
                           f"a deeper coffer — holds ◈ {COFFER_CAPS[nxt]:,}")
    if err:
        return err
    await conn.execute(
        "UPDATE ascent_factions SET coffer_tier=$2 WHERE name=$1",
        fac["name"], nxt)
    return None


async def buy_chest(conn, tenant: str, player: str,
                    tier: int | None = None) -> str | None:
    fac, err = await _works_faction(conn, tenant, player)
    if err:
        return err
    nxt = int(fac["chest_tier"]) + 1
    if tier is not None and int(tier) != nxt:
        return "one tier at a time — the hall is built, not conjured"
    if nxt not in CHEST_PRICES:
        return "the chest is as big as they are made"
    err = await _pay_works(conn, fac, tenant, player, CHEST_PRICES[nxt],
                           "works_chest",
                           f"a bigger chest — {CHEST_SLOTS[nxt]} slots")
    if err:
        return err
    await conn.execute(
        "UPDATE ascent_factions SET chest_tier=$2 WHERE name=$1",
        fac["name"], nxt)
    return None


async def buy_bed(conn, tenant: str, player: str) -> str | None:
    """Steward buys one bed, ◈250 from the coffer, capped by room tier."""
    fac, err = await _works_faction(conn, tenant, player)
    if err:
        return err
    room, beds = int(fac["room_tier"]), int(fac["beds"])
    cap = BEDS_BY_ROOM.get(room, 0)
    if beds >= cap:
        if cap == 0:
            return "the back room fits no beds — buy up the hall first"
        return (f"{ROOM_NAMES[room]} fits {cap} beds — "
                "buy up the hall for more")
    err = await _pay_works(conn, fac, tenant, player, BED_PRICE,
                           "works_bed", f"bed {beds + 1} for the bunks")
    if err:
        return err
    await conn.execute(
        "UPDATE ascent_factions SET beds = beds + 1 WHERE name=$1",
        fac["name"])
    return None


async def claim_bed(conn, tenant: str, player: str,
                    doc: dict) -> str | None:
    """Any member, free, while claims remain — first come, first bunked.
    A claim sets the SAME lodged_until_day flag the Lodge sells, so PvP
    target selection honors it untouched. Safety only: no night job, no
    rested-XP — dawn heals everyone regardless."""
    me = await member_row(conn, tenant, player)
    if me is None:
        return "you have no faction"
    beds = int(await conn.fetchval(
        "SELECT beds FROM ascent_factions WHERE name=$1 FOR UPDATE",
        me["faction"]) or 0)
    if beds <= 0:
        return "no bunks stand in your hall yet"
    day = pstate.world_day()
    mine = await conn.fetchval(
        "SELECT 1 FROM ascent_faction_bed_claims "
        "WHERE tenant=$1 AND player=$2 AND world_day=$3",
        tenant, player, day)
    if mine:
        return "you already have a bunk tonight"
    claimed = int(await conn.fetchval(
        "SELECT count(*) FROM ascent_faction_bed_claims "
        "WHERE faction=$1 AND world_day=$2", me["faction"], day) or 0)
    if claimed >= beds:
        return "every bunk is claimed tonight — first come, first bunked"
    row = await conn.fetchrow(
        "INSERT INTO ascent_faction_bed_claims (tenant, player, faction,"
        " world_day) VALUES ($1,$2,$3,$4) "
        "ON CONFLICT DO NOTHING RETURNING world_day",
        tenant, player, me["faction"], day)
    if row is None:
        return "you already have a bunk tonight"
    doc["lodged_until_day"] = day + 1     # the Lodge's flag, set free
    return None


async def write_note(conn, tenant: str, player: str,
                     line: str) -> str | None:
    """One line on the bulletin board, any member, free. One note per
    member per world-day — writing again the same day replaces it."""
    me = await member_row(conn, tenant, player)
    if me is None:
        return "you have no faction"
    line = " ".join(str(line).split())[:NOTE_MAX_CHARS]
    if not line:
        return "the board takes one line — write something first"
    await conn.execute(
        "INSERT INTO ascent_faction_notes (faction, tenant, player,"
        " world_day, line) VALUES ($1,$2,$3,$4,$5) "
        "ON CONFLICT (faction, tenant, player, world_day) "
        "DO UPDATE SET line=EXCLUDED.line, created_at=now()",
        me["faction"], tenant, player, pstate.world_day(), line)
    return None


async def hall_state(conn, faction: str) -> dict | None:
    """The hall as one payload: room, coffer, chest, bunks, the board,
    and the works rows a steward can buy. Rides the scene injection
    (social._faction_panel) and /v1/faction/detail."""
    fac = await conn.fetchrow(
        "SELECT room_tier, coffer_tier, chest_tier, beds, treasury "
        "FROM ascent_factions WHERE name=$1", faction)
    if fac is None:
        return None
    day = pstate.world_day()
    used = int(await conn.fetchval(
        "SELECT count(*) FROM ascent_armory WHERE faction=$1",
        faction) or 0)
    tonight = await conn.fetch(
        "SELECT coalesce(p.doc->>'name', c.player) AS name "
        "FROM ascent_faction_bed_claims c "
        "LEFT JOIN ascent_players p ON p.tenant=c.tenant "
        "  AND p.player=c.player "
        "WHERE c.faction=$1 AND c.world_day=$2 ORDER BY name",
        faction, day)
    notes = await conn.fetch(
        "SELECT n.world_day, coalesce(p.doc->>'name', n.player) AS player,"
        " n.line FROM ascent_faction_notes n "
        "LEFT JOIN ascent_players p ON p.tenant=n.tenant "
        "  AND p.player=n.player "
        "WHERE n.faction=$1 ORDER BY n.id DESC LIMIT $2",
        faction, NOTES_KEPT)
    room, coffer, chest = (int(fac["room_tier"]), int(fac["coffer_tier"]),
                           int(fac["chest_tier"]))
    treasury, beds = int(fac["treasury"]), int(fac["beds"])
    works = []
    if room + 1 in ROOM_PRICES:
        price = ROOM_PRICES[room + 1]
        works.append({"kind": "room", "tier": room + 1, "price": price,
                      "label": f"buy up the hall — {ROOM_NAMES[room + 1]}",
                      "affordable": treasury >= price})
    if coffer + 1 in COFFER_PRICES:
        price = COFFER_PRICES[coffer + 1]
        works.append({
            "kind": "coffer", "tier": coffer + 1, "price": price,
            "label": f"a deeper coffer — holds ◈ {COFFER_CAPS[coffer + 1]:,}",
            "affordable": treasury >= price})
    if chest + 1 in CHEST_PRICES:
        price = CHEST_PRICES[chest + 1]
        works.append({
            "kind": "chest", "tier": chest + 1, "price": price,
            "label": f"a bigger chest — {CHEST_SLOTS[chest + 1]} slots",
            "affordable": treasury >= price})
    if beds < BEDS_BY_ROOM.get(room, 0):
        works.append({
            "kind": "bed", "tier": beds + 1, "price": BED_PRICE,
            "label": (f"a bed for the bunks — "
                      f"{beds + 1} of {BEDS_BY_ROOM[room]}"),
            "affordable": treasury >= BED_PRICE})
    return {
        "room_tier": room, "room_name": ROOM_NAMES.get(room, "?"),
        "coffer": {"bal": treasury,
                   "cap": COFFER_CAPS.get(coffer, COFFER_CAPS[1]),
                   "tier": coffer},
        "chest": {"used": used,
                  "cap": CHEST_SLOTS.get(chest, CHEST_SLOTS[1]),
                  "tier": chest},
        "beds": {"count": beds, "tonight": [r["name"] for r in tonight]},
        "notes": [{"day": int(r["world_day"]), "player": r["player"],
                   "line": r["line"]} for r in notes],
        "works": works,
    }


async def week_standings(conn, week: int | None = None) -> list[dict]:
    """Entered banners this week with live progress, best first — the
    Guildhall's standings wall (032 §3)."""
    week = world_week() if week is None else week
    rows = await conn.fetch(
        "SELECT w.faction, f.banner, w.goal_kind, w.goal_target "
        "FROM ascent_faction_weeks w "
        "JOIN ascent_factions f ON f.name=w.faction "
        "WHERE w.week=$1 AND w.entered ORDER BY w.faction", week)
    out = []
    for r in rows:
        progress = await _progress(conn, r["faction"], r["goal_kind"], week)
        out.append({"name": r["faction"], "banner": r["banner"],
                    "progress": progress,
                    "target": int(r["goal_target"])})
    out.sort(key=lambda s: (-(s["progress"] / max(1, s["target"])),
                            s["name"]))
    return out


async def banner_scores(conn) -> list[dict]:
    """Every banner with its all-time score line — wins, members, room
    tier — sorted by wins (the hall-of-banners tiles)."""
    rows = await conn.fetch(
        "SELECT f.name, f.banner, f.room_tier,"
        "  count(m.player) AS members, coalesce(w.wins, 0) AS wins "
        "FROM ascent_factions f "
        "LEFT JOIN ascent_faction_members m ON m.faction=f.name "
        "LEFT JOIN (SELECT faction, count(*) AS wins "
        "           FROM ascent_faction_weeks WHERE won "
        "           GROUP BY faction) w ON w.faction=f.name "
        "GROUP BY f.name, f.banner, f.room_tier, w.wins "
        "ORDER BY wins DESC, f.name")
    return [{"name": r["name"], "banner": r["banner"],
             "wins": int(r["wins"]), "members": int(r["members"]),
             "room_tier": int(r["room_tier"])} for r in rows]


async def hall_board(conn) -> dict:
    """The trimmed board every scene injection carries — this week's
    standings and the hall of banners (032 §3)."""
    week = world_week()
    return {"week": week, "kind": week_kind(week),
            "standings": await week_standings(conn, week),
            "banners": await banner_scores(conn)}


# ── The news board (COMMUNITY tab — read-only, any tenant) ───────────────

async def board(conn) -> dict:
    week = world_week()
    last = await conn.fetch(
        "SELECT faction, goal_kind, goal_target, progress, won, prize_note "
        "FROM ascent_faction_weeks WHERE week=$1 AND entered "
        "ORDER BY won DESC, progress DESC LIMIT 8", week - 1)
    # 032: the wins column is the hall-of-banners score line — shared
    # with the scene injection's hall_board, computed once
    scores = await banner_scores(conn)
    wins = [{"faction": s["name"], "wins": s["wins"]}
            for s in scores if s["wins"]][:8]
    stats = await conn.fetch(
        "SELECT f.name, f.banner, f.treasury, f.room_tier, "
        "  count(m.player) AS members, "
        "  round(coalesce(avg(coalesce((p.doc->>'level')::int,1)),0)) "
        "    AS avg_level "
        "FROM ascent_factions f "
        "LEFT JOIN ascent_faction_members m ON m.faction=f.name "
        "LEFT JOIN ascent_players p ON p.tenant=m.tenant "
        "  AND p.player=m.player "
        "GROUP BY f.name, f.banner, f.treasury, f.room_tier")
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
        "wins": wins,
        "most_members": sorted(peopled, key=lambda r: (-r["members"],
                                                       r["name"]))[:5],
        "richest": sorted(rows, key=lambda r: (-r["treasury"],
                                               r["name"]))[:5],
        "highest": sorted(peopled, key=lambda r: (-r["avg_level"],
                                                  r["name"]))[:5],
        "banners": banners,
        "ticker": [r["line"] for r in ticker],
    }


# ── The faction desk (plan 015) ──────────────────────────────────────────
# Joining is a REQUEST an admin (any steward) accepts or rejects. The fee
# is charged at accept. Admins can rename the banner and promote members;
# the founder is a permanent badge, not a role.

async def is_admin(conn, tenant: str, player: str) -> str | None:
    """The caller's faction name if they hold the steward role, else None."""
    me = await member_row(conn, tenant, player)
    if me is None or me["role"] != "steward":
        return None
    return me["faction"]


async def request_join(conn, tenant: str, player: str,
                       name: str) -> str | None:
    if await member_row(conn, tenant, player):
        return "you already sit at a table — leave it first"
    fac = await conn.fetchrow(
        "SELECT name, requirements FROM ascent_factions WHERE name=$1",
        name)
    if fac is None:
        return "that faction no longer flies"
    doc = await _load_doc(conn, tenant, player)
    if doc is None or doc.get("stage") != "playing":
        return "no character"
    # 042: a request under the level bar would only rot at the desk
    req = parse_requirements(fac["requirements"])
    min_level = int(req.get("min_level", 0) or 0)
    if min_level and int(doc.get("level", 1)) < min_level:
        return f"their door reads: level {min_level}+"
    # one open request per player — asking elsewhere moves the request
    await conn.execute(
        "INSERT INTO ascent_faction_requests (tenant, player, faction,"
        " requested_day) VALUES ($1,$2,$3,$4) "
        "ON CONFLICT (tenant, player) DO UPDATE "
        "SET faction=EXCLUDED.faction, requested_day=EXCLUDED.requested_day,"
        " created_at=now()",
        tenant, player, name, pstate.world_day())
    return None


async def cancel_request(conn, tenant: str, player: str) -> None:
    await conn.execute(
        "DELETE FROM ascent_faction_requests WHERE tenant=$1 AND player=$2",
        tenant, player)


async def my_request(conn, tenant: str, player: str) -> str | None:
    return await conn.fetchval(
        "SELECT faction FROM ascent_faction_requests "
        "WHERE tenant=$1 AND player=$2", tenant, player)


async def pending_requests(conn, faction: str) -> list[dict]:
    rows = await conn.fetch(
        "SELECT r.tenant, r.player, r.requested_day,"
        "       p.doc->>'name' AS name,"
        "       coalesce((p.doc->>'level')::int, 1) AS level "
        "FROM ascent_faction_requests r "
        "LEFT JOIN ascent_players p ON p.tenant=r.tenant "
        "  AND p.player=r.player "
        "WHERE r.faction=$1 ORDER BY r.created_at", faction)
    return [dict(r) for r in rows]


async def approve_request(conn, tenant: str, player: str,
                          target_tenant: str,
                          target_player: str) -> str | None:
    """Accept a join request: charge the fee, seat the member. If the
    requester can't cover the fee the request STAYS (they can top up)."""
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return "only an admin works the desk"
    req = await conn.fetchrow(
        "SELECT faction FROM ascent_faction_requests "
        "WHERE tenant=$1 AND player=$2 AND faction=$3 FOR UPDATE",
        target_tenant, target_player, faction)
    if req is None:
        return "no such request at your desk"
    err = await join_faction(conn, target_tenant, target_player, faction,
                             via_request=True)
    if err:
        return err
    await conn.execute(
        "DELETE FROM ascent_faction_requests WHERE tenant=$1 AND player=$2",
        target_tenant, target_player)
    return None


async def reject_request(conn, tenant: str, player: str,
                         target_tenant: str,
                         target_player: str) -> str | None:
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return "only an admin works the desk"
    gone = await conn.execute(
        "DELETE FROM ascent_faction_requests "
        "WHERE tenant=$1 AND player=$2 AND faction=$3",
        target_tenant, target_player, faction)
    return None if gone.endswith("1") else "no such request at your desk"


async def rename_faction(conn, tenant: str, player: str,
                         new_name: str) -> str | None:
    """Admin renames the banner. Members/requests follow by FK cascade;
    weeks and the store ledger are plain text and move here, so wins and
    audit history stay attached."""
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return "only an admin renames the faction"
    new_name = new_name.strip()
    if not NAME_RE.match(new_name):
        return "3–24 letters, numbers, spaces, - or '"
    if new_name == faction:
        return None
    taken = await conn.fetchval(
        "SELECT 1 FROM ascent_factions WHERE name=$1", new_name)
    if taken:
        return "that faction already flies"
    await conn.execute(
        "UPDATE ascent_factions SET name=$2 WHERE name=$1",
        faction, new_name)
    await conn.execute(
        "UPDATE ascent_faction_weeks SET faction=$2 WHERE faction=$1",
        faction, new_name)
    await conn.execute(
        "UPDATE ascent_faction_ledger SET faction=$2 WHERE faction=$1",
        faction, new_name)
    from . import social
    await social.add_happening(
        conn, kind="faction", faction=new_name,
        line=f"The {faction} banner flies new colors — it is {new_name} now")
    return None


async def recolor_faction(conn, tenant: str, player: str,
                          color: str) -> str | None:
    """010: admin picks a new ink for the banner — one of the 9 named
    roster slugs. Every member's card strip follows on the next scene."""
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return "only an admin changes the colors"
    if color not in COLOR_SLUGS:
        return "unknown color"
    await conn.execute(
        "UPDATE ascent_factions SET color=$2 WHERE name=$1",
        faction, color)
    from . import social
    pretty = color.replace("-", " ")
    await social.add_happening(
        conn, kind="faction", faction=faction,
        line=f"The {faction} banner flies {pretty} now")
    return None


async def promote_member(conn, tenant: str, player: str,
                         target_tenant: str,
                         target_player: str) -> str | None:
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return "only an admin promotes"
    target = await member_row(conn, target_tenant, target_player)
    if target is None or target["faction"] != faction:
        return "not at your table"
    if target["role"] == "steward":
        return "already an admin"
    await conn.execute(
        "UPDATE ascent_faction_members SET role='steward' "
        "WHERE tenant=$1 AND player=$2", target_tenant, target_player)
    return None


async def faction_detail(conn, tenant: str, player: str,
                         name: str) -> dict | None:
    """The faction page: public roster + stats; the viewer's own flags;
    the request queue when the viewer is an admin of this faction."""
    fac = await conn.fetchrow(
        "SELECT name, banner, founder_tenant, founder_player, join_fee,"
        " weekly_dues, treasury, created_week FROM ascent_factions "
        "WHERE name=$1", name)
    if fac is None:
        return None
    members = await members_of(conn, name)
    week = world_week()
    attend = await week_attendance(conn, name, week)
    founder_key = (fac["founder_tenant"], fac["founder_player"])
    founder_name = ""
    out_members = []
    for m in members:
        is_founder = (m["tenant"], m["player"]) == founder_key
        if is_founder:
            founder_name = m["name"] or m["player"]
        out_members.append({
            "tenant": m["tenant"], "player": m["player"],
            "name": m["name"] or m["player"], "level": m["level"],
            "role": m["role"], "founder": is_founder,
            "you": (m["tenant"], m["player"]) == (tenant, player),
            "arrears": bool(m["arrears"]),
            "days": attend.get((m["tenant"], m["player"]), 0),
            "training": m.get("training") or {},
            "mastery": m.get("mastery") or {},
        })
    if not founder_name:
        # founder may have left the table — the mark on the page remains
        row = await conn.fetchrow(
            "SELECT doc->>'name' AS name FROM ascent_players "
            "WHERE tenant=$1 AND player=$2", *founder_key)
        founder_name = (row and row["name"]) or fac["founder_player"] or "?"
    wins = int(await conn.fetchval(
        "SELECT count(*) FROM ascent_faction_weeks WHERE faction=$1 "
        "AND won", name) or 0)
    wrow = await current_week_row(conn, name)
    me = await member_row(conn, tenant, player)
    viewer_role = (me["role"] if me and me["faction"] == name else "")
    is_admin_here = viewer_role == "steward"
    kind = week_kind(week)
    d = {
        "name": fac["name"], "banner": fac["banner"],
        "founder": founder_name,
        "founder_key": {"tenant": founder_key[0], "player": founder_key[1]},
        "join_fee": int(fac["join_fee"]), "dues": int(fac["weekly_dues"]),
        "store": int(fac["treasury"]), "wins": wins,
        "members": out_members,
        "week": {
            "kind": kind,
            "entered": bool(wrow and wrow["entered"]),
            "entry_cost": entry_cost(len(members)),
            "target": int(wrow["goal_target"]) if wrow else 0,
        },
        "viewer": {
            "member": bool(me and me["faction"] == name),
            "in_faction": bool(me),
            "admin": is_admin_here,
            "founder": (tenant, player) == founder_key,
            "requested": (await my_request(conn, tenant, player)) == name,
        },
    }
    # 032: the hall on the faction page — members get the whole house,
    # outsiders see the room tier and nothing private
    hall = await hall_state(conn, name)
    if hall:
        d["room_tier"] = hall["room_tier"]
        d["room_name"] = hall["room_name"]
        d["hall"] = (hall if d["viewer"]["member"] else
                     {"room_tier": hall["room_tier"],
                      "room_name": hall["room_name"]})
    if is_admin_here:
        d["requests"] = await pending_requests(conn, name)
    return d


async def search_factions(conn, q: str = "", limit: int = 10,
                          offset: int = 0) -> list[dict]:
    """Top banners by table size; q narrows by name (server-side)."""
    rows = await conn.fetch(
        "SELECT f.name, f.banner, f.join_fee, f.weekly_dues, f.treasury, "
        "f.requirements, count(m.player) AS members FROM ascent_factions f "
        "LEFT JOIN ascent_faction_members m ON m.faction=f.name "
        "WHERE ($1 = '' OR f.name ILIKE '%' || $1 || '%') "
        "GROUP BY f.name, f.banner, f.join_fee, f.weekly_dues, f.treasury,"
        " f.requirements "
        "ORDER BY members DESC, f.name LIMIT $2 OFFSET $3",
        q.strip()[:24], limit, max(0, int(offset)))
    out = []
    for r in rows:
        d = dict(r)
        d["requirements"] = parse_requirements(d["requirements"])
        out.append(d)
    return out


DIRECTORY_CAP = 100        # 042: the wall shows at most 100 banners


async def directory(conn) -> dict:
    """042: the Guild Hall wall — every banner joinable on the spot,
    biggest tables first, capped at 100 rows. {rows, total}."""
    total = int(await conn.fetchval(
        "SELECT count(*) FROM ascent_factions") or 0)
    rows = await search_factions(conn, "", limit=DIRECTORY_CAP)
    return {"rows": rows, "total": total}


async def set_requirements(conn, tenant: str, player: str,
                           min_level: int, invite_only: bool) -> str | None:
    """042: a steward writes the door rules. Anyone else is a no-op."""
    faction = await is_admin(conn, tenant, player)
    if faction is None:
        return "only the steward writes the door"
    req = {}
    if int(min_level) > 0:
        req["min_level"] = max(0, min(30, int(min_level)))
    if invite_only:
        req["invite_only"] = True
    await conn.execute(
        "UPDATE ascent_factions SET requirements=$2::jsonb WHERE name=$1",
        faction, json.dumps(req))
    return None


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


# ── Shared desk bodies (005: /v1/* and /play/api/* call the same code) ───

def desk_code(err: str) -> int:
    """HTTP code for a desk refusal — one mapping for both auth flavors."""
    if "not at your table" in err:
        return 404
    if "kick yourself" in err:
        return 422
    if "only" in err:
        return 403
    return 409


async def kick_member(conn, tenant: str, player: str, target_tenant: str,
                      target_player: str) -> str | None:
    me = await member_row(conn, tenant, player)
    if me is None or me["role"] != "steward":
        return "only the steward removes members"
    target = await member_row(conn, target_tenant, target_player)
    if target is None or target["faction"] != me["faction"]:
        return "not at your table"
    if (target_tenant, target_player) == (tenant, player):
        return "leave, don't kick yourself"
    if target["role"] == "steward":
        # 015: admins don't kick admins — the founder can
        founder = await conn.fetchrow(
            "SELECT founder_tenant, founder_player "
            "FROM ascent_factions WHERE name=$1", me["faction"])
        if (founder["founder_tenant"],
                founder["founder_player"]) != (tenant, player):
            return "only the founder unseats an admin"
    await conn.execute(
        "DELETE FROM ascent_faction_members "
        "WHERE tenant=$1 AND player=$2",
        target_tenant, target_player)
    return None


# ── Shared read bodies (005: /v1/* and /play/api/* call the same code) ───

async def settled_board(conn) -> dict:
    """The COMMUNITY news board — read-only, any caller. Resolves any
    pending weeks first so 'last week' is always settled."""
    names = await conn.fetch("SELECT name FROM ascent_factions")
    for r in names:
        await maybe_resolve(conn, r["name"])
    await maybe_post_week(conn)
    return await board(conn)


BROWSE_LIMIT = 50          # 059: the ledger IS the "all factions" page


async def browse(conn, tenant: str, player: str, q: str) -> dict:
    """The ledger: top factions by table size (50); q searches
    server-side. Includes the caller's open request so the UI shows the
    pending state."""
    rows = await search_factions(conn, q, limit=BROWSE_LIMIT)
    total = int(await conn.fetchval(
        "SELECT count(*) FROM ascent_factions") or 0)
    requested = await my_request(conn, tenant, player)
    # 019: the board's call-to-action needs to know the viewer sits
    # at no table (members get no join buttons, no pitch)
    mine = await member_row(conn, tenant, player)
    return {"factions": rows,
            "total": total,
            "requested": requested or "",
            "in_faction": (mine or {}).get("faction") or "",
            "banners": banner_slugs(),
            "found_fee": FOUND_FEE,
            "found_min_level": FOUND_MIN_LEVEL}


async def sync_doc_guild(conn, tenant: str, player: str, doc: dict) -> None:
    """Membership table is authoritative — the doc's guild string follows
    it (a kicked player sees their colors gone on the next load)."""
    row = await member_row(conn, tenant, player)
    if row is None:
        doc.pop("guild", None)
    else:
        doc["guild"] = row["faction"]
