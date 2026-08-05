-- 034 §3 — a Warden dies once, and the keep remembers when.
--
-- `fallen:{floor}` stored the slayer roll as a bare JSON string. The
-- memorial that now stands where an echo bout used to be needs a date as
-- well as a roll, so the row becomes an object:
--     {"names": "...", "day": 41, "ts": "2026-08-01T09:12:03+00:00"}
--
-- ADDITIVE ONLY. The names are copied verbatim into the new shape, the
-- date is recovered from the boss happening that floor wrote at the fall,
-- and floors whose happening has already scrolled away keep their names
-- with no date at all — the memorial says "in the early days of the
-- climb" rather than inventing one. Nothing is dropped, deleted or
-- overwritten with less than it held. Readers accept both shapes anyway,
-- so this migration is a convenience, not a requirement.

UPDATE ascent_world w
SET value = jsonb_build_object(
        'names', w.value,
        'day',   h.world_day,
        'ts',    to_char(h.created_at AT TIME ZONE 'UTC',
                         'YYYY-MM-DD"T"HH24:MI:SS+00:00'))
FROM (
    SELECT floor,
           min(world_day)  AS world_day,
           min(created_at) AS created_at
    FROM ascent_happenings
    WHERE kind = 'boss' AND floor > 0
    GROUP BY floor
) h
WHERE w.key = 'fallen:' || h.floor::text
  AND jsonb_typeof(w.value) = 'string';

-- Every remaining legacy row: same object, no date.
UPDATE ascent_world
SET value = jsonb_build_object('names', value)
WHERE key LIKE 'fallen:%'
  AND jsonb_typeof(value) = 'string';
