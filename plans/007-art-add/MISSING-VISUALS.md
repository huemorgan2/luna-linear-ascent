# Missing visuals — assets that DON'T exist

Audit date 2026-08-09, plugin commit 5291d81 (0.57.1). Inventory script
over all 100 floor YAMLs (425 encounters) checking
`content/art/creatures/<id>_320x112.png` / `_320x200.png` and
`content/art/events/<id>_<verb>_320x112.gif` with the combat.py
resolution rules (`_creature_art` / `_event_art`, breed fallback).

## Portraits: NONE missing

543/543 portrait PNGs exist; every one of the 425 encounters (and
wardens) resolves art. Local working tree == plugin HEAD == worldd
vendor == published 0.57.1 zip. The user-visible "no image" cases are
wrong-species portraits — see MISFIT-VISUALS.md P0.

## Own finish reels missing on floors 1–10 (3) — generic fallback plays

The engine falls back to the breed-generic reel
(`<kind>_<verb>_320x112.gif`), so nothing crashes — but the revealed
animal is the generic one, which mismatches the fought species:

| Floor | id | Missing asset | Fallback in use | Player-visible wrongness |
|---|---|---|---|---|
| 7 | rabid_boar (Cider-mad boar) | rabid_boar_freed_320x112.gif | native_freed | boar fight ends revealing a small dog/piglet-ambiguous canid |
| 9 | pylon_adder (Pylon adder) | pylon_adder_freed_320x112.gif | native_freed | snake fight ends revealing a small dog — clear species clash |
| 10 | muster_wight (Muster-wight) | muster_wight_evicted_320x112.gif | wrongmade_evicted | generic eviction reel; thematically fine, lowest priority |

History (phase C): all three were parked. muster_wight failed 3/3
re-rolls (arrow-stretch fail family — try thrown weapon or closer
framing per phase-c notes). rabid_boar and pylon_adder were parked on
reveal-size / mouth-escape families. Cap 3 grok takes each (~$0.64/take),
judge with the 16-row sheet + 6-rule checklist, park again on 3 fails.

Command per slug (from `plugin-linear-ascent/`, luna/.env sourced):
`uv run --project ../luna python tools/generate_event_gifs.py <id>_<verb> --backend grok --force`

## Reel with missing SUBJECT (1) — file exists, wight absent

| Floor | asset | Problem |
|---|---|---|
| 4 | lamptree_wight_evicted_320x112.gif | reel shows only a bare tree splitting/dissolving — no wight figure, no combat. Phase-C parked (lore third-figure + dark-scene fails). Counts as missing-in-effect: the encounter's monster never appears in its own finish. |

## Floors 11–100: no finish reels AT ALL (366 encounters) — by design, decision needed

Floors 11–100 still use the legacy encounter schema (no `kind:` field →
runtime breed "" → combat.py plays no finish reel). This is not a
regression; it is unbuilt content. Options, cheapest first:

1. **Assign `kind:` to all 366 encounters** (YAML-only edit) → they
   instantly inherit the three generic breed reels. Cost: editorial pass,
   zero art spend. Species-mismatch caveat same as the fallback trio above.
2. Generic reels per BIOME tier (10 zones × 3 kinds ≈ 30 reels).
3. Own reels per encounter (366 × ~$0.64 × takes) — full art pass.

OUT OF SCOPE for plan 007 until the user picks an option.

## Legacy floors spot-check (clean)

The 6 floors-11+ encounters whose id and display name share no words
(mirage_wisp→Heat-ghost, pale_fire→Colorless flame, standing_dead→Hollow
trunk, block_wight→Quarried thing, rigging_ghast→Tangled topman,
honored_mare→The master's remount) were eyeballed: every portrait matches
its display name. No action.
