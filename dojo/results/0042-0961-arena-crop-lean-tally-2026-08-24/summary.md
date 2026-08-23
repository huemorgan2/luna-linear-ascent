# Dojo run 0042 — 0.96.1: true-crop stage window, lean victory tally, big toolbar tiles

- **Date:** 2026-08-24
- **Scenario:** `luna/dojo/tests/labs-arena/walkthrough.mjs` (phase-8 v2 expectations)
- **Environment:** local uvicorn :8778, postgres :5434, `ASCENT_GAME_PATH` → isolation worktree of plugin-linear-ascent at e40c0e2 + 0.96.1 edits, Chromium 1228 headless (SwiftShader), viewport 420×900 + 1440 desktop checks
- **Code under test (pre-commit):** plugin render.py (crop vars −71.9%/187.5%, lean tally, 76px toolbar rows), worldd `arena3d.js` (attach() copies `--awin-top/--awin-h` inline, `?v=4`), walkthrough with the new canvas-rect assert

## What changed since 0041 (roy's three reports on live 0.96.0)

1. **The squash.** The 320×300 3D frame was squashed into the 160 band, not cropped. Root cause: `createStage` (fight3d.js) ships `inset:0;height:100%` as INLINE style, so the phase-8 stylesheet window (`.banner.arena canvas{top:var(--awin-top);height:var(--awin-h)}`) never applied — inline wins. Fix: `arena3d.js attach()` copies the slot's computed `--awin-top`/`--awin-h` onto the canvas as inline styles; the CSS stays the single source of truth. Window moved to rows 115–275 (`--awin-top:-71.9%`) so the actors (rows ~150–240) sit centered — sky cut above, ground cut below.
2. **Victory overlay blocked the scene.** The tally slab (black box + pip heaps) covered the settled 3D. Fix: `_tally_html(lean=True)` — only the two big lines (icon + amount + XP/GOLD), no `tmarks`, no `tnote`, `background:none`.
3. **Toolbar tiles too small.** New tile: a ROW — 76px black box (56px picon) with a 4-line text column on its right: `[n]`, label, gold ATK, `[i]` — every line the card's 16px.

## Verdict

**36/36 PASS** (final run). One earlier run 35/36: the S11 gap check assumed a single-row toolbar; the big tiles wrap to rows on a phone and row 2 sits 90px under the stage by construction. Check corrected (first row must hug the stage, gap ≤ 20), re-run — a harness fix, not a product regression.

The check that would have caught the 0.96.0 squash now exists and passed with numbers:

- **S11 canvas WINDOWED not squashed:** rect `{top:-142, h:369, bh:198}` — h/bh = 1.864 ≈ 1.875, top/bh = −0.717 ≈ −0.719.
- S11 tiles: toolbar under the stage, all boxes 76px, first-row gap 6px, none in banner.
- S6 first round settles in 2912 ms (< 8 s, honest parallel clock).
- S7 canvas persisted 8 rounds; S12 end card regular menu; V: no console errors, no 4xx/5xx.

The walkthrough's fight ended in **death** (content-random), so the S12 victory-lean check was vacuous in-run. Victory is covered by supplementary captures (`captures/`): `v2-victory-1440.png` (archer, 16 XP / 39 GOLD) and `v2-victory-420.png` (13 XP / 28 GOLD) — big lines over the visible scene, no slab, no heaps; plus pytest asserts (`tallies lean` present, `tmarks`/`tnote` absent from the banner).

## Tests alongside

- Targeted `tests/test_067_arena.py tests/test_067_labs.py`: **19 passed**.
- Full plugin suite in the worktree: **6 failed, 1296 passed** — the identical pre-existing six (test_008_pace×2, test_013_combat_feel, test_017_damage_types, test_017_death_relics, test_kill3d); no regressions.

## Captures

Walkthrough's numbered screenshots beside this file. `captures/`: `v2-round-1440.png` / `v2-round-420.png` (true crop, actors centered, big tiles), `v2-victory-1440.png` / `v2-victory-420.png` (lean tally over the scene).
