# Phase 3 — the strip: half-res sigil, no growth, the faction's own hover

## Goal

The card's faction strip renders the sigil at half resolution (160×56
source, same 60 px display height — visibly chunkier pixels), hover no
longer scales or glows anything, and hovering the door paints **only
the area the banner and the name occupy** with the faction's color
(ink flips to black for contrast). The climber/online counts to the
right change nothing on hover. Measurable: dojo screenshots + computed
CSS (no `transform` on hover; door background equals the faction hex).

## Steps

All in `plugin-linear-ascent/`, inherited by worldd in phase 4.

1. **Half-res sigil files** — `tools/halve_faction_sigils.py` (new):
   PIL, `Image.NEAREST` 320×112 → 160×56, re-threshold to pure
   white/transparent 1-bit; writes `<slug>_160x56.png` beside each of
   the 31 `<slug>_320x112.png` in `content/art/banners/factions/`.
   Commit the 31 generated files (art is committed, tool is rerunnable).
2. **`render.py` — the sigil becomes tintable ink**:
   - `_sigil_half_data_url(slug)` (new, lru_cached): prefer
     `_160x56.png`, fall back to `_320x112.png` — a missing half never
     blanks the strip. Deliberately NOT added to `_banner_data_url`'s
     size tuples: hall galleries, banner pages and room art keep full
     res; only the strip downshifts.
   - `_faction_block`: replace the `<img class="facsig">` with a masked
     span (the `_ticon` pattern, ~L1008):
     `<span class="facsig" style="-webkit-mask-image:url(...);mask-image:url(...)"></span>`
     — white-on-transparent art as a mask, `background-color` as the
     ink, so CSS can recolor it. Width fixed from the art's aspect
     (60 px tall → ~171 px wide at 320:112).
   - The block styles its door with the faction ink:
     `<div class="facblk" style="--fac:{faction_ink(m.faction_color)}">`
     (`colors.faction_ink` falls back to Warden Violet — legacy
     factions keep today's exact ink).
3. **CSS (the card styles in `render.py`, ~L2561–2586)**:
   - `.facsig`: keep `height:60px`, keep `image-rendering:pixelated`;
     rest ink `background-color:{TEXT}`-equivalent white kept as today
     via `{ARTBRIGHT}`; drop the `filter`/`transform` transition, keep
     a `background-color .12s` transition.
   - `.facdoor`: small padding (`2px 1ch 2px 0` — the highlight hugs
     banner + name, nothing else) and
     `transition:background-color .12s`.
   - Hover/focus (replaces the grow+glow rules at ~L2577–2581):
     ```css
     .facblk .facdoor:hover, .facblk .facdoor:focus-visible {
       background: var(--fac);
     }
     .facblk .facdoor:hover .facname, ... .facname { color: #000; border-bottom-color: transparent; }
     .facblk .facdoor:hover .facsig, ... .facsig { background-color: #000; }
     ```
     No `transform`, no `filter`, no gold underline. `.facsub`
     (counts) rules untouched.
   - The bannerless `JOIN A FACTION` door keeps the old gold text-only
     hover (no faction, no color).
4. Bump the CSS/asset cache-buster if the card ships one (check the
   `fight3d.js?v=` pattern for the card equivalent).

## Verification

- Rendered-card test: `_faction_block` output contains `--fac:#f26541`
  for a meters fixture with `faction_color="ember-red"`, and the
  Warden-Violet hex for `faction_color=""`.
- Grep the emitted CSS: no `scale(` and no `drop-shadow` inside the
  `.facblk` rules.
- Visual pass (dojo, phase 4 screenshots): sigil pixels ~2× chunkier;
  hover = flat color block behind banner+name only; layout does not
  shift on hover (bounding boxes identical hovered/unhovered).
- Data-URL payload of the strip sigil shrinks (~¼ the bytes) — spot
  check one card render.

## Rollback

`git revert` the phase commit (art files + render.py). The 160×56
files are additive; reverting render.py alone restores today's strip.

## Execution status

**Done — 2026-08-16, plugin commit `28f87b1`.**

- 30 sigils halved (the dir's 31st entry is `preview/`, not art);
  combined payload 50,493 bytes vs 190,179 for the 320x112 set —
  ratio 0.27, on the ~¼ target. All 30 verified pure
  white/transparent 1-bit at exactly 160x56.
- `_sigil_half_data_url` + masked-span `facsig` (width 171px from the
  60px height), `--fac` custom property from `colors.faction_ink`,
  flat `background:var(--fac)` hover with ink flipped `#000`, no
  `scale(`/`drop-shadow` anywhere in `.facblk`; `.facsub` rules
  untouched; `.facdoor.join` keeps the gold text-only hover.
- Step 4 (cache-buster): not applicable — the card's CSS is inlined in
  every rendered page (`render.py` f-strings), nothing cached to bust.
- Verification: 6 new tests in `test_010_faction_colors.py` cover the
  `--fac` hex for `ember-red` and the Warden-Violet fallback, the
  half-res mask markup (and that `_banner_data_url` still resolves
  320x112 for galleries), the no-scale/no-glow CSS, and the JOIN
  door's gold hover; `test_059_faction_block.py` updated for the span.
  Full plugin suite: 1193 passed; same 3 pre-existing failures as
  phase 2 (chest-card work, reproduce at pre-phase HEAD).
- Visual/computed-CSS pass lands with the phase-4 dojo walkthrough.
