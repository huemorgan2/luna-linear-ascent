-- 081 phase-3: directed happenings — a feed row addressed to ONE player
-- (wires and letters). NULL recipient = broadcast, the ascent_letters
-- convention. Additive only; scope is free text (019), so the new
-- 'player' value needs no constraint change.

ALTER TABLE ascent_happenings
    ADD COLUMN IF NOT EXISTS to_tenant TEXT,
    ADD COLUMN IF NOT EXISTS to_player TEXT;

-- the recipient's peek reads (to_tenant, to_player, id DESC); partial —
-- broadcast rows (the vast majority) never enter it
CREATE INDEX IF NOT EXISTS ha_directed_id
    ON ascent_happenings (to_tenant, to_player, id DESC)
    WHERE to_player IS NOT NULL;
