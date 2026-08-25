# 081 — early-game smoothing: eight small fixes for the first hours

## Problem

Eight independent frictions hit players in their first hours (levels 1–10).
Reported 2026-08-25; codebase evidence gathered same day. (A further item,
a "runner band" shop item, was dropped from scope by the user on
2026-08-25.)

1. **Rank-0 miss streaks feel terrible.** An untrained swing misses 25%
   of the time (`economy.TRAIN_MISS_PCT`, economy.py:782 — `25 − 2.5·rank`).
   At level 1 that regularly produces 2–3 misses in a row; the player has
   done nothing wrong and is punished with a full lost round each time.
2. **Wire transfers and letters are invisible.** `_fx_grant`
   (app/social.py:1282) and `_fx_send_letter` (app/social.py:1253) insert
   into `ascent_letters` and emit **no** happening, no pending event, no
   badge. The receiver discovers the money only by wandering into the
   Relay Office. The live-stream feed (`ascent_happenings`, 2 s peek poll
   at pane.py:701) has no per-player scope and no sticky/clickable toast.
3. **BUG — level-1 player huemorgan4 "couldn't collect" a grant.** After
   clicking *Collect the enclosed gold*, a red top banner said
   "That isn't one of the paths — pick a numbered row on the card"
   (core.py:704-708). Root cause below. The money was almost certainly
   credited on the FIRST click — verify in `ascent_ledger`
   (`kind='letter_gold'`, app/social.py:1276).
4. **Level-1 players don't know how to level.** The profile card shows an
   XP meter (render.py:886) but never says that leveling happens at the
   Guildhall and costs gold. Real numbers for 1→2: **24 XP + ◈ 60**
   (`xp_need(1)`, economy.py:1028; `levelup_gold(1)`, economy.py:1045 —
   NOT the 20 XP / 100 gold from the report; the box must print computed
   values, never hardcoded copy).
5. **Item parameters are unreachable on click/mobile.** Stats
   (ATK/DEF/durability) live only in the hover tooltip (`data-tiph`,
   render.py:1713-1748); the click popup shows name + actions only
   (`openMenu`, render.py:1942-1977), and on touch the tap tooltip is
   immediately killed by the menu (render.py:1846, 1944-1945). For the
   starter bow / gate armor the popup is a bare name + one grey line,
   though the data exists (bonus 5 / 7 in FORGE, economy.py:1987-2038).
6. **The pawn shop silently refuses the rusted dagger.** `rusted_shiv`
   and the other `BASIC_WEAPONS` (economy.py:2011-2012) are excluded
   from the offer list (core.py:2995) and a stale sell act falls through
   with no message (core.py:3067 → :3104) — the player never learns the
   broker won't buy basics. Adjacent glitch: price-0 gate kit is NOT in
   that set and gets a sell row offering ◈ 0 (core.py:2964-2967).
7. **"Hold" doesn't look like an action.** The equip row in the item
   popup is a button that reads as plain text (label authored at
   core.py:470-492; template render.py:1952-1957) — new players don't
   realize a pack weapon can be moved to hand.
8. **Monster types are opaque and the wrong weapon is a trap.** The
   encounter card explains the type triangle in three lines of verdict
   prose (combat.py:753-783, 924) a new player doesn't parse; worse,
   the pack is locked mid-encounter (core.py:375-384), so a player who
   walked in with a blade against a flyer (blade damage: zero,
   economy.py:715) can only flee or lose. Reported 2026-08-25
   (added mid-plan).

## Root cause (item 3, the bug)

`app/game.py` builds the response card **before** effects run:

```
game.py:202  scene = core.apply_choice(doc, option, text)   # card built
game.py:207  await social.execute_effects(...)              # gold moves HERE
game.py:212  doc["scene"] = scene.to_dict()                 # stale card stored
```

So the post-collect card is byte-identical to the pre-collect card: same
gold number, same "[◈ N enclosed]" line, same *Collect* row, same COLLECT
notice. The player naturally clicks Collect again. By then the letter is
`read=TRUE`, the rebuilt scene omits `collect` from `valid`
(core.py:681-684), and the click falls into the unknown-option refusal at
core.py:708 → red banner, card not swapped (pane.py:620-628), so the stale
button keeps inviting clicks. At level 1 it escalates to apparent theft:
the Relay is open only while `inbox_count > 0` (`RELAY_LEVEL = 2`,
economy.py:2122; gate at core.py:1376-1387), so after collection the door
re-locks and every signal says the money never arrived.

