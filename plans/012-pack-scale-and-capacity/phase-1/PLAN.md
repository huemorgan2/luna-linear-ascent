# Phase 1 — render: 150% cells, flowing rows, capacity-aware grid

## Goal
Every pack/hand cell is 1.5× its current size with text unchanged; the
grid wraps to the card's full width; the grid draws exactly the pack's
capacity in cells (surplus cells marked over-capacity), never a padded
multiple of 6.

## Steps
1. `render.py`: `.slot` 60px, `.hcell .slot` 75px, `.picon` 42px,
   `.hcell .picon` 51px, `.slotgrid{display:flex;flex-wrap:wrap;gap:6px}`;
   narrow media: `.slot` min-width 48px, `.hcell .slot` 66px, `.picon`
   36px, `.slotgrid` flex. Drop `_PACK_COLS`/`_PACK_MIN_SLOTS`.
2. `_inventory_html`: cells = items + blanks up to `scene.pack_slots`
   (0 → items only, min 6 blanks-total for the empty look); items past
   capacity get class `over`; label `pack used/cap` (+ ` · over`).
3. `scene.py`: `pack_slots: int = 0` field, in `to_dict`/`from_dict`.
4. `.slot.over{border-color:RED;border-style:dashed}` + tip.

Inherits: both hosts (pane + chat card) share render.py CSS/HTML — one
edit lands in both.

## Verification
- `pytest tests/test_014_inventory_tooltips.py tests/test_012_pack.py`
- Render a scene with 8 items and pack_slots=6 → 8 `.slot.item`, 2 with
  `over`, label `pack 8/6 · over`; with 2 items → 6 slots (2 + 4 empty).

## Rollback
`git revert` the phase-1 commit in plugin-linear-ascent.

## Execution status

**Executed 2026-08-17. Complete.** Plugin commit `a984f50` (render.py,
scene.py). Measured in Chromium on the shipped card: `.slot` 60 px,
`.hcell .slot` 75, `.picon` 42; narrow 48/66/36; `.slotgrid` flex-wrap —
7 per row at 474 px, 10 at 875 px; label `pack used/cap`, surplus cells
`.slot.over` in RED. Text sizes unchanged (16 px). Worn armor/shoes stay in
the grid but do not count against capacity (found and fixed during the
first render pass). `tests/test_012_pack.py` render checks green.
