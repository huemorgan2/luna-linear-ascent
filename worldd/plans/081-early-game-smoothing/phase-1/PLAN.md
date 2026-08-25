# 081 phase-1 — relay collect: the card tells the truth

## Goal

Collecting granted gold at level 1 works on the first click AND looks like
it worked: the returned card shows the incremented gold, no *Collect* row,
no COLLECT notice. A stale second click gets a friendly clerk line, never
the red "not one of the paths" banner. Measurable: the level-1 dojo
scenario (01) passes end to end; `test_social_api.py` gains a level-1 case
that asserts against the returned card, not just the doc.

## Steps

1. **Track first (evidence for huemorgan4).** Against prod DB, read
   `ascent_ledger` for that player: expect exactly one
   `kind='letter_gold'` row (inserted at app/social.py:1276) and the
   matching `grant_in` row. Record amounts + timestamps in this file's
   Execution status. If the row is absent, the letter still holds its
   gold (`ascent_letters.gold > 0`) and will be collectable after this
   phase — state which case it is.
2. **Post-effect card rebuild** in `app/game.py` `run_act`
   (game.py:168-217). After `social.execute_effects(...)` (game.py:207),
   if any executed effect kind is in a new `REFRESH_KINDS =
   {"collect_letter_gold"}` set: re-run the world injection that fills
   `w["letters"]` / `w["inbox_count"]` (app/social.py:172-188), rebuild
   the current-location scene via the engine's scene builder
   (core `_build_scene` path), carry over the original scene's
   `shard_note` ("+ the clerk counts it out twice"), and use THAT scene
   for both `doc["scene"]` (game.py:212) and the response (game.py:217).
   Keep the set minimal — this is a scalpel, not a rewrite of act
   ordering.
3. **Graceful stale collect** in the engine (both copies): in
   `apply_choice`'s unknown-option branch (core.py:700-710), special-case
   `option_id == "collect"` → return the current scene with
   `shard_note`/`note` "The clerk has nothing more for you — that gold is
   already in your purse." and NO `refusal`, so the client swaps the card
   (pane.py:620 only suppresses the swap on refusal) and the stale button
   disappears.
4. **Close the LIMIT-8 gap**: gate the *Collect* option and the COLLECT
   notice on a DB-side "any unread gold" flag. Add
   `w["gold_held"]` (count/sum of unread letters with `gold > 0`,
   uncapped) next to `w["inbox_count"]` in app/social.py:172-188; use it
   in `relay_scene` (engine/social.py:31-66) instead of
   `any(l.get("gold") ...)` over the 8-letter window, and in
   `_guildhall`-style notices where COLLECT is surfaced.
5. **Tests.**
   - Extend `worldd/tests/test_social_api.py`: receiver at level 1;
     after collect assert response fragment has no `collect` option, gold
     meter shows the credited total, and a second `collect` act returns
     `ok` with the clerk note and no `refusal`.
   - Regression: >8 unread letters with the gold letter oldest — Collect
     row still present.
6. **Vendor sync**: engine edits in `plugin-linear-ascent` submodule
   first, then `worldd/vendor` copy + parent pointer.

## Verification

- `pytest worldd/tests/test_social_api.py` then full worldd + plugin
  suites.
- Manual: level-1 receiver in local env — send grant, collect once,
  screenshot card (gold updated, no Collect row); click where the button
  was → nothing hostile.
- Prod after deploy: ledger query from step 1 re-run; no new
  "not one of the paths" refusals following `collect` acts in logs.

## Rollback

Revert the commit(s). No migration, no doc-shape change; `w["gold_held"]`
is derived per-request. The vendor pointer reverts with the parent
commit.
