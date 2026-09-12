# Phase 4 — Full arsenal, bestiary and routes

## Goal

Expand the working group loop to all 16 families / 64 grade variants and 425 authored creatures, with meaningful unequal niches, readable images/traits, valid sources and a matching generated wiki.

## Steps

1. Port approved family/grade/source/art records from wiki model revision089.3 into canonical runtime definitions. Extend lint/schema checks for distinct images, material/icon/frame mapping, grades, +0–20, probabilities and source gates. Preserve the original creature roster and neighboring variant/biome identities.
2. Implement all seven effects and six arrow payloads, source snapshots, exact timing, immunities, cooldown carry-over, control resistance and condition-dependent stats. Avoid double old/new type multipliers, double exhaustion and percent-max-HP boss damage. Preserve the resolved channel/cause for resistance popups across ordinary/arcane/fire arrows, damage ticks and Spell dispersal; the icon follows the actual resisted component, not the weapon family or defender badge.
3. Author groups/trails over floors1–100 using real local creature IDs. Candidate ranges: 2 on1–3; 2–3 on4–10; 2–4 on11–25; 3–4 on26–50; 3–5 on51–75; 3–6 on76–100. Keep shorter later routes. Do not multiply count by old full-monster threat/payout blindly.
4. Configure group arrival gaps and durable/fragile/fast roles. Ordinary and deep mode use one energy per begun enemy; deep danger, specimen mix and each rarity premium remain separate. No hidden deck-dependent counter-spawning or free preview rerolls.
5. Wire per-enemy independent material grades and categorical item rolls with actual family/carrier weights, source-specific +level/condition and Forge crafting at grade transitions. Update all reward, pawn, storage, trade/gift and equipment consumers.
6. Generate wiki/art payloads from the runtime definitions, with full creature parameters, individual/group conditional odds, deck coverage, acquisition and Forge recipes. Mark any unreleased settings as proposed. Audit avatars/3D weapons and fallback images so grade selection does not revert to one drawing.
7. Prove each family has a useful tested context; document blind spots and cost. Do not require equal win rates. Two-active-enemy waves remain an optional future prototype outside the release gate.

## Verification

Run content lint and `python3 worldd/tools/gen_wiki.py --check` after the generator reads runtime definitions; add exact distribution tests for caps/no-drop/family weights and integer/rounding tests for statuses. S04/S05/S07/S12 verify contrasting decks, push→bow/escape, poison→switch, repeated stun resistance, source gates25→26/50→51/75→76, paid Legendary+6 versus dropped+0/10%, all425 IDs/images and floor-slider changes. Review a coverage table per family/route and group duration/action distributions. Required full engine/service/simulator suites follow targeted tests.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Revert candidate content/effect/art/wiki commits in QA in reverse order while retaining state compatibility. Pin the prior content/rules revision for already-started groups and outstanding quotes; never reinterpret pending loot with a different probability table. Keep newly owned item records readable and reconcile any necessary conversion through receipts.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Not started. Rewritten for the three-weapon/group design on12 September2026; awaiting the user's plan review. This document is not evidence that runtime changes or tests have run.
