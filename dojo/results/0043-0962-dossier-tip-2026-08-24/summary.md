# Dojo run 0043 — 0.96.2: the [i] rides the creature name, the dossier is its tooltip

- **Date:** 2026-08-24
- **Scenario:** `luna/dojo/tests/labs-arena/walkthrough.mjs` (+ two new S13 checks)
- **Environment:** local uvicorn :8778, postgres :5434, `ASCENT_GAME_PATH` → isolation worktree of plugin-linear-ascent at 05ef049 + 0.96.2 edits, Chromium 1228 headless (SwiftShader), viewport 420×900 + 1440 desktop checks
- **Code under test (pre-commit):** plugin render.py only — no worldd changes this release.

## What changed since 0042 (roy's report on 0.96.1)

Roy: "put the [i] next to the creature name — remove the word dossier — the monster explanation opens in a tooltip over the [i] — keep the dossier panel's look — and remove it from the bottom of the screen under the scene."

1. **The [i] moved onto the headline.** The creature-name headline now ends in the standard `[i]` badge (`.headline .info`, inline-flex, dim → aether on hover/focus). Its `data-tiph` carries the whole dossier panel as trusted server HTML; `data-tip` keeps the flattened text fallback.
2. **The fold is gone.** `_dossier_html` returns the bare `<div class="dossier">` panel — no `<details class="dx">`, no "[i] dossier" line under the scene, `.dx` CSS deleted. The eplate's old `[i]` (flat-text tip) is gone too — one `[i]`, one place.
3. **The panel look is unchanged.** Same `.dossier`/`.dhead`/`.drw`/`.ticon` markup and CSS. Inside `#tipbox` the box itself is the aether-on-ink frame, so the panel sheds its own border/slab (`#tipbox .dossier{border:0;background:none;padding:0;margin:0}`) — one frame, same sheet. TIP_JS gives a dossier tip 560px instead of 380.

## Verdict

**38/38 PASS** (36 prior checks + 2 new S13), fight ended in **victory** this run, so the S12 victory-lean checks ran live (not vacuous).

- **S13 [i] on the name, fold gone:** `{infoOnName:true, tiph:true, fold:0, word:false}` — no `details.dx` on any card, no "] dossier" text anywhere.
- **S13 hover opens the panel:** `{shown:"block", panel:true, rows:4, dhead:true, unframed:true}` — screenshot `09-dossier-tip-open.png`.
- S6 first round settles in 4934 ms (< 8 s); S11 canvas window `{top:-142, h:369, bh:198}` — crop intact; S12 victory tally lean; V: no console errors, no 4xx/5xx.

Supplementary probe (shots9.mjs, `captures/`): opener + round cards at 1440 (archer) and 420 (warrior) — `[i]` present from the opener on, hover shows the sheet (5 rows at range / 4 rows close), hover-off hides it, `tip-open-1440.png` / `tip-open-420.png`. End cards (victory and death) carry no enemy → no `[i]`, regular menu intact.

## Tests alongside

- Targeted (info_card, damage_types, bestiary, mercy, climb_pays, qol, 067 arena+labs): **107 passed, 1 skipped**.
- Full plugin suite in the worktree: **3 failed, 1299 passed** — the same 3 fail at the pristine base commit with the diff stashed (test_033_when_a_warden_falls, test_kill3d ×2); pre-existing, not regressions.
- test_017_info_card updated: the `<details` asserts now assert the fold is GONE and the headline carries `data-tiph`.
