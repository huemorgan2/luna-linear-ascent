# 010 — Faction colors: the strip, the hover, and a color of one's own

## Problem

The faction strip at the foot of the player card (banner sigil + faction
name + climber counts, `_faction_block` in
`plugin_linear_ascent/render.py`) has three issues, reported 2026-08-16:

1. **The sigil renders too sharp.** The 320×112 source is displayed at
   60 px height — finer-grained than the rest of the 1-bit card art.
   Wanted: about half the resolution (chunkier pixels).
2. **Hover grows the banner.** `.facdoor:hover .facsig` applies
   `transform:scale(1.06)` + a brightness/glow filter
   (render.py ~L2579). Wanted: no growth — a color change only.
3. **Hover has no faction identity.** Hovering the door (banner + name)
   underlines the name in the global GOLD. Wanted: the whole area the
   banner and the name occupy — and nothing else in the strip (the
   climber/online counts stay untouched) — takes the **faction's own
   color** as background on hover.

## Root cause

Factions have no color. Evidence:

- `worldd` schema (`ascent_factions`, migration 011/016): columns
  `name, banner, founder_*, created_week, join_fee, weekly_dues,
  treasury, requirements` — **no color column**.
- All sigils are tinted one global ink: `_banner_tint` returns
  `VIOLET_SOFT` for anything in the sigils dir (render.py ~L119).
- The founding flow (`engine/social.py _founding_scene`) has steps
  name → banner → fee → dues; the admin desk (`pane.py`) offers only
  rename. Nowhere can a founder or steward choose a color.

So the hover requirement is blocked on a feature: **a faction color**,
picked at founding, changeable from the admin desk (the rename area),
stored server-side, and delivered through the meters to the card.

## The color roster

Only inks the game already owns (the 1-bit palette constants in
`render.py`), each named after something in the world that signals it:

| slug            | name           | ink       | source constant |
|-----------------|----------------|-----------|-----------------|
| `mouse-grey`    | Mouse Grey     | `#5b5952` | DIM             |
| `rag-silver`    | Rag Silver     | `#adaba0` | TEXT            |
| `bone-white`    | Bone White     | `#fbfbf7` | BRIGHT          |
| `coin-gold`     | Coin Gold      | `#f5b825` | GOLD            |
| `aether-teal`   | Aether Teal    | `#45d0c0` | AETHER          |
| `warden-violet` | Warden Violet  | `#d967c8` | VIOLET          |
| `ember-red`     | Ember Red      | `#f26541` | RED             |
| `orchard-green` | Orchard Green  | `#8ed24a` | OK              |
| `root-brown`    | Root Brown     | `#b5722f` | BROWN           |

No new hexes enter the palette. **Fallback:** factions founded before
this plan (and any missing/unknown value) resolve to `warden-violet` —
the exact ink their sigils fly today, so nothing changes color
uninvited.

Single source of truth: `plugin_linear_ascent/colors.py` (slug → name,
hex, ordered). `worldd/app/factions.py` mirrors only the slug list for
validation (the server never needs the hexes).

## Emergency mitigation already taken

None needed — cosmetic + additive feature, nothing is broken in
production.

## Fix — four phases

1. **phase-1/** — server: `color` column on `ascent_factions`
   (default `warden-violet`), found/recolor endpoints, color in the
   faction payload.
2. **phase-2/** — plugin: color roster module, founding step
   (name → banner → **color** → fee → dues), CHANGE COLORS beside
   rename on the admin desk (pane + in-scene hall), meters plumbing.
3. **phase-3/** — the strip: half-res (160×56) sigil, mask-tinted ink,
   hover = faction-color background over the banner+name door only, no
   scale, counts untouched.
4. **phase-4/** — vendor into worldd, full suites, migration, deploy,
   dojo walkthrough, production probes.

Phases execute in order; each is verified before the next begins.

## Verification (plan level)

- Plugin + worldd pytest suites green at every phase boundary.
- Dojo scenario `faction-colors` (ships with phase 4): found with a
  color, hover shows it, recolor from the desk propagates, legacy
  faction falls back to Warden Violet, hover does not grow the banner.
- `/health` game field shows the new version on BOTH the worldd vendor
  and the marketplace plugin before the ship is called done.

## Operational notes

- The migration is additive with a server-side default — old rows need
  no backfill and the previous release keeps working against the new
  schema (rollback = redeploy previous release, column stays).
- Changes land in both places: `plugin-linear-ascent` (source submodule)
  AND `worldd/vendor/plugin_linear_ascent` via `worldd/tools/vendor_game.sh`
  — `deploy.sh` refuses a stale vendor.
- Secret-pattern scan before every commit, as always.
