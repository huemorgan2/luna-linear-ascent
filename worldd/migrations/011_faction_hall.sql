-- 011: the banner hall (plan 032) — room tiers, the coffer's cap, chest
-- slots, bunks, and the bulletin board. Every price and cap lives in code
-- (factions.py, next to FOUND_FEE — one tuning surface); this file only
-- snapshots the caps to grandfather rows that predate it. Additive only.

ALTER TABLE ascent_factions
    ADD COLUMN IF NOT EXISTS room_tier   int NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS coffer_tier int NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS chest_tier  int NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS beds        int NOT NULL DEFAULT 0;

-- the bulletin board: one line per member per world-day; writing again
-- the same day replaces the line (no flooding, no moderation surface)
CREATE TABLE IF NOT EXISTS ascent_faction_notes (
    id bigserial PRIMARY KEY,
    faction text NOT NULL REFERENCES ascent_factions(name)
        ON DELETE CASCADE ON UPDATE CASCADE,
    tenant text NOT NULL, player text NOT NULL,
    world_day int NOT NULL, line text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (faction, tenant, player, world_day)   -- one note/member/day
);
CREATE INDEX IF NOT EXISTS idx_faction_notes_faction
    ON ascent_faction_notes (faction, id DESC);

-- the bunks: a claim is a free safe night — it sets the SAME
-- lodged_until_day flag the Lodge sells, so PvP targeting needs no change
CREATE TABLE IF NOT EXISTS ascent_faction_bed_claims (
    tenant text NOT NULL, player text NOT NULL,
    faction text NOT NULL REFERENCES ascent_factions(name)
        ON DELETE CASCADE ON UPDATE CASCADE,
    world_day int NOT NULL,
    PRIMARY KEY (tenant, player, world_day)       -- one bed/member/night
);
CREATE INDEX IF NOT EXISTS idx_faction_bed_claims_faction
    ON ascent_faction_bed_claims (faction, world_day);

-- grandfather existing banners: the smallest coffer tier whose cap
-- covers the treasury already held (caps 200 / 600 / 2,500 / 8,000)
UPDATE ascent_factions SET coffer_tier = CASE
    WHEN treasury <= 200  THEN 1
    WHEN treasury <= 600  THEN 2
    WHEN treasury <= 2500 THEN 3
    ELSE 4 END;

-- ...and the smallest chest tier whose slots cover the armory rows
-- already racked (slots 4 / 8 / 16 / 32) — never truncated
UPDATE ascent_factions f SET chest_tier = CASE
    WHEN a.n <= 4  THEN 1
    WHEN a.n <= 8  THEN 2
    WHEN a.n <= 16 THEN 3
    ELSE 4 END
FROM (SELECT faction, count(*) AS n FROM ascent_armory GROUP BY faction) a
WHERE a.faction = f.name;
