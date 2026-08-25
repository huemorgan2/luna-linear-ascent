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

## Execution status (2026-08-25)

- **Step 1 evidence (prod, ascent-world-db).** huemorgan4 = tenant
  `web`, player `huemorgan4`, now level 2, gold 1080. Ledger: `grant_in`
  ◈ 90 (from huemorgan, 07:20:06Z) + `grant_in` ◈ 101 (from huemorgan3,
  07:21:20Z), then ONE `letter_gold` ◈ 191 "collected" at 07:22:42Z —
  the first click credited everything; the red banner was the stale
  second click. No data lost, no correction needed. Access: machine IP
  added to the DB allow list via Render API, queried, allow list
  reverted to empty within minutes; connection material deleted.
- **Steps 2-4 implemented.** `_REFRESH_KINDS` rebuild in
  app/game.py `run_act` (re-inject world, `core.current_scene`, receipt
  note "The clerk counts out ◈ N — yours now.", second
  `execute_effects` pass); graceful stale `collect` in
  engine core.py `apply_choice` (clerk ledger line, no refusal);
  `w["gold_held"]` in app/social.py `inject_world` + gate in engine
  `relay_scene`. Notices and door gates already used the uncapped
  `inbox_count` (notices.py:151, core.py:1383, core.py:1461-1463) — no
  change needed there.
- **Step 5 tests.** `test_level1_collect_updates_card` (level-1
  receiver, asserts the returned card: receipt note, no enclosed line,
  no collect row, no refusal, friendly second click, exactly one ledger
  row) and `test_collect_row_survives_deep_inbox` (gold letter buried
  9th under 8 newer letters — Collect row present, ◈ 70 credited).
- **Suites.** worldd 216/216 passed. Plugin: 1369 passed, 8 failed —
  byte-identical failures on the pre-change tree (test_017 ×2,
  test_022, test_048, test_067, test_kill3d ×3), pre-existing at
  submodule HEAD a78de50, not from this phase.
- **Commits.** Plan aa6f4fd; submodule 83f21b3; parent 1f8a6e3 (vendor
  sync + pointer). Deploy deferred to phase-7 (ships all phases).
