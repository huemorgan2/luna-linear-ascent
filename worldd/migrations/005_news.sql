-- 005: world news (007 §4) — happenings learn which floor they happened
-- on, so the Morning Crier can serve floor-local gossip. Additive only;
-- old rows default to floor 0 (world-wide news).

ALTER TABLE ascent_happenings
    ADD COLUMN IF NOT EXISTS floor INT NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_happenings_floor
    ON ascent_happenings (floor, world_day, id DESC);
