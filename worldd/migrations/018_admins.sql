-- 018: the approved-admins list. The desk door stops being a key and
-- becomes a list of names (004: a name is an identity). Seeded from
-- ASCENT_FEEDBACK_ADMINS by the first reader; managed from the desk.
CREATE TABLE IF NOT EXISTS ascent_admins (
    name       text PRIMARY KEY,
    added_by   text NOT NULL DEFAULT '',
    added_at   timestamptz NOT NULL DEFAULT now()
);
