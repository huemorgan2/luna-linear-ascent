-- 003: social layer — letters, happenings, boss quorum commits, guilds.

CREATE TABLE IF NOT EXISTS ascent_letters (
    id          BIGSERIAL PRIMARY KEY,
    to_tenant   TEXT NOT NULL,
    to_player   TEXT NOT NULL,
    from_name   TEXT NOT NULL,
    body        TEXT NOT NULL,
    gold        BIGINT NOT NULL DEFAULT 0,
    read        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_letters_inbox
    ON ascent_letters (to_tenant, to_player, read, id);

CREATE TABLE IF NOT EXISTS ascent_happenings (
    id          BIGSERIAL PRIMARY KEY,
    world_day   INT NOT NULL,
    kind        TEXT NOT NULL,
    line        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_happenings_day
    ON ascent_happenings (world_day, id DESC);

CREATE TABLE IF NOT EXISTS ascent_boss_commits (
    floor       INT NOT NULL,
    tenant      TEXT NOT NULL,
    player      TEXT NOT NULL,
    name        TEXT NOT NULL,
    world_day   INT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (floor, tenant, player)
);

CREATE TABLE IF NOT EXISTS ascent_guilds (
    guild       TEXT PRIMARY KEY,
    founder     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ascent_stone (
    id          BIGSERIAL PRIMARY KEY,
    line        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