Contributing: the only test of this flow (`tests/test_social_api.py:90-124`)
forces both players to level 6 and asserts against the DB doc, not the
returned card — both failure modes are invisible to it.

## Emergency mitigation already taken

None needed in prod — no data is lost. Phase 1 step 1 verifies
huemorgan4's ledger and produces the evidence to tell the player their
gold was credited.

## Fix — seven phases

1. **phase-1 — relay collect: post-effect card + graceful stale clicks.**
   Rebuild the card after doc-mutating effects; friendly no-op for a stale
   `collect`; close the `LIMIT 8` letters vs unbounded `inbox_count` gap.
2. **phase-2 — beginner pity rule.** At level L ≤ 3, after L sequential
   misses the next swing is a guaranteed hit. Counter lives in
   `p["encounter"]`, constant in `economy.py`, guard at combat.py:2683.
3. **phase-3 — directed sticky feed notifications.** `scope='player'`
   rows in `ascent_happenings` for grant-received and letter-received;
   sticky toast (no 3 s timer) that navigates to the Relay on click and
   persists dismissal in localStorage.
4. **phase-4 — level-up explainer box.** Dismissable box in the profile
   column under the XP rail, level-1 only:
   `LEVEL UP — XP {xp}/{need} + ◈ {fee} — the Guildhall levels you up`.
5. **phase-5 — gear clarity.** (a) Item parameters (ATK/DEF/durability)
   render at the top of the click popup for gearmap slots AND pack rows,
   on mobile too; (b) the pawn broker names what he won't buy ("waves
   off the Rusted Shiv — gate steel and rusted basics are worth nothing
   to him, and never lost to you") and stops offering ◈ 0 for gate kit;
   (c) popup actions read as options: `[HOLD] — move to hand`.
6. **phase-6 — encounter type clarity + swap at the sizing-up.** The
   opener card swaps its verdict prose for a big-icon foe sheet
   (DEF / FLY / MAGIC RES / SPEED, each with the weapon that answers
   it), a dismissable "switch weapons from your pack" hint, and the
   pack unlocks for weapon swaps while the fight has not begun.
7. **phase-7 — dojo walkthrough + judgment.** All six scenarios in
   `worldd/tests/081-early-game-smoothing/`, results folder under
   `dojo/results/`, execution statuses appended per phase.

Order rationale: the bug first (trust), then the engine-only change,
then the two that touch schema/UI plumbing, then presentation, then the
encounter rework (largest surface last).

## Verification

- Per phase: targeted pytest listed in each phase PLAN, then the full
  worldd suite (`pytest worldd/tests`) and plugin suite
  (`pytest plugin-linear-ascent/tests`).
- Phase 7 dojo run is mandatory before this plan is reported complete:
  scenarios 01–06, evidence screenshots, PASS/FAIL table, regressions
  filed not fixed mid-run.
- Bug fix verified against the exact reproduction: level-1 receiver,
  grant, collect, card updates, second click is friendly, ledger row
  exists once.

## Operational notes

- **Two copies of the engine.** Source of truth is
  `plugin-linear-ascent/plugin_linear_ascent/`; the deploy reads
  `worldd/vendor/plugin_linear_ascent/` (gamepath.py:15-18). Every engine
  edit lands in the submodule first, then the vendor copy + parent
  pointer bump — same discipline as 080.
- No branches; commit straight to `main`. The workspace carries other
  agents' uncommitted WIP — stage only files this plan touches, by path.
- Migration in phase 3 is additive (new columns) — safe on a live DB.
- `numInstances: 1` is load-bearing for the feed head cache
  (social.py:842-846); phase 3 keeps the single write door
  (`add_happening`) so nothing changes there.
- Secret-pattern scan before every commit.

## Open decisions (flagged, defaults chosen so execution is not blocked)

1. **Pity above level 3** — default: none (mirrors
   `BEGINNER_MERCY_MAX_LEVEL = 3`, economy.py:2609). The request only
   specified levels 1–3.

