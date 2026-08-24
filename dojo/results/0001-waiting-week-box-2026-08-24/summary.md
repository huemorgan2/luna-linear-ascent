# Dojo run — waiting-week-box (plan 070)

- Date: 2026-08-24
- worldd: local, port 8778, `db:true`, live plugin source (`ASCENT_GAME_PATH=plugin-linear-ascent`)
- Plugin: game **0.98.0** working tree at commit `4513270` (`doors = {nt.get("opt") ... if nt.get("opt")}` guard present)
- DB: `postgresql://ascent:ascent@localhost:5434/ascent_world` (real local world, 610 players)
- Runner: `luna/dojo/tests/waiting-week-box/walkthrough.mjs` (Playwright, headless chromium)

## Result: 16/16 checks PASS

| # | Check | Verdict |
|---|-------|---------|
| S1 | signup + seed pending 3 | PASS |
| S2 | waiting-for-you on town card | PASS |
| S2 | one nested week box (single rail) | PASS |
| S2 | header plain English, no slang | PASS |
| S2 | four rows: gold / extra XP / repair / luck | PASS |
| S2 | copy has no engine slang | PASS |
| S2 | one complete square (solid 1px cyan, radius 0) | PASS |
| S3 | Vault has no prize rows | PASS |
| S3 | Vault still has deposit / back | PASS |
| S4 | Extra XP row clickable on town | PASS |
| S5 | box gone after the pick | PASS |
| S5 | receipt names extra experience | PASS |
| S6 | 390px: one complete square, four rows | PASS |
| V | no console errors | PASS |

## Screenshots (read, not just captured)
- `01-town-weekbox.png` — WAITING FOR YOU; header "You have a reward from last week. Choose one. You only get one."; one continuous cyan rectangle around the `1 2 3 4` rail; labels outside (Gold ◈285, Extra XP ✦35, Free repair, Luck charm).
- `02-vault-no-prizes.png` — Vault shows deposit/interest copy, `carried ◈200`, `strongbox — this week: 0 kills · 0 keeps · 0 floors`. No prize rows.
- `03-receipt-extra-xp.png` — box gone; card reads "You chose extra experience. Your next fights will give more XP until ✦ 35 runs out."
- `04-town-weekbox-390.png` — one complete rectangle at 390px; labels wrap; numbers stay inside the rail.

## DB / state truth (engine, level 6)
- `strongbox_aether(6)` = 35 → matches the `✦ 35` shown in-game.
- `rested`: 0 → 35 (**+35**). `gold`: 200 → 200 (**unchanged** — Extra XP is an XP bonus, not gold, not speed).
- `strongbox.pending` → `None` after the pick.

## Notes / findings
- First run against a mid-reconciliation working-tree snapshot hit `KeyError: 'opt'` in
  `core.apply_choice` (`doors = {nt["opt"] ...}`) because the 070 `weekpick` notice has no
  top-level `opt`. The committed code (`4513270`) already fixes this with `.get("opt")` and a
  filter; the clean re-run is 16/16. Regression guard worth keeping: a pytest that calls
  `apply_choice` from a notice room while a `weekpick` is pending.
