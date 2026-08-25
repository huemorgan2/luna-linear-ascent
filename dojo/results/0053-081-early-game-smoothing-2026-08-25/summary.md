# Dojo run 0053 — 081 early-game smoothing — 2026-08-25

## Environment
- worldd: local uvicorn on :8600 (`--reload`), commit 66e12ad
- engine: plugin-linear-ascent b3dc9e9 (vendor copy in sync)
- DB: Postgres 16 on :5434, database ascent_world
- Runner: Playwright headless Chromium (node 22), drivers in
  `luna/dojo/tests/081-early-game-smoothing/`
- Players seeded via web signup: DojoSendA, DojoRecvB, DojoByC,
  DojoCtrl4, DojoWalkF4, DojoPity1

## Results

| # | Scenario | Verdict | Evidence |
|---|----------|---------|----------|
| 01 | relay collect, level 1 | PASS | screenshots s01-1..5; SQL below |
| 02 | beginner pity misses | PASS | s02-rounds.txt; miss-card shots |
| 03 | directed toasts | PASS | screenshots s03-1..7; SQL below |
| 04 | level-up hint | PASS | screenshots s04-1..6; SQL below |
| 05 | gear clarity (desktop + mobile) | PASS | screenshots s05-* |
| 06 | encounter type clarity (desktop + mobile) | FAIL → re-walk PASS after phase-8 | R-0053-1; s06-arena-opener-no-foesheet.png; re-walk evidence below |

## Scenario 01 — PASS
- A (DojoSendA) wired ◈100 from B's Stone page; B's town card showed the
  COLLECT notice; the relay card read "from DojoSendA [◈ 90 enclosed]"
  with a Collect row. One click collected: card re-rendered with 0
  letters, the clerk's counting note, no Collect row, no red banner.
  Send→collected 4174 ms.
- Stale poke (same option again) → calm clerk line ("that gold is
  already in your purse"), no error banner.
- SQL: exactly one `grant_in +90` + one `letter_gold +90` for B, one
  `grant_out -100` for A; letter row `read=t, gold=0`; B gold 140 =
  50 + 90. Vault burn 10% (100 sent → 90 received) as designed.

## Scenario 02 — PASS
- DojoPity1 (level 1): 60 recorded attack rounds, 11 misses,
  maxMissStreak = 1 — misses never stacked past the level, and misses
  DID occur (the cap is doing the work, not a rigged hit table).
- DojoCtrl4 (level 4): 60 rounds, 12 misses, maxMissStreak = 4
  (one MMMM run) — streaks longer than 1 exist at level 4, proving the
  level-1 ceiling is the pity mechanic, not global RNG luck. 4 ≤ level,
  so the level-N cap holds for the control too.
- Full sequences in s02-rounds.txt. Rounds classified on the RAW act
  fragment (`ATTACK MISSED` rides `data-arena`), 067-aware.
- Driver note: both walkers needed SQL energy top-ups
  (`energy_val = 24.0`) between hunts — 60+ rounds vs the 1-per-45-min
  regen; precondition management, not gameplay.

## Scenario 03 — PASS
- Grant toast on B: "◈ 90 wired from DojoSendA — collect at the Relay
  Office" — sticky ≥30 s, still present after idle; body click switched
  to the game tab and walked B to the Relay Office; toast gone after
  the click.
- Letter: A composed on the Stone (pf_msg ask form) — "Meet me at the
  gate at dawn." Letter toast on B in 2701 ms: "A letter from DojoSendA
  waits at the Relay Office". ✕ wrote `la_ntf_seen=[8795]`; after
  reload the letter toast stayed gone. DB: ascent_letters 117833,
  happening 8795 (kind=letter, to_player=dojorecvb).
- Rapid pair: two wires 200 ms apart (A 14:38:55.739, F4 14:38:55.958,
  ledger 13812/13814). Fresh B context surfaced BOTH senders' toasts
  stacked (3×A + 1×F4) — no cap, no coalescing.
- Bystander C: no directed rows in C's feed, no toasts, no leak of
  B-directed lines. Undismissed mail resurfacing on reload is the
  designed exemption of directed rows from the since-cursor.
- Note: the scenario's ◈50 wire is below the pane's minimum row
  (pf_pay_100); walked with ◈100. Noted, not a regression.
- Driver note: the first run's bogus `pf_msg_send` act (before the ask
  mechanism was understood) fell through to a repeat pay and sent a
  real extra ◈100 wire (ledger 13783, 14:37:40) — driver artifact, not
  a game bug; the letter step was re-walked with the real ask submit.

