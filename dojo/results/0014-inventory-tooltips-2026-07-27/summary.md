# 0014 — inventory pack strip + [i] instant tooltips · 2026-07-27

Scenario: `plugin-linear-ascent/tests/014-inventory-tooltips/scenario-1-pack-and-glyphs.md`
Stack: local worldd (8600, fresh vendor) + QA Luna (8765, tenant qa007,
remote mode) + Playwright at 1600×1000.

## Findings — PASS

- **Pack strip** renders under the meters on every playing scene:
  equipped Rusted Shiv (sword icon, bright) then Medgel (vial icon,
  dim) with ×count. Icons are crisp 32×32 single-color 1-bit pixel art
  (01-pane-game.png).
- **[i] glyphs** on every option: fight card 5/5, kill card 4/4, the
  square 11/11, Apothecary 7/7 (buy_ prefix tips resolve). Tooltip
  appears INSTANTLY on hover, violet-bordered, positioned by the glyph
  (02, 04).
- **Tip content**: Stand explains the halved round + guard hold; the
  Forge tip explains ATK/DEF → higher floors → more gold/XP; Medgel tip
  carries +25 HP and the "more hunts per day" purpose (02, 03, 04).
- **[i] click safety**: clicking Attack's [i] mid-fight changed
  nothing — boar HP stayed 6/18. Verified by DOM read.
- **Live purchase**: buy_medgel at the Apothecary — gold 1,519→1,494
  (−25), strip updates to "Medgel ×2" in the same scene swap.
- **use_ path (new)**: at Lamplit Steading with HP 74/76, the camp
  offered `Use a Medgel · +25 HP · 2 left`; using it healed to 76/76
  (capped, "+ 2 HP — the medgel does its work."), count → 1, option
  disappeared at full HP.
- **Chat turn**: "hunt the wilds once" → Luna acknowledged pane play,
  called ascent_choose, pane refreshed to the new fight with glyphs +
  strip intact (06). Chip damage from 013 still landing (HP 76→75
  through armor).
- **Remote mode**: all of the above through worldd (vendored engine
  serves scene.inventory over the wire).

## Notes

- Chat "cards" in this conversation are collapsed awareness texts (the
  pane is the display since 009) — the legacy render_scene document
  still ships the tipbox + strip (unit-tested).
- 7 pre-existing worldd test failures in test_factions.py belong to the
  parallel 015-faction-desk work-in-progress (uncommitted app changes),
  unrelated to 014.
