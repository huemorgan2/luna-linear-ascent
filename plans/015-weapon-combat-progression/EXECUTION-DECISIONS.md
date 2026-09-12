# Execution decisions — gathering and smart progression

12 September 2026. The user authorizes the complete phased build, autonomous decisions and repeated game/simulator improvement. This document is committed before implementation and overrides older “mining separate” / “awaiting review” wording. The existing eight phases remain the execution sequence; gathering is part of phases2–5 and their release/rollback coverage.

## Goal and fixed choices

Use the actual game and shared services for all outcomes. Build a playable, attractive three-slot/group game, keep School non-slot training, preserve distinct weapon/monster identities and rising resistance icons, and prove that competent strategies—including saving/investing in the Vault—can follow a gradually slowing capability curve. Weak/random players may stall and ordinary strategies may advance more slowly. Do not flatten counters to rescue every bad deck.

Choose the documented sequential-first design, normal XP for exhausted kills, overflow reserve, and 50% outgoing damage / −2 speed initial exhaustion. The initial personal-capability target remains extra days =0.15×1.04^(floor−2); this is an optimization target for strong repeatable policies, not a promise for a random-population median or actual world unlock time. Use a tolerance envelope and inspect cliffs; never fabricate a curve. Preserve existing legitimate Vault returns, funding/collection timing and costs. Investment is useful when its time horizon beats an immediate upgrade, not compulsory for every purchase. Learn policy quality before retuning the game.

## Named gathering locations

The player sees the place name and resource, never a generic mandatory “mine.” Eight locations are available by floor80, with late Legendary resources gated high. Initial authored settings follow the earlier biome research; content lint/actual map inspection may refine names/species without moving access silently.

| Floor | Location | Resource | Tool | Favored combat approach |
|---|---|---|---|---|
| 3 | Drowned Copse | Wood | Wood axe | Bows versus fast birds/moths; a Magic guard can favor physical backup. |
| 3 | Bog-Iron Field | Raw Metal | Pickaxe | Blades versus ground Magic burrowers; occasional Power shell needs magic. |
| 18 | Tempered Scrap Seam | Steel | Hardened pickaxe | Blades against magic-bound ground sentinels; control prevents their heavy attack. |
| 25 | Buried Heartwood Grove | Hardwood | Steel wood axe | Bow/arrow choices versus airborne nest hunters; a grounded ward adds variety. |
| 45 | Starforge Slag Beds | Starforged Steel | Heat-resistant kit | Blade/control versus ground Magic remnants; Power slag creatures reward a staff. |
| 55 | Fallen-Star Crater | Meteorite | Impact pick | Bow coverage versus crater flyers; a Power shellback rewards magic. |
| 70 | Shard Fissure | Shard Matter | Shard extractor | Blades versus Magic ground fractures; occasional Power crystal guard. |
| 80 | Mythic Loom Hollow | Mythic Threads | Harvesting shears | Bows versus thread-wing hunters; Magic/Power ground spiders vary the answer. |

These are intentionally tilted compositions, not exclusive weapon locks. Bow recipes consume more A material, blade recipes more B, staves need both; the locations should help a player improve that approach while retaining some complementary threats. Retain425 existing creature identities and add site-specific variants/species where needed, with distinct/fitting art and at most three near-identical variants. A location cannot require the weapon grade the player is still collecting materials to craft. Tools are separate utility equipment, not a fourth combat weapon. A normally affordable tool/repair route must precede access.

## Expedition loop and costs

At the gate/map show the location name, target resource, required tool, favorable weapon types, danger and expected return. Opening the location is free. Starting the expedition locks the three selected weapons and the tool; current stock/resources are separate from its unbanked haul.

Each Gather action requires and spends one energy exactly once, wears the tool by its specified amount and rolls for the target resource and an ambush. Gathering at zero energy is unavailable; fighting an ambush at zero energy still follows the normal exhaustion rule. Initial success/risk ranges35–70% and3–8% are candidates, with unequal yield/tool/site differences. State the extra risk clearly: each enemy that actually engages in an ambush costs its own one energy, in addition to the gathering attempt. No charge for unstarted enemies. Reserve-energy decisions are a useful policy.

