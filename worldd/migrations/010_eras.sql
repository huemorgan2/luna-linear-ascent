-- 022/007: the era — the two PERMANENT tables. They live OUTSIDE the
-- reset scope: every other ascent_* table is wiped when an era ends,
-- these two survive forever (the Stone of Eras and the reincarnation
-- ledger). ascent_tenants also survives — auth is not era state.

CREATE TABLE IF NOT EXISTS ascent_eras (
    era        integer PRIMARY KEY,
    data       jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ascent_reincarnation (
    tenant  text NOT NULL,
    player  text NOT NULL,
    era     integer NOT NULL,
    name    text NOT NULL DEFAULT '',
    points  integer NOT NULL DEFAULT 1,
    tiers   jsonb NOT NULL DEFAULT '[]',
    PRIMARY KEY (tenant, player, era)
);
