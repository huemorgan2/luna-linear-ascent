-- 008: the faction desk (plan 015) — join requests + renameable banners.
-- Joining a banner now files a request an admin accepts or rejects; the
-- join fee is charged at ACCEPT time. Renames must carry membership with
-- them, so the members FK gains ON UPDATE CASCADE (weeks/ledger rows are
-- plain text and are updated by the rename routine). Additive only — no
-- data is dropped.

CREATE TABLE IF NOT EXISTS ascent_faction_requests (
    tenant         text NOT NULL,
    player         text NOT NULL,
    faction        text NOT NULL REFERENCES ascent_factions(name)
                        ON DELETE CASCADE ON UPDATE CASCADE,
    requested_day  int  NOT NULL DEFAULT 0,
    created_at     timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant, player)
);
CREATE INDEX IF NOT EXISTS idx_faction_requests_faction
    ON ascent_faction_requests (faction);

ALTER TABLE ascent_faction_members
    DROP CONSTRAINT IF EXISTS ascent_faction_members_faction_fkey;
ALTER TABLE ascent_faction_members
    ADD CONSTRAINT ascent_faction_members_faction_fkey
    FOREIGN KEY (faction) REFERENCES ascent_factions(name)
    ON DELETE CASCADE ON UPDATE CASCADE;
