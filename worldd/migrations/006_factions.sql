-- 006: factions (plan 010) — real membership, weekly goals, attendance.
-- ascent_guilds stays in place (data preserved per devprocess); factions
-- are the authoritative evolution and existing guilds are migrated in.

CREATE TABLE IF NOT EXISTS ascent_factions (
    name            text PRIMARY KEY,
    banner          text NOT NULL DEFAULT 'wolf_howl',
    founder_tenant  text NOT NULL DEFAULT '',
    founder_player  text NOT NULL DEFAULT '',
    created_week    int  NOT NULL DEFAULT 0,
    goal_kind       text NOT NULL DEFAULT 'hoard',   -- hoard | cull | climb
    goal_target     bigint NOT NULL DEFAULT 0,        -- 0 = no goal set
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ascent_faction_members (
    tenant      text NOT NULL,
    player      text NOT NULL,
    faction     text NOT NULL REFERENCES ascent_factions(name)
                     ON DELETE CASCADE,
    role        text NOT NULL DEFAULT 'member',       -- steward | member
    joined_day  int  NOT NULL DEFAULT 0,              -- world_day of joining
    PRIMARY KEY (tenant, player)
);
CREATE INDEX IF NOT EXISTS idx_faction_members_faction
    ON ascent_faction_members (faction);

-- one row per player per world_day with at least one act — the attendance
-- ledger behind the weekly prize multiplier
CREATE TABLE IF NOT EXISTS ascent_attendance (
    tenant     text NOT NULL,
    player     text NOT NULL,
    world_day  int  NOT NULL,
    PRIMARY KEY (tenant, player, world_day)
);
CREATE INDEX IF NOT EXISTS idx_attendance_day
    ON ascent_attendance (world_day);

-- resolved week history; the UNIQUE constraint is the idempotency lock
CREATE TABLE IF NOT EXISTS ascent_faction_weeks (
    id           bigserial PRIMARY KEY,
    faction      text NOT NULL,
    week         int  NOT NULL,
    goal_kind    text NOT NULL DEFAULT '',
    goal_target  bigint NOT NULL DEFAULT 0,
    progress     bigint NOT NULL DEFAULT 0,
    ratio        real NOT NULL DEFAULT 0,
    multiplier   real NOT NULL DEFAULT 0,
    prize_note   text NOT NULL DEFAULT '',
    resolved_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (faction, week)
);

-- migrate existing guilds → factions (names + founders preserved)
INSERT INTO ascent_factions (name, founder_player, created_at)
SELECT guild, founder, created_at FROM ascent_guilds
ON CONFLICT (name) DO NOTHING;

-- migrate memberships from player docs (doc->>'guild' was the only record);
-- the guild founder (by character name) becomes steward
INSERT INTO ascent_faction_members (tenant, player, faction, role, joined_day)
SELECT p.tenant, p.player, f.name,
       CASE WHEN p.doc->>'name' = f.founder_player
            THEN 'steward' ELSE 'member' END,
       0
FROM ascent_players p
JOIN ascent_factions f ON f.name = p.doc->>'guild'
WHERE p.doc->>'stage' = 'playing'
ON CONFLICT DO NOTHING;

-- factions whose steward didn't migrate get the earliest member promoted
UPDATE ascent_faction_members m SET role = 'steward'
WHERE role = 'member'
  AND NOT EXISTS (SELECT 1 FROM ascent_faction_members s
                  WHERE s.faction = m.faction AND s.role = 'steward')
  AND (m.tenant, m.player) = (
      SELECT tenant, player FROM ascent_faction_members
      WHERE faction = m.faction ORDER BY joined_day, tenant, player LIMIT 1);
