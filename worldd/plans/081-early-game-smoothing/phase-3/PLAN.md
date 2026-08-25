# 081 phase-3 — wires and letters hit the live stream, sticky and clickable

## Goal

When a player is wired gold (grant) or sent a letter, a notification
appears in their live stream within one 2 s peek cycle, as a **sticky**
toast (no auto-timeout) that stays until dismissed (✕) or clicked; a
click navigates to the Relay Office. Directed rows are visible ONLY to
the recipient. Dismissal survives a page reload. Measurable: dojo
scenario 03 — receiver sees the toast ≤ 4 s after the send, a third
player never sees it, click lands in the Relay, ✕ + reload does not
resurrect it.

## Steps

1. **Migration `0XX_directed_happenings.sql`** (additive, next free
   number in `worldd/migrations/`): on `ascent_happenings` add
   `to_tenant text`, `to_player text` (nullable; NULL = broadcast, the
   letters convention from 003_social.sql), plus a partial index on
   `(to_tenant, to_player, id)` where `to_player IS NOT NULL`. `scope`
   gains the value `'player'` (it's text with default 'world' — no
   constraint change; verify in 019_realtime.sql:7-11).
2. **Write door**: extend `add_happening` (app/social.py:855-880) with
   optional `to_tenant`/`to_player`; keep it the single door so the
   `_feed_head` bump (social.py:851) delivers realtime for free.
3. **Emit**:
   - `_fx_grant` (app/social.py:1282-1300), after the letters/ledger
     inserts: `kind="grant"`, `scope="player"`, recipient = resolved row,
     `line = "◈ {net} wired from {sender} — collect at the Relay
     Office"`, `meta={"go": "relay"}`.
   - `_fx_send_letter` (app/social.py:1253-1261): `kind="letter"`,
     `scope="player"`, `line = "A letter from {sender} waits at the
     Relay Office"`, `meta={"go": "relay"}`.
4. **Read path**: in `playing_feed` (app/social.py:930-975) fetch the
   caller's directed rows (`to_tenant/to_player = me`, recent window,
   e.g. 7 days) in a **separate uncached query** and merge them into the
   response — the 2 s in-process `_feed_rows` cache (social.py:918-928)
   is keyed per scope, not per player, and MUST NOT serve directed rows
   or they leak between players. Row shape gains `"meta"` (at least the
   `go` key). Broadcast queries exclude `scope='player'` rows.
5. **Client — sticky toast** (`pane.py`, both copies):
   - `const PLY_STICKY = {grant: 1, letter: 1};` — in `plyToast`
     (pane.py:1242-1261) skip the `setTimeout(gone, PLY_TOAST_MS)` for
     sticky kinds; sticky toasts also bypass the `PLY_TOAST_MAX = 4` cap
     accounting so a burst of kills can't push a wire off screen.
   - Click-to-navigate: make the toast body a click target (excluding
     the ✕): for `meta.go === 'relay'`, mark seen, remove the toast,
     `switchTab('game')`, and POST `/act` with a new engine deep-link
     option `goto_relay` (see step 6), reusing the delegate pattern at
     pane.py:1377-1397.
   - CSS: `.plytoast.grant` / `.plytoast.letter` next to pane.py:254-255
     (gold ink for grant, aether for letter), and matching `.plyrow.*`
     at pane.py:225-229 so the panel list colors them too.
6. **Engine deep-link** (both copies): accept option `goto_relay` in
   `apply_choice` for non-combat scenes → set location to the Relay and
   return `relay_scene`. Guards: refused mid-encounter with a normal
   refusal line; the Relay door rule stays intact — for a level-1
   recipient `inbox > 0` by construction (the notification exists
   because a letter row exists), so the L1 gate (core.py:1376-1387)
   opens.
7. **Dismissal persistence**: third copy of the `plyStore` pattern
   (pane.py:1203-1211 — the comment there blesses copying it):
   `la_ntf_seen` holds a capped (last 50) list of dismissed/clicked
   happening ids. On load, `plyToastLoad` (pane.py:1226-1241) shows
   directed rows from the feed that are not in the seen set, regardless
   of the `since` cursor; broadcast toasts keep today's behavior.
8. **Tests** (`worldd/tests/test_060_playing_toasts.py`,
   `test_social_api.py`): grant emits a directed row; letter emits one;
   `playing_feed` as recipient includes it, as a third player excludes
   it; cache does not leak directed rows across two different callers
   within the 2 s window.
9. **Vendor sync** for pane.py/engine edits: submodule first, then
   `worldd/vendor` + parent pointer. Bump the pane asset version param
   in `app/webplay.py` if pane JS is version-stamped.

## Verification

- Targeted tests above, then both full suites.
- Manual, two browsers: A wires B ◈ 50 → B's toast within ~4 s, sticky
  through 30 s idle; B clicks → Relay card with the grant letter; B
  collects (phase-1 behavior verified again here); reload → no
  resurrection. Third browser C: nothing.
- SQL: directed rows carry `scope='player'` and both recipient columns;
  broadcast feed queries return none of them.

## Rollback

Revert the code commit(s); the migration stays (additive columns are
harmless and empty once emitters are gone). If the migration itself must
go: `ALTER TABLE ascent_happenings DROP COLUMN to_tenant, DROP COLUMN
to_player;` and drop the partial index — safe because nothing else reads
them.

## Execution status

Executed 2026-08-25.

1. Migration `worldd/migrations/023_directed_happenings.sql` written:
   `to_tenant`/`to_player` TEXT columns + partial index `ha_directed_id`
   (applies on next deploy boot; additive, no backfill needed).
2. `add_happening` gained `to_tenant`/`to_player` params; `_fx_send_letter`
   and `_fx_grant` emit `scope='player'` rows with `meta={"go":"relay"}`
   after their INSERTs — same head-bump door, so realtime is free.
3. `playing_feed`: broadcast/faction cached queries exclude
   `scope='player'`; directed rows come from a deliberately UNCACHED
   per-player query (7-day window, FEED_LIMIT cap, id-dedup merge);
   `scope='player'` rows are exempt from the since-cursor so undismissed
   mail resurfaces on reload. `meta` (jsonb→str) json-loaded into the row.
4. Client (pane.py): `PLY_STICKY={grant,letter}`, `la_ntf_seen` capped-50
   dismissal store, sticky toasts shown uncapped ahead of the capped rest,
   ✕ marks seen, body click on `meta.go==='relay'` rows navigates
   tab→game + `goto_relay`; gold/aether inks on feed rows and toasts.
5. Engine `goto_relay` deep-link: refused mid-encounter, door rules
   respected (RELAY_LEVEL gate unless inbox_count>0), clears town
   sub-state, lands on the relay scene.
6. Tests: 3 new in `test_060_playing_toasts.py` (recipient isolation,
   since-cursor survival, no shared-cache leak) + 
   `test_wire_and_letter_emit_directed_notifications` in
   `test_social_api.py` (emitters + deep-link). Full worldd suite
   221 passed / 0 failed (17:48). Plugin suite at pre-existing baseline
   (8 known failures, 1375+ passed).
7. Vendor synced (`diff -rq` clean). Deploy rides phase-7.
