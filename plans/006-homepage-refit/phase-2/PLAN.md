# Phase 2 — the movie plays itself

## Goal

"THE STORY SO FAR" is one card that stays in one place and plays: panel
art runs, its lines type themselves at reading speed, and only when the
GIF has played a full cycle AND the last line has finished typing does
the panel dissolve to the next — I through IX, then round again. No
skip button, no click-to-advance. Moving dot-shapes in the ANSI ink mark
progress. Measurable: with the viewport parked on the section and no
input, panel II replaces panel I in the same viewport box.

## Steps

1. `index.html`: keep the nine `#lore` cards in markup (scripts-off /
   reduced-motion fallback stays the readable list). Add per-card data
   attributes: `data-art` slug, `data-ms` (full-cycle ms measured from
   the real GIFs: singles 6240; split pairs intro 4800 then `_loop`
   swap, mirroring the game's `_fx_split`), `data-intro`/`data-loop`
   srcs for the four split slugs.
2. `site.js`: a `storyPlayer()` that (motion allowed + JS only)
   converts `#lore` into the player:
   - shows one card at a time in a fixed-height stage;
   - restarts each panel's GIF deterministically (fresh `src` with a
     cache-buster) so the cycle clock starts at 0; split slugs swap
     `_intro` → `_loop` after `intro_ms`;
   - types `p.t` lines at ~28 ms/char (≈450 ms per short line pause) —
     reading speed, ~9× slower than today's 4 ms/char;
   - advance condition: `max(gifCycleDone, typingDone) + 900 ms` hold;
   - transition: a one-line dot sweep (`░▒▓` marching via `steps()`)
     plus the dot rail `·──●──·` (one mark per panel, active one
     bright/blinking) under the stage;
   - no skip affordance of any kind; loops forever.
3. `site.css`: `.stage` fixed box (art 320×200 + text well),
   `.dotrail`, `.sweep` keyframes in `steps()` (terminal law: no
   fades), all under `@media (prefers-reduced-motion: no-preference)`
   guards where animating.
4. The typewriter change applies only to the player's cards; other
   sections keep the existing materialize behavior.

## Verification

- `worldd tests`: test_site asserts the player scaffolding
  (`id="story-stage"` or `data-art` present ×9) and that no element
  with text like "skip" exists in `#lore`.
- Browser check (local + production): park on the section ≥40 s with
  zero input → at least two panel advances observed; text visibly types
  slower than before; DOM contains no skip control; disabling JS shows
  the nine readable cards.

## Rollback

`git revert` the phase commit — index.html/site.js/site.css return to
the 005 scroll layout.

## Execution status

**DONE 2026-08-08.** In-place player shipped in site.js: one card visible, advance only
when gif cycle (data-ms) AND typewriter (28 ms/char) finish + 1.4 s hold; split chapters
swap _intro→_loop; dot rail with gold live dot + marching ░▒▓▒░ train; no skip control.
One fix during local verify: boot observer had threshold 0.2 on the tall #lore section
(can never fire) → observe cards[0] with rootMargin -25%. Verified 45 s hands-off on
production: refugee→stone→theft in place, scrollY unchanged, console clean.
