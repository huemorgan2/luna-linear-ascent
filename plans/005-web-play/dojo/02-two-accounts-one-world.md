# 02 — A signs up, B signs up, A comes back: nothing bleeds

## Preconditions

- Production live. Two fresh usernames `webprobeA-<hex>`,
  `webprobeB-<hex>`.

## Scenario

1. Browser context 1: sign up A, play to ROOTHOLLOW as elf archer,
   enter floor 1, win one hunt. Note A's HP/XP/gold and ident line.
   Screenshot.
2. Browser context 2 (fully separate cookies): sign up B, play to
   ROOTHOLLOW as dwarf warrior. Note B's ident. Screenshot.
3. Context 2: open SCORE. Both A and B appear.
4. Context 1: log out. Log back in as A **from a third, brand-new
   browser context** (new device simulation).
5. Read A's scene and profile. Screenshot.

## Expected behavior

- A resumes exactly where A left off — same floor state, same
  meters, same pack — from a different browser.
- B's ident never shows A's name, race, class or meters, and vice
  versa.
- The leaderboard lists both, with the numbers each just earned.

## Fail conditions

- A returning sees the intro again (doc lost) or ANY of B's state
  (tenant/player keying broken — this is the catastrophic one).
- Session from context 1 still acts after logout.
- Leaderboard missing either player, or double-listing one.

## Verify

- DB: two rows in `ascent_players` for tenant `web`, players
  `<a>`/`<b>`; docs differ in race/class as chosen.
- A's pre-logout and post-relogin `/play/api/pane/scene` responses
  agree on hp/xp/gold.
