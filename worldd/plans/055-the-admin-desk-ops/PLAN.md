# 055 — the admin desk learns operations

The desk (worldd `/admin`) can change a player's numbers but cannot
answer the two questions every support thread starts with: *where did
the coin go* and *why is this player stuck*. This plan gives the player
page both answers.

## 1. The ledger panel

Every gold and xp movement already lands in `ascent_ledger` — the desk
just never shows it. New endpoint, same key/session lock as the rest:

- `GET /admin/api/player/ledger?tenant&player&limit=50` → the player's
  most recent entries (at, kind, gold, xp, note), newest first.

The player page grows a LEDGER card: the last entries with kind and
note, gold/xp deltas signed. Admin edits (kind `admin`) read in the
same list — the desk's own hand is part of the trail.

## 2. The rescue

A stuck player is always one of: dead-locked hp, a broken encounter
doc, lodged past their day, or a location the renderer no longer
serves. One button clears all four at once, the way the engine itself
returns a climber to safety:

- `POST /admin/api/player/rescue {tenant, player}` — only for
  `stage == "playing"` docs. Under the row lock:
  - `hp = state.max_hp(p)` (the engine's own arithmetic, armor and
    faction buff included)
  - `encounter = None`, `scene = None`
  - `location = "town"`
  - `lodged_until_day = -1`
  - ledger row `kind=admin, note=rescue`, `updated_at` untouched.

The proof of correctness is not the field values — it is that the
engine will serve the doc again: the test rescues a live player and
then walks `/v1/scene` to confirm the tower answers.

## 3. Non-goals

- No floor/level edits — those move the era math; the parameters card
  already covers what support needs.
- No doc free-editing. Every admin write stays a named, audited verb.

## Tests

- ledger endpoint returns the creation trail + admin edits, capped.
- rescue: lodge + wound + fake a broken encounter, rescue, assert doc
  fields, assert `/v1/scene` serves town, assert the ledger note.
- rescue refuses a non-playing doc (404/400) and a ghost player.
