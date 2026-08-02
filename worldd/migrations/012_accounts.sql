-- 003-linearascent-net: old-days accounts — a username and a password.
-- The account is the person, not the climb: it survives the era, like
-- ascent_tenants (see app/era.py PERMANENT_TABLES).
CREATE TABLE IF NOT EXISTS ascent_accounts (
    id bigserial PRIMARY KEY,
    username text NOT NULL,
    pw_hash text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- one name, any casing — "Kettle" and "kettle" are the same door
CREATE UNIQUE INDEX IF NOT EXISTS ascent_accounts_username_lower
    ON ascent_accounts (lower(username));