## Scenario 04 — PASS
- Box under the XP rail: "LEVEL UP — XP 2/24 + ◈ 60 — the Guildhall
  levels you up" — live xp, real economy numbers (24/60, not 20/100).
  Fragment carries exactly one `.lvlhint`.
- Survived a card re-render; ✕ removed it; stayed gone across an act
  and a reload (`la_tip_levelup=1`).
- Guildhall quoted the SAME numbers: "your bar is full and the fee is
  in hand: LEVEL 2 for 60". `guild_train` leveled: ledger
  `levelup -60`, level 2, HP 96 = player_max_hp(2, armor 7) → full.
- Fresh browser context at level 2: `.lvlhint` count 0 (server-side
  gone).
- Vendor-copy shell: `xp_need(1) == 24`, `levelup_gold(1) == 60`.

## Scenario 05 — PASS (desktop AND mobile 390×844 touch)
- Every stat-bearing popup opens with name + parameters: Rusted Sword
  "ATK 5 · DURABILITY 1,300/1,300", Gate-Issue Jerkin "DEF 7 ·
  DURABILITY ∞", Basic Bow "ATK 5", Gate-Issue Buckler "DEF 5", Medgel
  "HEALS 25" (effect line, no broken row). Same on tap (mobile) — the
  numbers ride `data-params` into the popup, no hover needed. No
  overflow on 390 px.
