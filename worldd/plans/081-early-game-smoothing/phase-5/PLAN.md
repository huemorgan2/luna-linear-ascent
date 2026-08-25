# 081 phase-5 — gear clarity: stats on tap, an honest pawn broker, a visible HOLD

Three small UI truths. All engine/render edits land in both copies
(submodule first, then `worldd/vendor` + parent pointer).

## Goal

(a) Tapping/clicking ANY item — gearmap slots beside the figure or pack
rows — shows its parameters (ATK/DEF, durability) at the top of the
popup, on desktop and mobile alike, including the starter bow and gate
armor. (b) The pawn shop says out loud which pack items the broker won't
buy, instead of silently ignoring them. (c) The equip action in the item
popup reads as an option: `[HOLD] — move to hand`. Measurable: dojo
scenario 05.

## Steps

### (a) Item parameters on click

Today stats live only in the hover tooltip (`data-tiph`, built in
`_slot_cell`, render.py:1713-1748); the click popup `openMenu`
(render.py:1942-1977) renders name + actions only, and on touch the tap
tooltip is immediately killed by the menu (`TIP_JS` bails when a
`.pmenu` exists, render.py:1846; `openMenu` hides the tipbox at
:1944-1945) — so on mobile the numbers are unreachable, and for the
starter bow / gate armor the popup is a bare name + one grey line
(`slot_actions` returns no rows for the only-weapon / price-0 cases,
core.py:246-281). The data itself is fine — `basic_bow` and
`gate_jerkin` carry bonus 5 / 7 in FORGE (economy.py:1987-2038).

1. In `_slot_cell` (render.py:1663-1780), emit the already-built
   `params` line (stat + durability spans) as a separate
   `data-params` attribute on the cell, alongside `data-tiph`.
2. In `openMenu` (render.py:1948-1960), insert
   `<div class="pstat">` + `data-params` content directly under
   `.phead`, before the action buttons / `.pwhy` line. New `.pstat` CSS
   next to `.pmenu` styles (render.py:3153).
3. Fill the gap for non-FORGE slot items: the charm/potion/relic branch
   of `_slot_map` (core.py:150-161) never sets `stat_name`/`stat_val` —
   set what exists (charm effect line, relic line) so their popups
   aren't blank; where an item genuinely has no numbers, `.pstat` is
   simply omitted.
4. Hover tooltip behavior stays as is — this adds the numbers to the
   click path, it does not move them.

### (b) The pawn shop names what it won't buy

The "rusted dagger" is `rusted_shiv` (STARTER_WEAPON,
economy.py:1987-1991); all starter weapons are in `BASIC_WEAPONS`
(economy.py:2011-2012) and are excluded from the offer list
(core.py:2995) AND from the sell action, which falls through silently
(core.py:3067 → :3104) — no message anywhere.

1. In `_pawn_scene` (core.py:2990-3060), right after the rate line
   (core.py:3004-3005), when the pack holds unsellable pieces, append:
   `"The broker waves off the {names} — gate steel and rusted basics
   are worth nothing to him, and never lost to you."` — computed from
   `[k for k in p["inventory"] if k in economy.BASIC_WEAPONS]` plus the
   price-0 gate pieces (`gate_buckler`, `gate_jerkin`,
   economy.py:2026-2037).
2. Fix the adjacent glitch found while exploring: price-0 gate kit is
   NOT in `BASIC_WEAPONS`, so it currently gets a sell row offering
   ◈ 0 (`_pawn_offer`, core.py:2964-2967). Exclude price-0 gear from
   the offer list and fold it into the waves-off line instead.
3. If a stale `sell_` act for an excluded slug arrives anyway, keep the
   silent fall-through but add the same waves-off note to the returned
   scene so the click visibly answered.

### (c) [HOLD] — move to hand

The label is server-authored in `pack_actions` (core.py:470-492:
`"Hold"` / `"Wear"`, hint "from your pack"); the popup row is a
`<button class="pact">` that reads as plain text (openMenu template
render.py:1952-1957, CSS render.py:3153-3160).

1. In the `openMenu` template, wrap the action label in the same
   bracket idiom as the main option rows: a `<span class="key">` whose
   CSS `::before`/`::after` render `[` `]` (mirroring `.opt .key`,
   render.py:3234-3252) — so every popup action reads `[HOLD]`,
   `[WEAR]`, `[MOVE TO THE PACK]` consistently, gold-inked.
2. Sharpen the hint at core.py:478: for weapons/shields,
   `"move to hand"` (or "swap out the {name}" when hands are full —
   keep that branch); labels remain server-authored and escaped
   (they're injected via innerHTML).

## Verification

- Plugin/worldd render tests: fragment for a level-1 player's card
  contains `data-params` with `ATK 5` on the starter weapon cell;
  pawn scene with a `rusted_shiv` + `gate_jerkin` in pack contains the
  waves-off line and no ◈ 0 sell row; popup template contains the
  bracketed key span.
- Manual, mobile viewport: tap starter bow in the gearmap → popup shows
  name, `ATK 5`, durability, and `[HOLD] — move to hand`; tap gate
  armor → `DEF 7`. Desktop hover tooltip unchanged.
- Then both full suites.

## Rollback

Revert the commit(s). Pure presentation + scene copy; no schema, no doc
shape, no economy values changed.
