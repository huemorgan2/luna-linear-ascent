-- 004-one-name: one name, one world. A climber's name IS their username —
-- one word, unique across every tenant and the site's door alike.
--
-- Nothing is dropped here. The names that already exist are TRANSFORMED in
-- place: "Master Chief" becomes "MasterChief", collisions take a numeric
-- suffix, and every survivor lands in the registry with its owner recorded.
CREATE TABLE IF NOT EXISTS ascent_names (
    name_lower text PRIMARY KEY,
    name       text NOT NULL,
    kind       text NOT NULL,          -- 'account' | 'climber'
    tenant     text,
    player     text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ascent_names_owner
    ON ascent_names (tenant, player);

-- The mason's alphabet, in SQL: the same rule as engine/names.py —
-- letters and numbers in any script, plus - and _, and nothing else.
CREATE OR REPLACE FUNCTION ascent_canonical_name(raw text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT left(regexp_replace(coalesce(raw, ''), '[^[:alnum:]_-]', '', 'g'),
                24);
$$;

-- The first free variant of a name: Fleet, then Fleet2, Fleet3 …
CREATE OR REPLACE FUNCTION ascent_free_name(base text)
RETURNS text LANGUAGE plpgsql AS $$
DECLARE
    stem text := ascent_canonical_name(base);
    try  text;
    n    int := 1;
BEGIN
    IF length(stem) < 2 THEN
        stem := 'climber';
    END IF;
    try := stem;
    WHILE EXISTS (SELECT 1 FROM ascent_names
                  WHERE name_lower = lower(try)) LOOP
        n := n + 1;
        try := left(stem, 24 - length(n::text)) || n::text;
    END LOOP;
    RETURN try;
END;
$$;

-- 1. The door's accounts go first: the person outlives the climb, so an
--    account keeps the name when a climber wants the same one.
DO $$
DECLARE
    r    record;
    want text;
BEGIN
    FOR r IN SELECT id, username FROM ascent_accounts ORDER BY id LOOP
        want := ascent_free_name(r.username);
        IF want <> r.username THEN
            UPDATE ascent_accounts SET username = want WHERE id = r.id;
        END IF;
        INSERT INTO ascent_names (name_lower, name, kind)
        VALUES (lower(want), want, 'account')
        ON CONFLICT (name_lower) DO NOTHING;
    END LOOP;
END;
$$;

-- 2. Then every climber who already has a name on a doc. The busiest
--    hands go first (a live climber keeps the name a dormant one shares).
DO $$
DECLARE
    r    record;
    want text;
BEGIN
    FOR r IN SELECT tenant, player, doc->>'name' AS nm
             FROM ascent_players
             WHERE coalesce(doc->>'name', '') <> ''
             ORDER BY updated_at DESC LOOP
        want := ascent_free_name(r.nm);
        IF want <> r.nm THEN
            UPDATE ascent_players
               SET doc = jsonb_set(doc, '{name}', to_jsonb(want))
             WHERE tenant = r.tenant AND player = r.player;
        END IF;
        INSERT INTO ascent_names (name_lower, name, kind, tenant, player)
        VALUES (lower(want), want, 'climber', r.tenant, r.player)
        ON CONFLICT (name_lower) DO NOTHING;
    END LOOP;
END;
$$;
