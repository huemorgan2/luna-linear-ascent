# Dojo 006-01 — the homepage plays its own movie

## Preconditions

- Production https://linearascent.net serves `/health` with game ≥
  0.51.0 and `db: true`.
- A fresh, uniquely-named isolated browser context (verify `/me` →
  `{"username": null}` before starting). Set a User-Agent on any raw
  API probe (edge 403s without one).

## Scenario

1. Open the homepage. Screenshot the first fold.
2. Scroll once to THE STORY SO FAR and then **stop giving input
   entirely**. Watch for 45 seconds. Screenshot at ~0 s, ~20 s, ~40 s.
3. Inspect the story section DOM: list every button/anchor inside it.
4. Read a panel while it types: judge whether the text writes at a
   pace a person can comfortably read along with (not appearing
   instantly, not crawling).
5. Scroll to HOW IT PLAYS. Screenshot the three class figures.
6. Scroll to THE CLIMB AHEAD. Screenshot the whole section; check for
   a horizontal scrollbar at 1280 px and at 375 px width.
7. Read THE STONE OF ERAS copy. Screenshot.
8. Regression: sign up a fresh throwaway account from the gate card;
   confirm it lands in `/play` and the first story card renders.

## Expected behavior

- The story movie stays in one place: the panel at ~20 s or ~40 s is a
  **different chapter** than at 0 s, in the same viewport box, with no
  scrolling and no clicks. Panels change only after their text has
  finished typing. A row of dot-shapes marks which panel is playing;
  something dot-like visibly moves in the terminal ink style.
- Text types at reading speed.
- WARRIOR is a woman in armour; ARCHER is a heavily armoured elf;
  SORCERER is a huge dwarf wizard holding a staff, clearly taller
  (head-and-shoulders or more) and wider than the other two figures.
- Floors section: exactly six entries, stacked vertically, titled
  "Floor 1 · …" through "Floor 6 · …".
- Stone copy says we remember no matter what happens on the hundredth
  floor.
- Signup still opens straight into the tower.

## Fail conditions

- Any "skip" control (button, link, or clickable area that advances
  the movie) inside the story section.
- The movie advancing before its text finished typing, or never
  advancing within 45 s.
- The page scrolling by itself, or the movie living in a horizontal
  scroller.
- "F1"-style captions anywhere; floors 7–10 art on the page.
- The wizard rendered the same height as the other portraits.
- Horizontal page scroll at 375 px.
- Signup failing or landing anywhere but /play.

## Verify

- DOM: story section contains no element whose text or aria-label
  matches /skip/i.
- Network: the four split chapters fetch `_intro` then `_loop` GIF
  variants.
- `curl -A dojo /health` game matches the shipped version; homepage
  HTML contains `Floor 1 ·` and not `F1 ·`.
- Console: zero errors during the whole walkthrough.
