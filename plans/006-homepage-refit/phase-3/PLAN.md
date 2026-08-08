# Phase 3 — floors stand in a column; the Stone remembers

## Goal

THE CLIMB AHEAD shows exactly floors 1–6, stacked vertically with no
horizontal scroll, each captioned "Floor N · NAME" (never "F1"). THE
STONE OF ERAS copy states that we remember no matter what happens on
the hundredth floor. Measurable: homepage HTML contains six
`floorN_world` images (1–6), zero occurrences of `F1 ·`…`F10 ·`, and
the phrase "No matter what happens on the hundredth floor".

## Steps

1. `index.html` `#floors`: drop figures 7–10; retitle captions
   `Floor 1 · THE FENCEROWS` … `Floor 6 · THE HOLLOW LANES` (keep the
   town · Warden subline); replace `.strip` with a vertical `.floorcol`.
2. `site.css`: `.floorcol { display:flex; flex-direction:column;
   gap:3ch; align-items:center; }` — no `overflow-x`; figures keep
   320×200 pixelated art and captions under the image. Remove/leave
   `.strip` unused (delete to keep the sheet clean).
3. `#stone` copy: rewrite the lead paragraph to carry "No matter what
   happens on the hundredth floor — we remember." while keeping the
   era-reset/ledger-frozen facts.

## Verification

- test_site: `"Floor 1 · THE FENCEROWS" in body`,
  `"F1 ·" not in body`, `"floor7_world" not in body`,
  `"No matter what happens on the hundredth floor" in body`.
- Browser: the six figures render stacked, page has no horizontal
  scrollbar at 375 px and 1280 px widths.

## Rollback

`git revert` the phase commit.

## Execution status

**DONE 2026-08-08.** .strip → .floorcol vertical column, floors 1–6 only, captions
"Floor N · NAME" (Warden sublines kept); Stone copy leads with "No matter what happens
on the hundredth floor — we remember." Verified on production at 1280 and 375 px, no
horizontal scroll.
