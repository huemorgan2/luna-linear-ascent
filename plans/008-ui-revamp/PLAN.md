# 008 — UI revamp: the game under the terminal law

## The problem

Two visual languages. The homepage obeys the terminal law (plan 003):
one font (IBM VGA 8×16), one size (16px/1.3), hierarchy by caps /
bright / dim / reverse video / borders, `ch`-grid layout, scanlines,
`steps()` motion. The game (`render.py` + `pane.py`) is a modern dark
HUD: 14px/1.6 system monospace, five extra font sizes, a blue-black
multi-hue palette. Crossing from `/` to `/play` reads as leaving the
product.

## Step 1 — the mock (this plan)

A static mock of the game's screens restated under the homepage's law,
served for side-by-side judgment:

    worldd/static/site/mock/roothollow.html   (+ mock.css, art/)

- Reuses `site.css` verbatim; `mock.css` only swaps ink and restates
  game components.
- **CGA 16-color palette**, nothing in between: black `#000`, light
  gray `#AAA` text, dark gray `#555` dim/borders, white `#FFF` bright,
  yellow `#FF5` accent (the old gold), light green `#5F5` HP, light
  cyan `#5FF` energy/notifications, light magenta `#F5F` XP, light
  red `#F55` damage, brown `#A50` the Crier's ink.
- Screens covered: the square (14 doors, meters rail, Crier sheet),
  the Forge card wall (real tier-1 gear + real 1-bit icons), a fight
  (enemy plate, dossier fold, combat log), the School (▰▱ ranks).
- Idioms: door rows as ANSI menu lines with `·` dot leaders instead of
  bordered buttons; meters as `▓░` text; reverse video on hover
  (yellow for open doors, dark gray for locked); banners stay 1-bit
  masks tinted with one ink; `▸/▾` folds for legend and dossier.

## Step 2 — the port (separate plan, after the look is approved)

Port `SCENE_CSS` (`render.py`) and the pane shell (`pane.py`) to the
law: ship the VGA woff into the game shell, collapse all font sizes to
one, adopt the CGA tokens, kill fades, decide the Crier serif
exception's fate.

## Verify

    cd worldd && .venv/bin/uvicorn app.main:app --port 8000
    open http://localhost:8000/static/site/mock/roothollow.html

Font, size, line height and card frames must be indistinguishable from
`/`; content must match the live square at `/play`.
