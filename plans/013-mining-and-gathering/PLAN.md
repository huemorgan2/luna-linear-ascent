# Mining and gathering — future project note

**Status: proposed, not started.** This is a separate project from the [weapon/material research](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/weapon-upgrades/RESEARCH.md). Mining must not be required to ship or complete weapon progression. This note reserves the eight material sites and their intended loop; it does not authorize a production mutation or claim an executed phase.

## Problem, evidence, and timeline

On 11 September 2026, the weapon proposal introduced four material grades and eight materials. Creature drops are the initial source. A later gathering activity should let a player deliberately pursue one material, spending energy and risking the expedition's haul. Existing content reaches floor 100 and already provides floor-specific biomes and map navigation, but this research has not identified an implemented eight-material gathering loop.

The current pack and combat flows are built around ordinary inventory gains and fights that return to town. A gathering expedition needs its own pending-haul state so “lose everything collected this trip” cannot accidentally delete materials earned before the expedition.

## Root cause / missing capability

Materials need an intentional source distinct from hunting. The game currently lacks the proposed combination of site eligibility, gathering-tool validation, per-energy gathering rolls, site encounters, unbanked expedition inventory, and explicit extraction.

## Emergency mitigation already taken

None required. No runtime or production changes were made. The weapon proposal is balanced around creature drops without mining.

## Eight proposed sites

Floors are world locations, not player levels. Player levels currently cap at 30. Site names and enemy concepts below are proposed content, not claims that those map landmarks already exist.

| Floor | Existing biome / zone | Proposed site | Material | Required equipment concept | Encounter concept |
|---:|---|---|---|---|---|
| 3 | Men / The Drowned Pasture | Drowned Copse | Wood | Serviceable wood axe | Mire boar or root-tangled wolf |
| 3 | Men / The Drowned Pasture | Bog-Iron Field | Raw Metal | Serviceable pickaxe | Ironback burrower |
| 18 | Ironvale / The Deep Drifts | Tempered Scrap Seam | Steel | Hardened pickaxe | Ore crawler or discarded mine sentinel |
| 25 | The Barrows / The Processional Way | Buried Heartwood Grove | Hardwood | Steel wood axe | Barrow stag or heartwood guardian |
| 45 | The Scorch / The Ogre Steps | Starforge Slag Beds | Starforged Steel | Heat-resistant mining kit | Slag hound or furnace remnant |
| 55 | Frosthold / The Giant Steadings | Fallen-Star Crater | Meteorite | Reinforced impact pick | Meteor shellback or frost-crater beast |
| 70 | Stormreach / The Tempest Court | Shard Fissure | Shard Matter | Shard-safe extraction tool | Fracture sentinel |
| 80 | The Gloom / The Pale Court | Mythic Loom Hollow | Mythic Threads | Attuned harvesting shears | Loom spider or threadbound hunter |

The first two sites deliver the requested floor-3 forest/metal choice. Both Legendary sites are high in the tower, and all eight are reachable by floor 80. Steel and Starforged Steel sites are salvage/extraction deposits, avoiding a separate smelting economy in the initial mining project. Tools, names, and enemy placement need content review against the existing maps before execution.

## Core loop

1. Enter an unlocked site with its required usable tool. Show the material, success chance, energy charge, encounter risk, and unbanked-haul warning before starting.
2. Each gathering attempt spends **one energy**, exactly once. It rolls for the chosen material and for a small site-specific encounter chance. Different sites need not have identical odds or yields; knowledge, tool choice, and danger should create better and worse routes.
3. Gathered units enter an expedition haul, separate from ordinary materials. A failed collection roll still spends the energy. An encounter prevents further gathering until resolved.
4. Defeating the site enemy adds a bonus of the same targeted material to the expedition haul. The amount must be priced into total expected yield; fights cannot become a free infinite-material loop.
5. Extracting banks the haul into the Materials compartment. Dying loses **all materials collected in that expedition**, including enemy bonuses, while pre-existing materials remain intact. Running away, disconnecting, and death-prevention effects need explicit rules; do not let reconnecting bank the haul automatically.

