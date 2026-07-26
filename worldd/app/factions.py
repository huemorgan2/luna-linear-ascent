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
    """Steward menu material — fair targets scaled to the crew."""
    m, lv = max(1, members), max(1, avg_level)
    return {
        "hoard": 300 * lv * m,     # ≈ a solid 4-day hunting week of gold
        "cull": 50 * m,            # kills
        "climb": 200 * lv * m,     # xp
    }


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
        "SELECT m.tenant, m.player, m.role, m.joined_day,"
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

async def maybe_resolve(conn, faction: str) -> None:
    """Resolve the faction's previous week if it hasn't been yet."""
    week = world_week() - 1
    if week < 0:
        return
    row = await conn.fetchrow(
        "SELECT name, banner, created_week, goal_kind, goal_target "
        "FROM ascent_factions WHERE name=$1 FOR UPDATE", faction)
    if row is None or row["created_week"] > week or not row["goal_target"]:
        return
    claimed = await conn.fetchrow(
        "INSERT INTO ascent_faction_weeks (faction, week, goal_kind,"
        " goal_target) VALUES ($1,$2,$3,$4) "
        "ON CONFLICT (faction, week) DO NOTHING RETURNING id",
        faction, week, row["goal_kind"], row["goal_target"])
    if claimed is None:
        return                          # already resolved
    await _resolve(conn, dict(row), week, claimed["id"])


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


async def _resolve(conn, fac: dict, week: int, row_id: int) -> None:
    name, kind, target = fac["name"], fac["goal_kind"], int(fac["goal_target"])
    members = await members_of(conn, name)
    attend = await week_attendance(conn, name, week)
    required = sum(required_days(m["joined_day"], week) for m in members)
    attended = sum(attend.get((m["tenant"], m["player"]), 0)
                   for m in members)
    mult = attendance_multiplier(attended, required)
    progress = await _progress(conn, name, kind, week)
    reached = progress >= target
    pct = base_pct(len(members))
    note = ""

    if reached and mult > 0 and members:
        if kind == "hoard":
            pool = round(pct * target * mult)
            note = await _pay_gold(conn, name, members, attend, pool)
        else:
            buff_kind = "hp" if kind == "cull" else "xp"
            buff_pct = round(pct * mult * 100)
            note = await _bless(conn, members, buff_kind, buff_pct, week + 1)
        await conn.execute(
            "INSERT INTO ascent_happenings (world_day, kind, line) "
            "VALUES ($1,'faction',$2)", pstate.world_day(),
            f"The {name} banner met its weekly {kind} — {note}")
    elif reached:
        note = "goal met, but the hall stood empty — no prize "
        note += f"(attendance {attended}/{required})"
    else:
        note = f"goal missed ({progress:,}/{target:,})"

    await conn.execute(
        "UPDATE ascent_faction_weeks SET progress=$2, ratio=$3, "
        "multiplier=$4, prize_note=$5 WHERE id=$1",
        row_id, progress,
        (attended / required) if required else 0.0, mult, note[:200])


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
                         banner: str, founder_name: str) -> None:
    week = world_week()
    await conn.execute(
        "INSERT INTO ascent_factions (name, banner, founder_tenant,"
        " founder_player, created_week) VALUES ($1,$2,$3,$4,$5)",
        name, banner, tenant, player, week)
    await conn.execute(
        "INSERT INTO ascent_faction_members (tenant, player, faction,"
        " role, joined_day) VALUES ($1,$2,$3,'steward',$4)",
        tenant, player, name, pstate.world_day())


async def join_faction(conn, tenant: str, player: str, name: str) -> None:
    exists = await conn.fetchval(
        "SELECT 1 FROM ascent_factions WHERE name=$1", name)
    if not exists:
        return                       # banner dissolved between scene and act
    await conn.execute(
        "INSERT INTO ascent_faction_members (tenant, player, faction,"
        " role, joined_day) VALUES ($1,$2,$3,'member',$4) "
        "ON CONFLICT (tenant, player) DO NOTHING",
        tenant, player, name, pstate.world_day())


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
