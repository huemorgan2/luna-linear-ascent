-- 078 Phase 1: generated projection columns on ascent_players.
--
-- Every hot social read used to filter on doc->>'…' (unindexable without
-- expression indexes) and several fetched EVERY playing doc and parsed it
-- in Python — O(players) per click. These columns are computed BY Postgres
-- from the same doc on every write; the doc itself is never rewritten and
-- nothing is dropped. Old code that reads doc directly keeps working.
--
-- Numeric fields go through ::numeric so a stray float in a legacy doc
-- rounds instead of failing the whole table rewrite.

ALTER TABLE ascent_players
    ADD COLUMN IF NOT EXISTS stage text
        GENERATED ALWAYS AS (doc->>'stage') STORED,
    ADD COLUMN IF NOT EXISTS name text
        GENERATED ALWAYS AS (doc->>'name') STORED,
    ADD COLUMN IF NOT EXISTS race text
        GENERATED ALWAYS AS (doc->>'race') STORED,
    ADD COLUMN IF NOT EXISTS clazz text
        GENERATED ALWAYS AS (doc->>'clazz') STORED,
    ADD COLUMN IF NOT EXISTS guild text
        GENERATED ALWAYS AS (doc->>'guild') STORED,
    ADD COLUMN IF NOT EXISTS location text
        GENERATED ALWAYS AS (doc->>'location') STORED,
    -- the census/presence floor rule: town counts as floor 1
    ADD COLUMN IF NOT EXISTS floor int
        GENERATED ALWAYS AS
        (greatest(coalesce(round((doc->>'floor')::numeric)::int, 0), 1))
        STORED,
    ADD COLUMN IF NOT EXISTS unlocked_floor int
        GENERATED ALWAYS AS
        (coalesce(round((doc->>'unlocked_floor')::numeric)::int, 1)) STORED,
    ADD COLUMN IF NOT EXISTS level int
        GENERATED ALWAYS AS
        (coalesce(round((doc->>'level')::numeric)::int, 1)) STORED,
    ADD COLUMN IF NOT EXISTS gold bigint
        GENERATED ALWAYS AS
        (coalesce(round((doc->>'gold')::numeric)::bigint, 0)) STORED,
    ADD COLUMN IF NOT EXISTS bank bigint
        GENERATED ALWAYS AS
        (coalesce(round((doc->>'bank')::numeric)::bigint, 0)) STORED,
    -- -1 mirrors _pvp_targets' "never lodged" default
    ADD COLUMN IF NOT EXISTS lodged_until_day int
        GENERATED ALWAYS AS
        (coalesce(round((doc->>'lodged_until_day')::numeric)::int, -1))
        STORED,
    -- a sleeping body is IN the bunkroom however long it lies (042)
    ADD COLUMN IF NOT EXISTS sleeping boolean
        GENERATED ALWAYS AS
        (doc->'sleeping' IS NOT NULL AND doc->'sleeping' <> 'null'::jsonb)
        STORED;

-- The playing set is the working set — partial indexes keep them tiny.
CREATE INDEX IF NOT EXISTS ix_players_playing_updated
    ON ascent_players (updated_at DESC) WHERE stage = 'playing';
CREATE INDEX IF NOT EXISTS ix_players_playing_floor
    ON ascent_players (floor) WHERE stage = 'playing';
CREATE INDEX IF NOT EXISTS ix_players_playing_name
    ON ascent_players (name) WHERE stage = 'playing';
-- the Muster Roll's board order
CREATE INDEX IF NOT EXISTS ix_players_playing_roster
    ON ascent_players (unlocked_floor DESC, level DESC)
    WHERE stage = 'playing';

-- 078: _profiles' contribution sums used to GROUP the whole ledger /
-- damage tables per act; now they filter by the profiled players.
CREATE INDEX IF NOT EXISTS ix_faction_ledger_giver
    ON ascent_faction_ledger (tenant, player)
    WHERE amount > 0 AND kind IN ('join_fee','dues','donation');
CREATE INDEX IF NOT EXISTS ix_warden_damage_giver
    ON ascent_warden_damage (tenant, player);
CREATE INDEX IF NOT EXISTS ix_armory_donor
    ON ascent_armory (tenant, player);
