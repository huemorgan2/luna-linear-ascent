# Phase 1 — the faces

## Goal

The homepage trio shows: WARRIOR = a woman in plate (new art), ARCHER =
the most armoured elf we already have, SORCERER = a massive giant dwarf
wizard with a staff who stands ~2 heads taller and visibly wider than
the other two. The game's `wick` portrait (lodge NPC, and the image the
user calls "the game image") becomes the same wizard at 100×200.
Measurable: three files exist under `worldd/static/site/art/`, the trio
markup references them, and
`plugin_linear_ascent/content/art/portraits/portrait_wick_100x200.png`
has new content (hash changes).

## Steps

1. Source `LUNA_GEMINI_API_KEY` from `~/Documents/Luna/luna/.env`
   (never printed).
2. Extend the 030 pipeline in a one-off scratchpad script that imports
   `plugin-linear-ascent/tools/generate_030_art.py` helpers (PORTRAIT_STYLE,
   `to_1bit`, `bits_to_png`, providers) — no edits to the parallel
   session's dirty tools files. Jobs:
   - `portrait_maiden` — a woman climber in full plate, sword, at
     100×200 → site art (`portrait_maiden_100x200.png`).
   - `portrait_wick_giant` — colossal ancient dwarf archwizard, huge
     knotted staff, vast beard, runed robes; one raw paint, dithered
     twice: 140×260 for the site
     (`portrait_wick_giant_140x260.png`) and 100×200 to REPLACE the
     plugin's `portrait_wick_100x200.png`.
3. Copy `plugin .../portrait_elf_aegis_100x200.png` (the most armoured
   elf wardrobe, no sword in hand) → `worldd/static/site/art/`.
4. Rewire `index.html` `.trio`: plate→maiden, elf_leather→elf_aegis,
   wick→wick_giant with `width=140 height=260`; CSS `.trio` gets
   `align-items:flex-end` so the giant towers instead of stretching.
5. Inspect all three renders (contact sheet) — regenerate any paint
   where the figure breaks the style law (outlines, glow, cropped head)
   or the woman/giant/staff read is ambiguous.

Inheritance: the plugin change rides Phase 4's vendor run into worldd's
vendored engine; new tenants/installs inherit via the marketplace zip
when publish recovers.

## Verification

- `sips -g pixelWidth -g pixelHeight` (or PIL) confirms 100×200,
  100×200, 140×260.
- `git diff --stat` shows `portrait_wick_100x200.png` changed in the
  plugin repo only (no other plugin files).
- Contact-sheet eyeball: woman reads as a woman, giant reads as a
  dwarf wizard with a staff and fills 140×260.

## Rollback

`git checkout -- plugin_linear_ascent/content/art/portraits/portrait_wick_100x200.png`
in the plugin repo; delete the three new site PNGs; revert the
index.html/site.css hunks (all in one phase commit → `git revert`).

## Execution status

_(appended after execution)_
