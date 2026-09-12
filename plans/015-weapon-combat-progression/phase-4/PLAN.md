# Phase 4 — All weapon families, creatures and combat rules

## Goal

Extend the proven loop to all 16 families,64 grade variants and425 authored creatures without multiplying old/new type modifiers or losing readability.

## Steps

1. Implement poison, burn, bleed, push, stun, slow and Expose with one documented action order. New DoTs first tick on the next enemy phase. Effects refresh under their stated limits; an immune target remains immune.
2. Implement all six arrow payloads, techniques and cooldowns. One accepted shot consumes one arrow even on a miss; rejected actions consume none. Switching gear cannot reset cooldowns or award free actions.
3. Preserve authored body/bite/specimen differences while assigning fixed movement/affinity/traits. Expand floors through content bands; no eight-image replacement roster or unrestricted universal reskins.
4. Complete all 64 weapon definitions and their Forge/source display, frames and drawings. Every family needs at least one intentional tactical or resource role and a meaningful weakness.
5. Update pack, shop, loot, death, Forge, combat, tool descriptions and encyclopedia from the same definitions. Retain16px game typography, game icons, keyboard/tap access and open selectors of six or fewer options.
6. Keep any new monster-specific control behavior out of PvP until explicit PvP rules are verified; item/stat compatibility is still required.

## Verification

Run the content lint and full catalog/instance checks. Exhaustively validate legal reach, effect timing, counters, 84 upgrade states and all 425 species; use end-to-end encounters to test their combinations. Run dojo S04/S05/S06, including Ramguard push → paid bow shot/escape, spell-dispersing flyers, poison immunity, Shield wall and max-grade art. Inspect event logs rather than just final HP.

## Rollback

Revert the content/combat/UI implementation as a unit in QA. Preserve readers and asset history. Do not run different damage-rule versions against one shared warden.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
