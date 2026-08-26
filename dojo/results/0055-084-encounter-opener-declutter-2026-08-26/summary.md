# Dojo run 0055 — 084 encounter-opener declutter

- **Date:** 2026-08-26
- **Environment:** local worldd `uvicorn app.main:app --port 8600` on the
  synced vendor tree (0.106.0), postgres localhost:5434/ascent_world,
  Playwright Chromium headless; viewports 1280×900 desktop, 390×844
  touch mobile.
- **Player:** Dojo084A (fresh account through the real /signup +
  character-creation code paths; tenant web).
- **Driver:** `luna/dojo/tests/084-encounter-opener-declutter/walkthrough.mjs`
- **Scenario:** `worldd/tests/084-encounter-opener-declutter/01-opener-declutter.md`

## Verdict

| Scenario | Result | Notes |
|---|---|---|
| 084/01 opener declutter (desktop + mobile) | **PASS** | 33/33 checks; final run all green |

Foes drawn across runs: Grey wolf (runt/tough), Goblin straggler,
Feral boar, The Last Pack (alpha) — the shape held for every one.

## Evidence (screenshots/)

- `01-desktop-opener.png` — opener is art + slab (HP/ATK/DEF/SPEED + [i]
  on one line) + eyebrow "FLOOR 1 · MEN · THE FENCEROWS · THE LAST PACK
  — ALPHA" + one-row foe sheet (solid #26241f cells, white text, no
  borders) + swap hint + option rows. No headline, no ◇ plate, no
  description prose, no You-line, no whisper.
- `02-desktop-dossier-open.png` — hovering the slab [i] opens the full
  dossier panel; the ◇ range verdicts live there now.
- `03-desktop-round-card.png` — after close_in the round card keeps its
  surfaces: both nameplates, support line "It is between you and the way
  forward.", option tiles.
- `04-mobile-opener.png` — 390px: slab folds to two lines ([i]
  reachable), eyebrow wraps with the name, one-row sheet fits, no
  horizontal scroll, hint stays dismissed (server-side flag).

## DB verification

- `doc->>'foehint_done'` flips to `true` after the ✕ click; the hint is
  absent on the player's next opener (mobile pass).

## Regressions

- **R-0055-1 — the foehint ✕ was a dead button in a real browser.**
  `render.py` emits `button.x[data-opt=foehint_close]`, but the pane's
  delegated wiring (`wireOptions`, pane.py) never included `button.x` —
  clicks did nothing; run 0053 verified the dismissal via API only and
  missed it. **Fixed in this plan:** `button.x[data-opt]` added to the
  wiring selector; coded guard `test_foehint_x_is_wired_in_the_pane`
  added to test_084_opener_declutter.py. Re-walk PASS (browser click
  dismisses, flag persists, hint gone on next opener).
- **Driver finding, not a product bug:** the first probe read the
  eyebrow mid-typewriter; the driver now waits for the full line.