Suggested starting experiment: ordinary gathering success 35–70% depending on site/tool; encounter chance 3–8% per attempt. These are test ranges, not approved universal probabilities. A longer trip should create a visible risk/reward decision. Existing combat energy and death policies must be reconciled so a gathering encounter does not silently charge an unexplained second entry cost.

## Proposed phases

### Phase 1 — tools, site data, expedition state

**Goal:** One eligible player can open a correctly gated site and spend energy into a separate, persistent haul without creating a normal-inventory gain yet.

**Steps:** Define the eight site records in content; add instance-aware tool checks and versioned expedition state; add begin/attempt/extract actions through the same engine used by local and worldd play. Existing and newly provisioned players inherit the same defaults. Record a pre-migration player snapshot before the first write. Write and commit a phase-specific implementation plan before code execution.

**Verification:** Replay a fixed seeded attempt sequence; compare starting/ending energy and haul quantities; verify wrong tools, wrong floors, repeated requests, and full ordinary packs. Execute the phase-1 [dojo scenario](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plans/013-mining-and-gathering/DOJO-SCENARIOS.md).

**Rollback:** Disable new expedition starts; settle or restore in-flight expeditions from the migration/transaction journal under a documented policy; revert the site/state commit. Never remove a haul field while it contains earned units.

**Execution status:** Not started.

### Phase 2 — encounters, victory, loss, extraction

**Goal:** Site fights use the actual combat engine; victory adds the targeted material; death removes only the current expedition's haul; extraction transfers exactly once.

**Steps:** Author themed encounters, integrate encounter interruption and return-to-expedition flow, settle bonuses and losses atomically, and define death-save/retreat/disconnect outcomes. Price gathering yield and fight bonuses together. Preserve personal materials from before the expedition.

**Verification:** Force success, empty roll, encounter victory, defeat, retreat, reconnect, and duplicate extraction in test fixtures; then perform actual browser fights for the corresponding scenarios. Verify player documents and ledger deltas, not only the receipt text.

**Rollback:** Disable new site encounters; finish or compensate in-flight fights via recorded before/after state; revert the encounter integration commit while retaining readable expedition records.

**Execution status:** Not started.

### Phase 3 — maps, route economics, release

**Goal:** Eight discoverable map sites deliver deliberately different but viable gathering routes without making creature hunting obsolete or bypassing high-floor access.

**Steps:** Add site markers and tool/source hints to the existing map UI. Compare materials per energy, gold/XP opportunity cost, tool repair costs, encounter survival, and loss-adjusted return with hunting. Canary one account before broader migration; update the plugin and worldd vendored engine; deploy only through an explicit execution plan.

**Verification:** Targeted tests, full suites, floor-specific browser walkthroughs, two-account isolation, server logs, and an end-to-end gather → extract → Forge upgrade. Run the Legendary access scenario and compare an informed route with a poor route.

**Rollback:** Disable new starts, hide site markers, preserve or settle active hauls, revert the exact release commits, verify old hunting and Forge upgrades remain available. Record concrete SHAs and snapshot identifiers in the execution plan before rollout.

**Execution status:** Not started.

## Operational notes

Every attempt and extraction needs a stable idempotency key and server time. Persist rolls before presenting their result. Test login/reconnect without free rerolls, and isolate one player's haul from another's. Keep all material arithmetic integral and all API quotes authoritative.

Do not run the site actions as unattended energy automation; each expedition is a player activity. Do not add the mine reward tables into the weapon release's guaranteed supply. Once mining becomes available, revisit material requirements using observed route behavior rather than assuming the original drop-only schedule remains balanced.

This draft note is reversible by removing the two new files in `plans/013-mining-and-gathering/`. There is no runtime rollback to perform because no phase has been executed. Before implementation, expand each phase into its own committed `phase-N/PLAN.md` with exact commands and concrete inverse operations.
