-- 056 realtime: the Playing tab.
-- Widen the existing world feed instead of inventing a second one.
-- Additive only — existing rows keep working (scope defaults to
-- 'world', which is exactly what every old row was).

ALTER TABLE ascent_happenings
    ADD COLUMN IF NOT EXISTS actor   TEXT,
    ADD COLUMN IF NOT EXISTS faction TEXT,
    ADD COLUMN IF NOT EXISTS scope   TEXT NOT NULL DEFAULT 'world',
    ADD COLUMN IF NOT EXISTS meta    JSONB;

-- the world tab reads (scope, id DESC); the faction tab reads
-- (faction, id DESC) across both scopes
CREATE INDEX IF NOT EXISTS ha_scope_id
    ON ascent_happenings (scope, id DESC);
CREATE INDEX IF NOT EXISTS ha_faction_id
    ON ascent_happenings (faction, id DESC)
    WHERE faction IS NOT NULL;
