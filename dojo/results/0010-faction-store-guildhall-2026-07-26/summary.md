# 0010 · Faction store & Guildhall — live dojo run (2026-07-26)

Scenario 2 (faction life at the Guildhall) played live against the QA Luna
(qa007 tenant → local worldd :8600, migration 007 applied). Player A "Dojo"
(steward, browser); Player B "Brynn" (tenant-a, scripted HMAC driver).

## What passed

- **Hall list**: empty hall shows "No banners fly yet. Yours could be the
  first." + "Raise a new banner ◈ 500"; after founding, the hall lists
  `Join Night Ledger — join ◈ 25 · dues ◈ 5/wk` with the purse up front.
- **Founding flow** (name → sigil → join fee → dues): typed steps land in
  chat, sigil is an 8-way option pick, ◈500 charged exactly once
  (2,000 → 1,500). worldd row: `banner=twin_moons, join_fee=25,
  weekly_dues=5, treasury=0`.
- **Join**: Brynn pays ◈25 (242 → 217), store 0 → 25, `join_fee` ledger row.
- **Donate**: typed prompt, ◈30 carried → store 55, `donation` ledger row,
  card names the new balance ("◈ 55 now").
- **Enter the week**: steward-only option; ◈10 (5 × 2 members) left the
  store (55 → 45); week row `entered=true, entry_paid=10, kind=climb,
  target=800`; panel shows "374/800 — entered, on pace for ×0.00".
- **Kick picker**: steward-only, lists members but never self, shows
  attendance pips. (Cancelled — kept the faction intact.)
- **Community tab = news board only**: THIS WEEK (challenge + entry note),
  HALL OF BANNERS (wins), MOST CLIMBERS / RICHEST STORE / HIGHEST BLADES
  with 1-bit sigils, THE WIRE ticker. No join/create/manage controls.
- **Crier tie-in**: the town square news announces "This week the Ascent
  demands a CLIMB — banners enter at the Guildhall (◈ 5 a head, from the
  store)".
- Every store movement has a ledger row (join_fee / donation / entry).

## Bugs found and fixed during the run

1. **Typed replies never reached the game.** Typing "Night Ledger" at the
   name prompt made Luna say "I don't have a Night Ledger in my context".
   Nothing told the sidekick a scene was waiting for typed text.
   Fix: `Scene.awaits_text` (engine) — set on naming, founding fee/dues,
   donation, and letter scenes; surfaces in `to_text()`, the awareness
   notice ("IMPORTANT: the game is waiting for the player to TYPE…, pass
   it straight through, no confirmation question"), and the ascent_choose
   tool description. After the fix "25" and "5" passed straight through.
2. **Pane never refreshed after chat-driven acts.** `scene_id` was declared
   but never stamped anywhere, so `/pane/peek` always compared empty
   strings. Fix: the engine stamps `scene_id = s<act_seq>` (a per-doc act
   counter) in `current_scene`/`apply_choice`; acts bump it, reads reuse
   it. Verified live: after a chat-typed act the pane refreshed within the
   15s poll.

## Environment note (not a code bug)

Restarting `luna serve` without the QA env
(`LUNA_ASCENT_WORLDD_URL/TENANT/SHARED_SECRET`) reconnects the plugin to
production worldd via vault credentials. The QA launch env is mandatory.

## Cosmetic findings (not fixed)

- The join act's own response still renders the pre-join hall list (world
  block is injected before effects execute); the very next read shows the
  member panel. Harmless but slightly off for API clients — the pane
  refresh hides it.
- "on pace for ×0.00 of the prize" is correct (attendance < 50%) but could
  read as broken early in the week.

## Screenshots

1. `01-guildhall-empty-hall.png` — hall card, 1-bit banner, raise option
2. `02-sigil-pick.png` — 8 sigil options for Night Ledger
3. `03-founded-member-panel.png` — STORE ◈0 · dues ◈5/week · join ◈25
4. `04-entered-week.png` — CLIMB entered, store 55 → 45, kick option
5. `05-community-board.png` — the news board, rankings + sigils
6. `06-community-wire.png` — the wire ticker