- HOLD reads as a bracketed key row (`.key` "HOLD" + hint "swap out the
  Rusted Sword …") and works: bow moved to hand, sword to the pack;
  reverse swap on mobile also worked. No duplication (1 of each in
  inventory after).
- Pawn: waves-off line names the refused items ("The broker waves off
  the Gate-Issue Buckler and Rusted Sword — gate steel and rusted
  basics are worth nothing to him, and never lost to you"); zero ◈ 0
  rows; only sellable row was the medgel.
- Control sale: quote "Medgel ×1 — offers 12" (51% day rate on 25);
  paid +12; ledger: exactly one `pawn +12 medgel` row, zero rows for
  the refused items.

## Scenario 06 — FAIL (regression R-0053-1)
- **The foe sheet never renders on the web pane — the surface real
  players use.** Root cause (tracked, reproduced): `Scene.to_dict()` /
  `Scene.from_dict()` (engine/scene.py:381/440) do not carry the new
  `foe_sheet` field. worldd's `/play/api/act` and `/play/api/pane/scene`
  round-trip every scene through that serialization
  (app/webplay.py `_card` → `Scene.from_dict`), so `foe_sheet` arrives
  as None and the renderer draws nothing — grid AND dismissable hint.
  Evidence: s06-arena-opener-no-foesheet.png (fresh floor-1 opener,
  `data-arena phase:"opener"` present, no `.foesheet`, no `.foehint`);
  three driver runs found zero sheets across floors 1–4; a direct
  vendor-code repro (fight_scene → render_scene_fragment, no dict
  round-trip) DOES draw the sheet on the identical opener.
- Not the arena: `arena_live` is False on opener-phase cards
  (render.py:2528), so the "suppressed in arena_live" guard never
  fires on openers — the loss is purely the serialization gap.
- Plugin tests pass because they render the Scene object directly:
  `tests/test_081_foe_sheet.py` — 10 passed (payload per type,
  fragment draws sheet + hint, foehint_close). The dict round-trip has
  no test — that is the hole the dojo run caught.
- **Verdict prose IS gone from the opener body** (per design): the old
  "it CANNOT reach you…/your steel can't swing…" lines now live only
  inside the [i] dossier tooltip attribute, not the card body.
- **Swap window works** (walked live via API on a floor-1 goblin
  opener): `pack` row present at sizing-up; `wear_basic_bow` accepted
  (weapon changed, card rebuilt, still at range); after one attack the
  swap-back was refused with the reason line ("Not mid-fight — you
  don't re-rig your hands with teeth in your face") and the weapon
  stayed put (DB: gear.weapon=basic_bow, encounter.attacked=true).
- `foehint_close` accepted server-side (doc foehint_done=true) — but
  the box it dismisses never renders on arena floors.
- Type-collection, hint-persistence, and mobile 2×2 grid checkpoints
  were unwalkable with no sheet on any reachable floor.

### Scenario 06 — phase-8 re-walk: PASS (all checkpoints)
Re-walked same day after the phase-8 fixes (engine d8dfae5 serialization
+ ca4b5a4 rebuild-keeps-opener), vendor in sync, same local env.
- **Sheet renders on the pane.** Fresh floor-1 opener via `/play/api/act`
  carries `.foesheet` + `.foehint`; plain foe shows DEF / SPEED /
  NO SIGN ("every weapon bites full") with icons, 2×2 grid, You-line
  with the held weapon (s06-desktop-opener-foesheet.png).
- **All four type pairings collected live:**
  plain — DEF n, SPEED n, "NO SIGN — every weapon bites full";
  armoured (floor 2, shellback tortoise) — "DEF 5 :: best weapon:
  magic", "SPEED 3 :: you can outpace it", no NO SIGN cell
  (s06-desktop-type-armoured.png);
  magic_resist (floor 3) — "MAGIC RES 98% :: best: swords"
  (s06-desktop-type-magic_resist.png);
  fly (floor 4, lamp newt) — "DEF 5 :: best weapon: magic",
  "FLY — YES :: best: bows and magic", "SPEED 7 :: closes distance
  fast" (s06-mobile-opener.png).
- **Hint dismissal persists:** `foehint_close` → hint gone from the
  rebuilt card, absent on the next opener and after a full reload
  (doc `foehint_done=true`); the sheet itself stays.
- **Reload keeps the opener (fix #2):** a fresh browser load mid
  sizing-up re-renders the full opener — sheet present, cells intact
  (`{"sheet":true,"cells":["DEF 5","SPEED 3"],"hint":false}`),
  s06-desktop-type-armoured.png is that fresh load.
- **Swap window re-verified live:** `wear_basic_bow` accepted at range;
  after the first attack a swap is refused with the re-rig line and the
  DB weapon is unchanged.
- **Round cards stay clean:** post-attack fragments carry no
  `.foesheet`; verdict prose lives only in the [i] dossier attribute.
- **Mobile 390×844:** grid is 2 columns × 2 rows, no horizontal
  scroll, no `<img>` tags (icon glyphs inline).
- Plugin `test_081_foe_sheet.py` now 12 passed — includes the dict
  round-trip test and the reload-keeps-opener test the original gap
  slipped through.

## Regressions filed
- **R-0053-1** — 081 phase-6 foe sheet (grid + swap hint) never shows
  on the web pane: `Scene.to_dict`/`from_dict` drop the `foe_sheet`
  field, and worldd's pane round-trips every scene through them.
  Filed from this run; fixed in phase-8 (engine d8dfae5: serialize the
  field + round-trip test; ca4b5a4: scene rebuild keeps the opener via
  `opener=combat.swap_window(p)` — second cause found in the re-walk),
  re-verified by re-walking scenario 06 same day: PASS (addendum above).

## Method notes
- 067 arena-live round cards keep round prose OFF the DOM (it rides the
  `data-arena` attribute); s02 classifies rounds on the RAW fragment
  string, validated against `s.to_text()` truth over 120 engine rounds.
- Bulk loops drive `window.__laAct` directly (typewriter reveal makes
  real clicks impractical); s01's clicks are real buttons.
