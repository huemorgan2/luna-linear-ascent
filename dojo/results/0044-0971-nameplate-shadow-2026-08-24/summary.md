# Dojo run 0044 — 0.97.1: [i] on the foe's nameplate; win amounts with pixel shadow, 150% icons, +

- **Date:** 2026-08-24
- **Scenario:** `luna/dojo/tests/labs-arena/walkthrough.mjs` (S13 retargeted, S14 added)
- **Environment:** local uvicorn :8778, postgres :5434, `ASCENT_GAME_PATH` → isolation worktree of plugin-linear-ascent at c1bc08b (0.97.0) + 0.97.1 edits, Chromium 1228 headless (SwiftShader), viewport 420×900 + 1440 desktop checks
- **Code under test (pre-commit):** plugin render.py + tests/test_067_arena.py — no worldd changes this release.

## What changed since 0043 (roy's report on 0.96.2)

Roy: "you added the name an [i] at the bottom — remove that and add the [i] next to the existing name it has on the scene" and (on the lean victory tally) "make a crisp black shadow under it by duplicating the same object and moving it 45° one DRAWING pixel right+down — the text and the icons need different screen displacement — icons 150%, same resolution — and a + after the number."

1. **The [i] moved onto the foe's HUD nameplate.** In a live round the creature's name exists in exactly one place — the top-right `.astat.foe .aname` slab on the scene — and the `[i]` (data-tiph = the dossier panel) now rides it there. The duplicate name headline under the scene is gone (`arena_live and scene.enemy` → no headline div). Opener and end cards keep their headline (+[i] on the opener).
2. **Crisp black shadow on the win amounts.** `.awin .bigtx div{text-shadow:1ch .5em 0 #000}` — the big font's drawing pixel is one char wide (1ch) and half a line tall (.5em, half-block rows), so the duplicate shifts exactly one grid cell at 45° at any font size (8px/8px @16px desktop, 4.5px/4.5px @9px trim). Icons are 16×16 grids: `filter:drop-shadow(display/16 …)` — 2.8125px @45px, 1.5px @24px.
3. **Icons 150%, same resolution.** `.awin .thead>.eg` 30→45px desktop, 16→24px in the ≤600px container trim (pixelated mask scaling, still the 16×16 grid).
4. **+ after the number.** Lean tally renders `{n}+ {WORD}` ("17+ XP", "34+ GOLD"); "+" added to the `_BIG` half-block font (missing chars are silently dropped) and to its gold char set.

## Verdict

**39/39 PASS** (38 prior + S14; S13 retargeted to the nameplate), fight ended in **victory** this run — S12/S14 ran live.

- **S13:** `{infoOnName:true, tiph:true, headline:0, fold:0, word:false}` — the [i] on `.astat.foe .aname`, zero `.headline` on the live round card.
- **S13 hover:** `{shown:"block", panel:true, rows:4, dhead:true, unframed:true}` — screenshot `09-dossier-tip-open.png`.
- **S14:** `{shadow:"rgb(0, 0, 0) 4.5px 4.5px 0px", plus:true, egw:"24px", filter:"drop-shadow(rgb(0, 0, 0) 1.5px 1.5px 0px)"}` @420.
- S6 first round settles in 3013 ms (< 8 s); V: no console errors, no 4xx/5xx.

Supplementary probe (shots10.mjs, `captures/`): live rounds at 1440 (archer) and 420 (warrior) — `[i]` on the nameplate, tip opens (6 rows) and hides, no headline; victory at both widths — `1440-end-1440.png` shows "17+ XP / 34+ GOLD" with the 8px text shadow and 45px icons (2.8125px icon shadow), `420-end-420.png` the 9px/24px trim (4.5px / 1.5px). Opener keeps its name headline with the [i] (`OPENER-TIP {infoOnHeadline:true}`).

## Tests alongside

- Targeted (info_card, 067 arena incl. 3 new 0.97.1 tests, the real climb): **104 passed**.
- Full plugin suite in the worktree: **5 failed, 1305 passed, 1 skipped, 1 xfailed** — the same 5 fail at the pristine base c1bc08b with the diff stashed (test_031 ident_header, test_033 warden falls, test_048 no_clazz, test_kill3d ×2); pre-existing, not regressions (test_031/test_048 arrived with 0.97.0).

## Note

Mid-release the other session shipped 0.97.0 (plugin c1bc08b + root 4be7db5, worldd app now requires `engine.profile.public_sheet`). This release was rebased from 6f15bc0 onto c1bc08b and renumbered 0.96.3 → **0.97.1** so the marketplace never goes backwards.
