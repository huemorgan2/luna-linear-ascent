# 012 — The pack: 150% cells, free-flowing rows, and a size you can buy

## Problem

Reported 2026-08-17 (screenshot of the PACK block on the player card):

1. **The cells are small.** Slot squares are 40 px (hand cells 50 px,
   glyph 28/34 px). Wanted: every box 150% larger; the text (labels
   `in hand / held / shield`, the ×count) stays at its current size.
2. **The grid is locked to 6 columns.** `.slotgrid` is
   `grid-template-columns:repeat(6,40px)` and `_inventory_html` pads
   the cell list to a multiple of 6 (min 12). Wanted: cells flow to the
   right edge of the card — more than 6 per row when the width allows.
3. **The pack has no size.** `p["inventory"]` grows without bound; the
   grid draws as many blanks as it needs. Wanted: a **basic pack of 6
   slots**, and larger packs sold at the Forge in tiers of **+3 slots**,
   unlocking at **level 3, 6, 9, 12** (→ 9, 12, 15, 18 slots).

## Root cause

- Render: fixed column count + padding math in
  `plugin_linear_ascent/render.py` (`_PACK_COLS`, `_PACK_MIN_SLOTS`,
  `.slotgrid`, `.slot`, `.picon` and the narrow-media overrides).
- Capacity: no field, no counter, no shop row. Every gain writes
  `p["inventory"][slug] += n` directly (~100 sites across engine/*).

## Design decisions (stated, not asked)

- **A slot is a stack.** Capacity counts distinct slugs in
  `p["inventory"]` with count > 0. Stacking onto an existing slug never
  needs room. Equipped gear, held weapons and open carry slots are the
  hand row — not pack slots.
- **State:** `p["pack_slots"]`, default 6, self-healed in
  `state.migrate` like `slots`.
- **Enforcement at the counter, never at the loot.** Shops (Forge,
  Arcanum, Medlab, relic rows, basic-weapon rows) refuse a purchase
  that would open a NEW stack in a full pack — before gold moves — with
  a shard note + refusal that names `used/cap` and points at the Forge.
  Gear buys whose old piece would go to the pack are refused the same
  way. Loot, rewards, unequip-to-pack, death returns and every other
  non-shop gain still land: nothing the player earned is dropped by a
  bookkeeping rule. A pack over capacity renders the surplus cells
  in RED dashed border and the label reads `pack 7/6 · over`; shops
  stay closed to new stacks until it is back under.
- **Tiers** (economy.py `PACK_TIERS`): `(level 3 → 9 slots, ◈ 40)`,
  `(6 → 12, ◈ 120)`, `(9 → 15, ◈ 300)`, `(12 → 18, ◈ 600)`. Sequential.
  The Forge shows one row: the NEXT tier, buyable or LOCKED with its
  level (the 049.2 lesson: a locked row that names its gate, never a
  bare hint). Each tier is an `Unlock` in `unlocks.py` so the
  "what opens when" legend lists them.
- **Wire:** `Scene.pack_slots: int` (0 = unlimited/legacy, so an old
  render half draws exactly what it drew before). Renderer draws
  `max(pack_slots, len(rest))` cells.
- **Scale:** slot 40→60, hand slot 50→75, glyph 28→42, hand glyph
  34→51, gap 4→6. Narrow media: min 32→48, hand 44→66, glyph 24→36.
  `.hlab`, `.invlbl`, `.slot .ct` untouched.

## Fix — phases

- **Phase 1** — render: scale + flow + capacity-aware grid.
- **Phase 2** — engine: `pack_slots` state, `pack_cap/pack_used/
  pack_room` helpers, shop refusals, Forge rows, unlocks legend, tests.
- **Phase 3** — release: bump 0.87.0, vendor into worldd, tests, push,
  deploy, marketplace publish, dojo walkthrough.

## Verification

- `../worldd/.venv/bin/python -m pytest tests/ -q` in the plugin: new
  `tests/test_012_pack.py` green, suite unchanged otherwise.
- Rendered card: `.slot` 60×60, `.hcell .slot` 75×75, `.slotgrid` is
  `flex-wrap`, 7+ cells in one row at ≥ 520 px card width.
- Prod `/health` → `game: 0.87.0`; marketplace index 0.87.0 sha256
  matches the local zip.
- Dojo scenario `luna/dojo/tests/pack-capacity/scenario.md`, results
  folder under `dojo/results/`.

## Operational notes

- No DB migration: `pack_slots` lives in the player doc (JSON), healed
  on load.
- Rollback per phase in the phase plans; a full rollback is
  `git revert` of the plugin commits + re-vendor + deploy.