An ambush is a themed group of at least two, with the usual per-kill XP, committed deck and resource carry-over. Full ambush victory returns to the same expedition and adds its targeted-resource bonus to the unbanked haul. It does not automatically extract or grant town recovery. A successful flee/extraction rescue from an active ambush abandons the entire expedition haul. Death likewise loses only this expedition's collected/bonus resources, plus the separately defined ordinary death penalties; previously secured materials remain intact. In-place revival preserves the expedition and receipts.

When no ambush is active, Extract secures the current haul exactly once and exits. Disconnect/refresh preserves state, never rerolls or banks it. Tools cannot be repaired or replaced remotely while locked. If a tool breaks, allow extraction and a visible recovery route; do not strand the character. Full-pack/overflow handling uses the same ownership guarantees as group victory.

## Return and progression tests

Prepared gathering should deliver a measured upgrade-material advantage over hunting alone, after tool purchase/wear, travel, ambush energy, deaths, failed rolls and lost hauls. Initial target is approximately1.5–2.5× secured targeted materials per comparable energy/active time on the intended site/grade, not a mandated equality between all sites. Report the whole recipe completion time too: abundant Wood alone does not solve Raw Metal starvation. Hunting keeps its gold/XP and varied-drop advantages. Test hunting-only, gathering-only, mixed, deep, riskier long expeditions, cautious extraction and wrong-deck miners under matched seeds; mandatory upgrades remain attainable without a rare item drop.

Add software policies: legal random actions, random loadouts, ordinary learners, counter-aware specialists, material-route planners, early/late extraction policies, immediate spenders and Vault investors. Separate policy RNG from game RNG; no hidden/future information. Search upgrade-versus-invest choices with a retained cash/repair/energy reserve, then validate winners on fresh seeds and against random/ordinary baselines. The strongest repeatable strategy must meet the curve envelope without requiring a lucky singleton; retain fastest observed alongside median and quantify the success/reach population. Do not interpret a large gap alone as proof of skill.

Trust gates: direct-engine parity and replay; immutable probes; exact receipts; no illegal-action loops; serial/all-CPU semantic identity; equal policy schedules; held-out seeds; confirmed Vault return once at real game time; browser-confirmed flows. Extend shared-service headless trials for wards/real world access before claiming multiplayer days or party sizes.

## Phase additions and verification

Phase1 incorporates published baseline and reproduces Vault timing in the existing engine. Phase2 adds utility-tool ownership and expedition/ambush/haul state with local/HTTP contracts. Phase3 includes the two floor3 sites, gate visibility and gather→ambush→extract→Forge in the complete opening. Phase4 adds all eight sites, themed creatures, art, wiki parameters and drop/yield/tool definitions. Phase5 iterates actual-game economy and simulator policy/search until competent paths approach the reviewed target; phase6 rechecks with actual shared wardens. Phase7 rehearses active-expedition migration/rollback and real multi-client play. Phase8 ships the complete coherent version only after verification.

See dojo S15 for the new site scenario. Add targeted tests for attempts, no energy, tool gates/wear/breakage, seed persistence, ambush cost/XP/bonus, flee/death/revive, reconnect, duplicate extraction and pre-existing materials. Run required full suites and actual web/Luna walkthroughs per phase. Commit configuration changes with matched experiment evidence, not unrecorded tuning.

## Rollback and execution notes

Documentation rollback is reverting this revision's commit. Implementation commits are recorded per phase. Before data writes, preserve original documents and stable receipts. Stop new expedition starts, allow safe extraction/explicit settlement of existing hauls, retain readers and compensate by receipt; never restore an old whole-player snapshot over later progress. No production secrets or real player data enter run artifacts. Local tests use isolated worlds/accounts. This authorization covers autonomous reversible implementation and QA; irreversible production data operations retain the project's confirmation requirement.
