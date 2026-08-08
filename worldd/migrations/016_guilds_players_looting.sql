-- 042 guilds/players/looting: joining terms on the banner, the loot log,
-- the warden damage roll, and a fast path for the 1-hour activity read.

-- A steward's door rules: {"min_level": 10, "invite_only": true} — empty
-- means the door is open to anyone who covers the fee.
ALTER TABLE ascent_factions
    ADD COLUMN IF NOT EXISTS requirements jsonb NOT NULL DEFAULT '{}';

-- Every loot attempt, win or lose — the tower logs the name on the blade.
CREATE TABLE IF NOT EXISTS ascent_loot_attempts (
    id         bigserial PRIMARY KEY,
    tenant     text NOT NULL,
    player     text NOT NULL,
    target_tenant text NOT NULL,
    target_player text NOT NULL,
    outcome    text NOT NULL,            -- 'win' | 'fail' | 'blocked'
    haul       integer NOT NULL DEFAULT 0,
    item       text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_loot_attempts_target
    ON ascent_loot_attempts (target_tenant, target_player, created_at);

-- Per-strike warden damage — dealt and taken — so the boards survive the
-- 40-strike truncation of the live record.
CREATE TABLE IF NOT EXISTS ascent_warden_damage (
    id         bigserial PRIMARY KEY,
    floor      integer NOT NULL,
    tenant     text NOT NULL,
    player     text NOT NULL,
    name       text NOT NULL,
    dmg        integer NOT NULL DEFAULT 0,
    taken      integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_warden_damage_floor
    ON ascent_warden_damage (floor, created_at);

-- The 1-hour looting rule reads updated_at across the room's occupants.
CREATE INDEX IF NOT EXISTS idx_players_updated
    ON ascent_players (updated_at);
