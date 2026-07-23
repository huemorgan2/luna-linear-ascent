-- 002: shared-world schema — tenants, players, ledger, idempotency.

CREATE TABLE IF NOT EXISTS ascent_tenants (
    tenant      TEXT PRIMARY KEY,
    secret      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS ascent_players (
    tenant      TEXT NOT NULL REFERENCES ascent_tenants(tenant),
    player      TEXT NOT NULL,
    doc         JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant, player)
);

CREATE TABLE IF NOT EXISTS ascent_ledger (
    id          BIGSERIAL PRIMARY KEY,
    tenant      TEXT NOT NULL,
    player      TEXT NOT NULL,
    kind        TEXT NOT NULL,
    gold        BIGINT NOT NULL DEFAULT 0,
    xp          BIGINT NOT NULL DEFAULT 0,
    note        TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ledger_tp ON ascent_ledger (tenant, player, id);

CREATE TABLE IF NOT EXISTS ascent_idempotency (
    tenant      TEXT NOT NULL,
    idem        TEXT NOT NULL,
    response    JSONB NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant, idem)
);

-- world-shared state (frontier floor etc.)
CREATE TABLE IF NOT EXISTS ascent_world (
    key         TEXT PRIMARY KEY,
    value       JSONB NOT NULL
);
INSERT INTO ascent_world (key, value)
    VALUES ('frontier', '1'::jsonb)
    ON CONFLICT (key) DO NOTHING;
