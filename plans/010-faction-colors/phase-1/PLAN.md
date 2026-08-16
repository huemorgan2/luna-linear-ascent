# Phase 1 — server: the color column and its doors

## Goal

`ascent_factions` carries a `color` (slug from the 9-name roster,
default `warden-violet`); founding accepts it, stewards can change it,
and every faction payload the engine receives includes it. Measurable:
new worldd tests pass; a psql `SELECT color FROM ascent_factions`
returns `warden-violet` for every pre-existing row.

## Steps

1. **Migration** `worldd/migrations/020_faction_colors.sql`:
   ```sql
   ALTER TABLE ascent_factions
     ADD COLUMN IF NOT EXISTS color text NOT NULL DEFAULT 'warden-violet';
   ```
2. **`worldd/app/factions.py`**
   - `COLOR_SLUGS: list[str]` — the 9 roster slugs (mirror of the
     plugin's `colors.py`; slugs only, no hexes).
   - `found_faction(..., color: str = "")`: validate
     (`color in COLOR_SLUGS`, else 422 "unknown color" — empty string
     falls back to the default); thread into `create_faction` INSERT.
   - `recolor_faction(conn, tenant, player, color)` — mirrors
     `rename_faction`: steward-only (403 otherwise), validates slug
     (422), `UPDATE ascent_factions SET color=$1 WHERE name=$2`.
   - `member_summary` payload: add `"color": fac["color"]` (the dict
     built ~L272 in `app/social.py` reads it from the row — extend the
     `SELECT` at ~L234 with `color`).
3. **`worldd/app/social.py`**
   - Hydration: `w["faction_colors"] = factions.COLOR_SLUGS` beside the
     existing `w["faction_banners"]` (the founding flow's picker reads
     it).
   - Faction dict for members: include `"color"`.
   - Effects switch (~L1073): handle `"faction_recolor"` →
     `factions.recolor_faction(...)`, beside `faction_rename`.
   - Founding effect (~L1135): pass `e.get("color", "")` through to
     `found_faction`.
4. **Endpoints**
   - `worldd/app/main.py`: `POST /v1/faction/recolor`
     (`FactionColorIn {color: str}`), beside `/v1/faction/rename`
     (~L458).
   - `worldd/app/webplay.py`: `POST /play/api/pane/faction/recolor`,
     beside the rename route (~L340).

## Verification

- New `worldd/tests/test_faction_colors.py`:
  - found with `color="ember-red"` → row persists `ember-red`;
  - found with no color → `warden-violet`;
  - recolor by steward → 200 and row updated; by plain member → 403;
  - `color="hot-pink"` → 422;
  - member faction payload includes `color`.
- `cd worldd && pytest` — full suite green.
- Against the dev DB: apply 020, then
  `SELECT name, color FROM ascent_factions;` → every old row
  `warden-violet`.

## Rollback

```sql
ALTER TABLE ascent_factions DROP COLUMN IF EXISTS color;
```
plus `git revert` of the phase commit. The column is additive and
default-filled, so reverting code without dropping the column is also
safe.

## Execution status

_(appended after execution)_
