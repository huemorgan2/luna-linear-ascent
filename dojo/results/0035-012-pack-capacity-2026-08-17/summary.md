# Dojo run 0035 — 012 the pack: 150% cells, flowing rows, bought capacity (2026-08-17)

**Scenario:** `luna/dojo/tests/pack-capacity/scenario.md`
**Release under test:** game 0.87.0 — plugin `0527f47` (012 code `a984f50`),
root vendor `d214780`, Render deploy `dep-da1js87qj5pc73d7iji0` (live),
marketplace index 0.87.0 sha256 `e3efc4357361b6c6…` == local zip.

## Environment — hybrid run (deviation, declared)

- **Production, API probes over HMAC** (`/v1/enroll` throwaway tenant
  `dojo012-4b3a1879`, UA `dojo-probe/012`; `dojo012_probe.py`, scratchpad):
  a fresh climber walked through the intro to the square, then the Forge.
  Level 3 / six stacks are not reachable for a fresh prod character in one
  session (no admin creds; XP grind ≫ energy), so the purchase and
  refusal steps ran locally.
- **Local, the shipped code** (plugin `0527f47` == vendored `d214780`):
  the engine walked through the real `core.apply_choice` path (the same
  function `/v1/act` calls) with preconditions set on the doc (level 3,
  gold, six stacks — documented setup, not a tested flow); every card
  rendered by `render.render_scene` (the chat-card host) and measured in
  real Chromium (Playwright) at 380 / 720 / 1100 px. `walk.json` and
  `measurements.json` hold the raw numbers.

## Verdicts

| # | Check | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | Squares 1.5×, text unchanged | PASS | `.slot` 60 px, `.hcell .slot` 75, `.picon` 42 (was 40/50/28); `.invlbl`/`.hlab` font-size 16px both before and after; `w2_over_720.png` |
| 2 | Narrow media scaled too | PASS | 380 px viewport: slot 48, hand 66, glyph 36; `w2_over_380.png` |
| 3 | Rows flow to the edge, no 6-column lock | PASS | `.slotgrid` display `flex`, `flex-wrap: wrap`; 7 per row at 474 px, 6 at 441, 4 at 252, **10 per row at 875 px** (`w3_after_pack9_1100.png`) |
| 4 | Grid draws capacity, label `used/cap` | PASS | 6/6 → 6 squares + worn armor; after buy `pack 9/9` with 10 cells (9 + armor); prod fresh char: wire `pack_slots: 6` |
| 5 | Prod: fresh character sees the locked row | PASS | Forge option `buy_pack` label `Larger pack — 9 slots`, hint `🔒 level 3 · ◈ 40`, `locked: true` |
| 6 | Prod: click at level 1 refuses with the gate | PASS | refusal `Can't buy this — it opens at level 3 (you: 1)`, note "The 9-slot pack opens at level 3 — you're level 1." |
| 7 | Shop refuses a new kind in a full pack, no gold moves | PASS | Forge `buy_ratskin_round` at 7/6 (worn plank shield would need a slot): `Can't buy this — pack full (7/6 slots)`, gold unchanged, shield still `plank_shield` |
| 8 | Stacking onto an owned kind allowed when full | PASS | Medlab `buy_medgel` at 7/6: no refusal, medgel 4 → 5, ◈ 25 paid |
| 9 | Loot over capacity lands and shows red | PASS | two kinds added outside a shop → used 9, cap 6, wire `pack_slots` 6; label `pack 9/6 · over`; 3 `.slot.over` cells with border `rgb(242,101,65)` (RED); `w2_over_720.png` |
| 10 | Buy the 9-slot pack at level 3 | PASS | `+ a larger pack — 9 slots now (was 6). The straps take the weight.`; cap 9; ◈ 40 deducted; `w3_after_pack9_720.png` |
| 11 | Next tier shows locked at level 6 | PASS | row `Larger pack — 12 slots` hint `🔒 level 6 · ◈ 120`, locked; `w1_forge_row_720.png` (the level-3 buyable row) |
| 12 | Tiers in order, gates and prices | PASS (coded) | `tests/test_012_pack.py::test_forge_sells_tiers_in_order` — 9/12/15/18 for ◈ 40/120/300/600 at level 12; `test_second_tier_gated_at_level_6`; 16/16 green |
| 13 | Old docs heal to 6 | PASS (coded) | `test_old_doc_without_key_heals_to_six` |
| 14 | Both halves live | PASS | prod `/health` → `game 0.87.0`; marketplace 0.87.0 sha256 match |

**Overall: PASS — 14/14** (12–13 by coded tests on the shipped code, the rest walked).

## Observations (not regressions)

- In the chat card (≈ 440–475 px content width) the 60 px squares fit
  6–7 per row; the "more than 6" only shows in wider hosts (the pane at
  ≥ 520 px). Flow is unconditional; the host width decides.
- Setting up "six stacks" locally also parked the starting rusted sword
  in the pack, so the walk's refusal states read 7/6 rather than 6/6 —
  same rule, one more stack.
- Prod probe tenant `dojo012-4b3a1879` left in place (throwaway).

## Files
`w1_forge_row_720.png` (Forge card, level 3, buyable pack row),
`w2_over_720.png`, `w2_over_380.png` (over-capacity grid, red cells),
`w3_after_pack9_720.png`, `w3_after_pack9_1100.png` (9-slot pack, 10 per row),
`walk.json`, `measurements.json`.
