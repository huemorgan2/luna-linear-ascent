-- 007: the faction store (plan 010, third + fourth directives).
-- Factions gain a shared purse: a one-time join fee and weekly dues both
-- land in the treasury; the world posts ONE challenge per week and
-- entering it is paid from the store. Additive only — goal_kind /
-- goal_target stay in place (data preserved; the world posts challenges
-- now, stewards no longer set goals).

ALTER TABLE ascent_factions
    ADD COLUMN IF NOT EXISTS join_fee    int    NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS weekly_dues int    NOT NULL DEFAULT 5,
    ADD COLUMN IF NOT EXISTS treasury    bigint NOT NULL DEFAULT 0;

ALTER TABLE ascent_faction_members
    ADD COLUMN IF NOT EXISTS arrears boolean NOT NULL DEFAULT false;

-- weeks become two-phase: the row is created when the steward ENTERS the
-- world challenge (entered=true, entry_paid=the store debit) and later
-- marked resolved; factions that never entered get a resolved row with
-- entered=false at week turn (dues still collect).
ALTER TABLE ascent_faction_weeks
    ADD COLUMN IF NOT EXISTS entered    boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS entry_paid bigint  NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS won        boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS resolved   boolean NOT NULL DEFAULT false;

-- rows that predate this migration were all written by the resolver
UPDATE ascent_faction_weeks SET resolved = true, entered = true
WHERE NOT resolved AND prize_note <> '';

-- every store movement, auditable: join fees, dues, donations, entries
CREATE TABLE IF NOT EXISTS ascent_faction_ledger (
    id          bigserial PRIMARY KEY,
    faction     text   NOT NULL,
    week        int    NOT NULL DEFAULT 0,
    kind        text   NOT NULL,       -- join_fee|dues|donation|entry
    amount      bigint NOT NULL,       -- + into the store, - out of it
    tenant      text   NOT NULL DEFAULT '',
    player      text   NOT NULL DEFAULT '',
    note        text   NOT NULL DEFAULT '',
    created_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_faction_ledger_faction
    ON ascent_faction_ledger (faction, id DESC);
