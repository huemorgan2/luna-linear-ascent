# Audit of the first progression simulator

12 September 2026. Sources are local research and the pinned release `1897edd615682c6a960101adaa5299b986f681df` (game 0.112.0/wiki 089.3). The existing JSON is retained; no live accounts or production balance were changed.

| Mechanic | Source / agreed rule | First simulator | Audited treatment |
|---|---|---|---|
| Three slots, energy, haul and kill XP | User decisions; [group research](../combat-atlas/DECKS-AND-MONSTER-GROUPS.md) | Three, 1 energy on enemy entry, XP per kill, loot on full clear | Retain; contract tests and playable same-engine prototype |
| Weapon/material/gold growth | [upgrade research](../weapon-upgrades/RESEARCH.md), frozen wiki states | 84 states, four grades, 16 families and per-species unequal drops | Retain 1.3 capital/power and 1.25 income; no extra hone multiplier |
| Repair basis | Research: never charge a percentage of historical cumulative upgrade payments. Economy `repair_price`: running price discounted at item's gate | Cumulative spend ×0.20 / pacing wedge | Correct to a single equivalent capital value `200 × 1.3^(gate−1) × family cost`, discounted by 1.04^(gate−1). The 200 anchor and continuous basis are an explicit candidate; 0.13 comes from the pinned repair coefficient. This is not a live catalog adapter |
| Upgrade wear | Preserve **absolute missing durability**; broken items must be repaired first | Preserved missing percentage; allowed broken upgrades to be considered | Preserve missing units; reject broken-item upgrades; durability-only steps still offered |
| Damage floor | [combat proposal](../combat-atlas/PLAN.md): retain 15% of attack before affinity when flat defense dominates | Flat subtraction could collapse to 1 before affinity | Apply the documented 15% floor, retain seeded hit variance and range/affinity |
| Shield capacity | Combat proposal: `50 × shield DEF/2` absorbed-damage endurance | `max(1300,80×DEF)`, far more generous early | Correct to 25×base DEF; damage absorbed alone spends capacity. Shield repair cost remains a disclosed local-income candidate |
| Farming fade | Pinned `economy.fade_multiplier`: no loss within five floors, minimum 25% | Fade immediately below frontier, down to 10% | Restore the pinned five-floor grace and 25% minimum |
| Starter recovery | Pinned class starters: permanent, +5 attack, 1-gold repair, half contribution when broken | Three paid-equivalent starter weapons; no retained basic tools, broken weapons dealt zero | Keep the opening gifts for comparability. Candidate recovery modes separately enable retained +5 basic blade/staff or partial paid repairs. Basic tools use one of the same three slots, have no special effect, and cannot be upgraded/sold as paid weapons |
| Current condition | Damaged drops should need repair to recover performance; exact paid-weapon curve not frozen | Weapon contribution scales linearly to zero | Retain and label candidate. Retained basic tools have a half-contribution floor; that protection does not apply to paid gear |
| Healing | Pinned wound-scaled price is correct: 6 base kills for full HP | Buys full heal below 65% before every other consideration | Keep price, expose scale as experiment only; smarter policies can rest or farm safely instead of spending all cash |
| Character training | Pinned XP/gold prices and level-30 cap | Exact prices, but spending greedily precedes everything else | Preserve prices; smarter policies protect upkeep money and compare training with gear gains |
| Defense acquisition | No new complete armor/shield shop defined by this weapon proposal | Reference defenses, price derived from 2/3 of honing quote | Remains explicit approximation; do not claim production timing parity |
| Shops, arrows, drops | Wiki starting levels/conditions/gates; ordinary paid arrows need supply | Correct starting settings, but no same-grade replacement decision; immediate salvage of unused drops | Add inspectable replacement decisions. Gold-priced arrows, simplified pack storage and 2% salvage remain candidates. No perfect future-loot knowledge |
| Death | Persistent upgrades requested; exact condition penalty unresolved | 50% purse loss, 10% condition loss, beginner gold protection | Keep as visible candidates; avoid calling them old live death rules |
| Group construction | Research asks for unequal roles and profitable alternatives | Whole monster draws, 2–6 typical, often contact arrivals | Retain the baseline for controlled comparisons; HP multiplier and route selection remain separate experiments, not hidden global nerfs |
| Readiness | Prepared-resource probe estimate, not sustainable profit | Eight probes; 7/8 needed; checked when gear bucket changes | Retain rule, report last failed probe, restored-gear/next-gear diagnostics and final-day resources. Prepared capability and profitable repeated hunting are separate |
| Wardens | Shared HP, continuous fixed healing, finite energy | Implemented proposal, direct attacks only | Retain; do not raise healing to cancel smarter player improvements. Report observed hunters separately from reference gear |

## Baseline preservation

`proposal-v1` retains the original player decisions and original combat branches. `simulation/data/v1-reference.json` records the original full-HP 24-player/120-day run's config and player/floor/warden digests. New metadata and diagnostic fields are not evidence of a gameplay change; compare outcome digests and explicitly saved revision/settings. Old saved files lacking a model revision must be displayed/copied as v1.

## Remaining omissions

No live shop transaction adapter, race/faction/School mastery, quests, trade, pack travel, rested-XP system, multiplayer world-unlock calendar, mine economy, or shared-boss statuses. Dawn recovery and averaged sleep energy remain simplifications. A local prototype can establish that choices/resources work and expose pacing problems; it cannot establish human retention or enjoyment. Production deployment of the new combat still belongs to plan 015.

The first floor-12 interpretation was therefore incomplete: the chart correctly reported the program's output, but that program had several mismatches with its intended inputs and weak recovery decisions. Correct those before treating the old stall as game-design evidence.
