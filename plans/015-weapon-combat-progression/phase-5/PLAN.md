# Phase 5 — The complete economy and progression curve

## Goal

Show that ordinary and informed players can fund survival and progress across100 floors, with better decisions yielding a measurable advantage and bad luck unable to create a resource dead end.

## Steps

1. Apply the84 neutral upgrade states once, all family recipes and shop/drop/craft settings. Preserve grade-transition crafting at 1/26/51/76 and shop delivery at 1/28/57/84.
2. Implement material and item rolls using the wiki's floor/species/specimen/deep modifiers. Materials are independent grade rolls; weapons use one categorical roll including no weapon. Keep rates unequal and show individual family odds.
3. Add a small set of fitting hunting trails where the roster supports them. Trails alter encounter weights, not a free reroll; show carrier/danger before energy is spent. Ensure both materials remain reachable.
4. Calibrate and expose the proposed native-grade dry-streak safeguard. It must retain carrier ratios and never guarantee early Epic/Legendary discoveries. Include the safeguard in all published probabilities and simulations.
5. Set repair, ammo and resale formulas against actual net earnings. Preserve condition fraction on upgrade and avoid repair/reforge/resale loops that create currency. Account for removed weapon XP honing and preserved levels/materials on death.
6. Run baseline/candidate policies with paired seeds: ordinary, informed, wrong-counter; main weapon plus counter; saving versus upgrading; normal versus deep; migration and wealthy cases. Analyze each material bottleneck, not just total units.
7. Publish tables of median/P90/P99 effort and stalled runs for each floor and grade boundary. Record every changed coefficient and its reason.

## Verification

Run `python tools/progression/run.py --rules candidate --floors 1-100 --runs 10000 --seed 1501 --output output/progression/candidate`. Compare with phase 1 and the main acceptance table. Run dojo S07/S08 at boundaries25→26,50→51,75→76 and shop gates28/57/84. Test unlucky paths, zero-gold recovery, an unaffordable secondary weapon, and repeated deep-hunt losses.

## Rollback

Revert candidate tuning/configuration in QA and rerun the same seed set. For any later live tuning, version outstanding quotes and preserve already-completed transactions; never charge a player retroactively.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
