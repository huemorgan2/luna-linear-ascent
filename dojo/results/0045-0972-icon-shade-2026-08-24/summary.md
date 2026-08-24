# Dojo run 0045 — 0.97.2: the win-tally icons actually cast their shadow

- **Date:** 2026-08-24
- **Scenario:** `luna/dojo/tests/labs-arena/walkthrough.mjs` (S14 upgraded to a pixel-truth check)
- **Environment:** local uvicorn :8778, postgres :5434, `ASCENT_GAME_PATH` → worktree of plugin-linear-ascent at 43b6201 (0.97.1) + 0.97.2 edits, Chromium 1228 headless (SwiftShader), viewport 420×900 + 1440 desktop checks

## The bug (roy's report on 0.97.1, with zoomed crops of both icons)

"this has no shade.. add shade to both icons." He was right and run 0044 was wrong: 0.97.1 put `filter:drop-shadow(...)` directly on the masked `.eg` span. CSS paints **mask after filter**, so the element's own `mask-image` clips the freshly painted shadow away — the computed style dutifully reported the filter while zero shadow pixels ever reached the screen. S14 checked computed style only and passed on a lie.

## The fix

The icon now sits in an `.egsh` wrapper and the filter sits on the wrapper — the wrapper's drop-shadow is generated from the child's already-masked rendering, so the shadow survives:

- `_tally_html` head: `<span class="egsh">{eg}</span>`.
- `.awin .thead>.egsh{filter:drop-shadow(2.8125px …)}` desktop, `1.5px` in the ≤600px trim; sizing moved to `.awin .thead .eg` (24/45px), base `.thead .eg` 30px, `.thead>.egsh{display:flex;flex:none}`.
- Same drawing-pixel arithmetic as 0.97.1 (display/16), unchanged text shadow.

## Verdict

**39/39 PASS**, fight ended in **victory** this run — S12/S14 ran live.

- **S14 (now pixel-verified):** `{shadow:"rgb(0,0,0) 4.5px 4.5px 0px", plus:true, egw:"24px", wrapFilter:"drop-shadow(rgb(0,0,0) 1.5px 1.5px 0px)", egFilter:"none", pixeldiff:true}` — the check screenshots the icon with the filter on, forces `filter:none`, screenshots again, and requires the buffers to differ. They do now; on 0.97.1 they would not have.
- Supplementary probe (shots11.mjs, `captures/`): both icons × both widths — `ICON{0,1}-PIXELDIFF true` at 1440 (45px icon, 2.8125px shadow) and 420 (24px, 1.5px). `zoom-sheet.png` is a 4× nearest-neighbor sheet of shadow/no-shadow crops — the gold badge at 1440 shows the black offset silhouette over the orange art plainly.
- V: no console errors, no 4xx/5xx.

## Tests alongside

- New regression test `test_0972_icon_shadow_rides_a_wrapper_not_the_mask`: the lean head wraps the eg in `.egsh`, the CSS filter targets the wrapper, and no `drop-shadow` rule in SCENE_CSS ends its selector on `.eg`.
- Targeted (067 arena + the real climb): **77 passed**. Full worktree suite: **5 failed, 1306 passed, 1 skipped, 1 xfailed** — the same 5 pre-existing failures as run 0044 (present at pristine c1bc08b), not regressions.
