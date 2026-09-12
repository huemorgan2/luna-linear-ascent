# Phase 3 — A complete first-ten-floor play loop

## Goal

Make a fresh player complete hunt → materials → Forge → +1 upgrade → meaningful counter-choice → recovery in one coherent QA experience. Show this milestone before expanding all 100 floors.

## Steps

1. Implement a small complete selection of Common blade/bow/staff families, rather than enabling every ability at once. Include a basic damage option, a positional opening and a lasting effect so the new decisions can be assessed.
2. Wire actual creature drops, the separate Materials compartment, starter access, the authored opening material reward, atomic Forge quotes, repair and source-condition settings. Reach the floor 2 upgrade through normal starter resources; later early-game upgrades should require hunting.
3. Implement the required damage/reach/shield/movement rules together with their UI. Shield wall may improve defense but at least25% of a landed covered hit reaches HP. Incoming wear is charged only to the shield's absorbed share.
4. Teach one new idea at a time: ordinary targets first, reach and affordable anti-air before a required flyer, then affinity and timing. The wiki's Air Power spell-dispersal exception must be visible on that creature.
5. Render exact costs, next-stat deltas, distance, status duration and action readiness in game cards and plain text. The outside card navigates to the Forge; it cannot upgrade in combat or teleport the player.
6. Provide a QA-only teaching warden fixture to assess the first 10-floor experience. Production shared-warden migration is reserved for phase 6.

## Verification

Run targeted engine/Forge tests and both backend contracts, then dojo S03/S04/S05 with a new character through Luna and web play. Exercise click and plain-text selection, insufficient funds/materials, +0/+1, a full ordinary pack, death and a broken weapon. Record starting/ending resources; no developer grants or energy refills may rescue the walkthrough.

## Rollback

Disable the candidate rules in the isolated QA world and revert the phase's implementation commits. Preserve schema adapters from phase 2. Nothing in this phase is released alone to the shared production world.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
