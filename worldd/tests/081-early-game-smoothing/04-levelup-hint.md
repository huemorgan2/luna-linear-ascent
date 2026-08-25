# 04 — the level-1 profile explains how to level up

## Preconditions
- Fresh level-1 player with some XP earned (0 < xp < 24), enough gold to
  eventually level (≥ ◈ 60 + fight earnings).

## Scenario
1. Open any scene card and look at the profile block under the XP rail.
   Screenshot.
2. Fight once (the card re-renders). Look again.
3. Click the box's ✕. Act once more, then reload the page.
4. Earn to a full XP bar, go to the Guildhall, and level up (pay the
   fee). Return to a normal card, and also open the game in a fresh
   browser context for the same account.

## Expected behavior
- Step 1: a small box directly under the XP meter reading
  `LEVEL UP — XP {xp}/24 + ◈ 60 — the Guildhall levels you up`, with
  live xp matching the meter above it. Numbers are the real economy
  values (24 / 60), not the folklore 20 / 100.
- Step 2: the box survives card re-renders.
- Step 3: after ✕ it is gone and stays gone across acts and reload.
- Step 4: the Guildhall drillmaster quotes the SAME numbers; after
  leveling, the box is absent even in a fresh browser (server-side gone
  at level 2), and the level-up itself works: gold −60, level 2, full
  HP.

## Fail conditions
- Hardcoded or mismatched numbers anywhere (box vs XP meter vs
  drillmaster).
- The box reappearing after dismissal, or dismissal hiding anything
  other than the box.
- The box rendering for level ≥ 2 players, or on other players'
  profiles (`player_avatar_html` must not include it).
- Layout breakage of the pcol/pip rows on narrow widths.

## Verify
- Fragment HTML for a level-1 act response contains one `.lvlhint`; a
  level-2 response contains none.
- `xp_need(1) == 24`, `levelup_gold(1) == 60` in a shell against the
  deployed vendor copy (guards against economy drift making the copy
  wrong later — the box must track the functions, not constants).