Resolved 2026-08-25: the runner-band item was removed from scope by the
user; huemorgan4 needs no personal message — just the phase-1 fix.

## Appendix — other early-game step functions found during exploration
(not in scope for 081; candidates for 082)

1. **The Guildhall gold trap.** Full XP bar but < ◈ 60 → the player is
   told to come back richer, with no pointer to how. Consider waiving the
   L1 fee or printing "earn ◈ N more — kills on floor 1 pay ◈ X".
2. **XP surplus is destroyed on level-up** (`p["xp"] = 0`,
   engine/social.py:938-941). Losing overflow XP at L1–L3 punishes
   enthusiasm; consider carrying surplus for the first few levels.
3. **Miss copy references the School by name only** ("Improve at the
   School", combat.py:2687) — a level-1 player has no idea where that is.
   Make it a notice row or a click target.
4. **Unknown-option refusal is hostile and self-perpetuating.** On
   refusal the card is deliberately not swapped (pane.py:620-628), so a
   stale button stays clickable forever. Consider auto-refreshing the
   card on any unknown-option refusal — it would have halved the impact
   of the phase-1 bug class.
5. **No idempotency key on `/act`** (pane.py:622) — every double-click is
   a genuine second act. Cheap to add, removes a whole bug class.
6. **Grants resolve receivers by display name** with
   `ORDER BY updated_at DESC LIMIT 1` across tenants
   (app/social.py:1250) — a duplicate name silently pays the wrong
   player. Enforce unique names or key grants by player id.
7. **Free dawn full-heal is undiscoverable** (economy.py:2584) — new
   players pay the tent for what the sunrise gives free. One tip line.
8. **Beginner death-mercy (≤ L3) is unannounced** until it fires —
   telling new players early that death is forgiving lowers fear of the
   first fights (unlocks.py:360 already surfaces rules; add it there).
9. **Toasts last 3 s** (`PLY_TOAST_MS`, pane.py:1212) — fast readers
   only. Phase 3's sticky kind helps; consider 5 s for the rest.

## Execution status

Executed 2026-08-25, phases 1–8 in order, each verified before the next.
Engine work in submodule plugin-linear-ascent (vendor copy synced and
`diff -rq` clean at every commit), worldd changes committed to main.

- phase-1 — relay collect: post-effect card rebuild + friendly stale
  collect. huemorgan4's ledger verified: the gold WAS credited on the
  first click (bug was the stale card, not lost money).
- phase-2 — beginner pity rule (L ≤ 3, streak cap = level). Dojo
  numbers: L1 walker 60 rounds / 11 misses / max streak 1; L4 control
  60 / 12 / max streak 4 (cap is the pity rule, not RNG luck).
- phase-3 — directed sticky notifications (grant + letter), per-player
  happenings, click-to-Relay, dismissal persisted.
- phase-4 — level-up explainer box with computed numbers (24 XP + ◈ 60
  at L1), dismissable, server-side gone at L2.
- phase-5 — gear clarity: params in click popup (desktop + mobile),
  pawn waves-off line, no ◈ 0 rows, [HOLD] key row.
- phase-6 — foe sheet (DEF/FLY/MAGIC RES/SPEED + best-weapon lines),
  dismissable pack-swap hint, weapon swap open during the sizing-up.
- phase-7 — dojo run 0053: scenarios 01–05 PASS, 06 FAIL →
  **R-0053-1 filed** (foe sheet never rendered on the web pane).
- phase-8 — R-0053-1 root-caused and fixed: (1) `Scene.to_dict`/
  `from_dict` dropped `foe_sheet` (worldd round-trips every scene);
  (2) `_build_scene` rebuilt live encounters with `opener=False`, so
  reloads lost the opener. Fixed (d8dfae5, ca4b5a4), round-trip +
  rebuild tests added, scenario 06 re-walked: PASS.

Suites at completion: plugin 1395 passed / 1 skipped / 1 xfailed
(8 pre-existing failures, unchanged baseline); worldd 221 passed.
Results: `dojo/results/0053-081-early-game-smoothing-2026-08-25/`.

Deploy: engine 0.104.0 — see phase-7/phase-8 statuses; post-deploy
verification recorded below after the deploy completed.
