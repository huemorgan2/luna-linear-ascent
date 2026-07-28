-- 009: the faction armory (017 phase 007) — a shared rack of gear.
-- Members donate paid gear (the wear-fraction rides with the piece,
-- never laundered back to full) and take pieces out again. No gold
-- moves through the armory, ever: the row stores exactly what left the
-- donor's pack and hands back exactly that. Additive only.

CREATE TABLE IF NOT EXISTS ascent_armory (
    id            bigserial PRIMARY KEY,
    faction       text NOT NULL REFERENCES ascent_factions(name)
                       ON DELETE CASCADE ON UPDATE CASCADE,
    tenant        text NOT NULL,           -- the donor
    player        text NOT NULL,
    donor_name    text NOT NULL DEFAULT '',
    slug          text NOT NULL,           -- FORGE catalog slug
    uses_left     int,                     -- durability stash; NULL = fresh
    deposited_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_armory_faction
    ON ascent_armory (faction, id);

-- one take per player per world day (the anti-vacuum cap)
CREATE TABLE IF NOT EXISTS ascent_armory_takes (
    tenant    text NOT NULL,
    player    text NOT NULL,
    take_day  int  NOT NULL,
    PRIMARY KEY (tenant, player)
);
