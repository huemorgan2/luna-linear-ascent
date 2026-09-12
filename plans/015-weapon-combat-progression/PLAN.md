# 015 — weapons, combat and player progression

12 September 2026. **Implementation plan; runtime work has not started.** The public wiki is a design reference, not evidence that its combat, loot or Forge rules already run in the game.

## Problem, evidence and timeline

The 11 September research replaced a large mostly attack-based catalog with persistent weapons and tactical identities. The 12 September wiki now shows 16 families, 64 different grade drawings, 425 authored creatures, source settings and proposed loot rates. The next task is to make that loop work for actual players.

Inspection of game 0.112.0, as vendored in release 4e052b1, confirms that the engine still uses the old item/honing model, mutually exclusive enemy types, complete protection in the Shield wall branch, and two different shared-warden paths. Ordinary warden damage is reported at the end of an exchange; milestone floors use pledges and an aggregate-power resolution. The current per-swing energy charge does not match the whole-exchange unit used in warden sizing. This is a source-supported calibration concern to reproduce in phase 1, not a claim of a measured production outage.

The existing 84-state neutral upgrade table matches the reference weapon contribution across all 100 floors. It does **not** validate new statuses, family premiums, ammunition, repair losses, gold balances, XP, or finite-energy group combat. Earlier +0.18% effort-index parity is not a forecast of player progress or season length.

## Root cause

Item identity, combat choices, resource supply, UI and boss timing have evolved separately. A visually correct weapon table can still produce an unaffordable counter, a repair trap, an obsolete upgraded weapon, or a boss no real group can finish.

## Emergency mitigation

None required for this planning task. Keep the current runtime while the replacement is developed in an isolated QA world.

## What we are building

- 16 weapon families × Common/Rare/Epic/Legendary, each +0–20, with the wiki's 64 distinct drawings and grade frames.
- Individual weapon instances: levels, condition, ownership and history belong to that item. Techniques work from +0; levels improve attack and endurance without extending stun indefinitely.
- 425 authored creatures on their actual floors. Separate Ground/Air, Common/Power/Magic defensive affinity, outgoing attack channel, and species traits. Preserve identities, art and ecology; at most three nearby variants of one animal.
- Persistent distance, useful speed, poison/burn/bleed, push, stun, slow, Expose and six arrow payloads. The first release adds no boss-healing suppression or passive energy regeneration.
- Eight materials, unequal creature drops, stronger deep-hunt rewards, and useful choices of hunting trail. Mining and its expedition-loss rules stay in plan 013.
- Forge-only upgrades, visible gathered/required materials and exact gold, shop/drop/craft starting settings, and recoverable weapon investment.
- One shared warden health bar with healing over actual time. Accepted attacks damage it immediately. No pledge pool, combined-stat victory or timezone-compensation mechanic.

## Progression rules to protect

Keep the power/capital scale 1.3 per floor, income scale 1.25, pacing ratio 1.04, warden growth factor 1.02, character cap 30 and ten equipment/energy bands as reference anchors. Keep rarity, weapon level, character level and effective progression floor separate. Weapon upgrades replace weapon honing; never multiply both. Removing its XP cost must be included in character-level pacing.

The reference is a measuring stick, not a requirement for equal damage or equal progress. Family factors, counters, species, preparation and routes must produce different outcomes. A clever player can skip an inefficient purchase, use a specialist, farm the right carrier and move faster.

| Grade | Native floors | Materials | Forge delivers | Shop delivers | Hunt drop delivers |
|---|---|---|---|---|---|
| Common | 1–25 | Wood + Raw Metal | +0, full condition, floor 1 | +0, full, floor 1 | +0, 40% |
| Rare | 26–50 | Hardwood + Steel | +0, full, floor 26 | +2, full, floor 28 | +0, 30% |
| Epic | 51–75 | Meteorite + Starforged Steel | +0, full, floor 51 | +4, full, floor 57 | +0, 20% |
| Legendary | 76–100 | Mythic Threads + Shard Matter | +0, full, floor 76 | +6, full, floor 84 | +0, 10% |

Rare/Epic discoveries can occur earlier at the wiki's small rates. Legendary discovery begins at 50; equipping the dropped item still requires76. Character and access gates are checked independently. An item +0 is not comparable across grades by its level number alone; show actual before/after performance. Native-grade crafting bridges the gap before higher-level shop stock, but crafting is not a guaranteed acquisition route unless its materials are obtainable too.

Default design recommendations to validate: upgraded weapon levels survive ordinary death; death adds repair loss rather than deleting the investment. Ordinary Materials storage is safe. Existing beginner/protection rules take precedence. These reduce old loss sinks and must be priced in the account simulation. On an upgrade, preserve the item's remaining-condition fraction against its new maximum; do not grant a hidden full repair. Broken weapons remain broken until repaired. Shop/craft full condition and damaged drops are explicit source exceptions.

## Steps and completion gates

Each phase has its own [goal, steps, verification and rollback](phase-1/PLAN.md). Implementation is sequential; every phase must pass before the next expands scope. Phases2–7 run behind a versioned ruleset in QA, not as incomplete production features.

| Step | What players will eventually receive | Evidence before proceeding |
|---|---|---|
| [1. Measure the current game](phase-1/PLAN.md) | A tested pacing baseline and a defined action clock | Existing hunts and both boss paths reproduced with finite energy; actual client latency recorded |
| [2. Establish shared data and safe item conversion](phase-2/PLAN.md) | Persistent weapon identity; consistent stats and art everywhere | Every old item/storage case maps safely; no silent loss or duplicate instance; migration can be rerun |
| [3. Build a complete Floors1–10 loop](phase-3/PLAN.md) | Hunt → collect → Forge → upgrade → useful counter → recover after loss | A fresh character completes the loop in real Luna and web play without developer gifts/refills |
| [4. Expand combat and content](phase-4/PLAN.md) | All64 weapons,425 creatures, effects, arrows and readable fight controls | All families have a tested useful role; reach, status clocks, shields and movement work together |
| [5. Balance the whole climb and economy](phase-5/PLAN.md) | Meaningful upgrades, viable material routes and affordable recovery | Whole-account simulations, native-grade access, median and P90 effort pass across floors 1–100 |
| [6. Replace shared wardens](phase-6/PLAN.md) | Real concurrent attacks against continuously healing HP, including100 | Discrete attacks with finite energy prove group wins, appropriate solo failure and one-time rewards |
| [7. Play through and rehearse conversion](phase-7/PLAN.md) | A coherent game for new and returning players | Real multi-turn Luna, web/mobile and multiple-player scenarios pass; migration and rollback rehearsed |
| [8. Release and measure](phase-8/PLAN.md) | A verified release with preserved player progress | Isolated-world canary, explicit deployment, public verification and measured progression gates |

The first visible milestone is step3. We will show that complete small loop before building out the rest of the tower. A phase 3 warden fixture is a QA teaching encounter; it does not claim that multiplayer phase 6 is complete.

## How we judge playability and progression

These are **proposed starting acceptance targets**, to freeze against measured phase 1 data before implementation expands. They are not measured results or promises of equal outcomes.

| Concern | Proposed launch gate | What happens if it fails |
|---|---|---|
| First session | Starter gear and the floor 2 +1 upgrade are reachable through the authored opening rewards and normal available energy; first 10 committed actions teach a clear next goal | Change opening rewards/tutorial cost or instruction; do not raise rare-drop odds globally |
| Ordinary hunting | Prepared reference characters win at least80% of eligible ordinary encounters in each tested band; runts and alphas are reported separately | Inspect a counter/access or survival failure; deliberate elite fights need not meet this rate |
| Spending has a purpose | Every paid upgrade improves displayed attack or useful endurance; durability-only levels are identified | Change the recipe/gate or the presentation; never advertise a nonexistent damage gain |
| No resource dead end | Both native materials and at least one affordable answer to every mandatory encounter are reachable before they are needed | Add a fitting hunting trail or adjust that floor's supply; a rare weapon drop cannot be compulsory |
| Bad luck | P90 time to required native materials is at most2× the median on a sensible route | Tune a native-grade dry-streak safeguard; keep early Epic/Legendary discoveries exceptional |
| Gold pressure | Median time to reference progression milestones starts within±15% of the measured old whole-account route, unless a deliberate change is recorded | Adjust actual net-income/upgrade sinks; do not infer parity from nominal sticker prices |
| Smart play | Demonstrate roughly 25–50% faster progress to representative upgrades through route/loadout/upgrade choices | Improve actionable information and specialization; larger local advantages are allowed |
| Choice remains useful | No family is strictly outperformed in every intended matchup/resource situation; no one loadout wins every comparison on damage, safety and cost | Rework a redundant family or a universal interaction; equal win rates are not the objective |
| Recovery | After death or breakage, a legal starter/repair/recovery route can earn the cost of returning to play without an unaffordable counter dependency | Adjust recovery access or repair basis; retest repeated losses |
| Deep hunts | Better rarity per successful kill; a demonstrated net reward advantage for suitably prepared builds after two entry energy, failure, healing and wear | Tune species/mode premiums; ordinary hunting stays viable for weaker builds |
| Cooperative finale | A prepared reference group can finish within its real energy/HP window; no legal single-account endgame build can burst or sustain the kill | Tune HP/healing/cadence together; do not just compare average DPS |
| Reliability | Zero duplicate charges, items, kills, refunds, rewards or era closure in the concurrency/retry suite | Block release and correct the transaction path |

P90 means90% of the simulated players finished within that effort; also report non-completion and P99, rather than discarding stalled characters. Material tails, gold tails and full progression tails are different metrics.

The native-grade safeguard is a proposed adoption of the research's optional rule: after a tuned number of eligible wins without that grade, award one ordinary bundle with the defeated creature's normal carrier ratio. It persists across sessions and cannot accelerate higher-grade discoveries before their native band. The wiki must show both base probability and the actual safeguard state. The opening tutorial reward is separate. Neither changes all monsters to equal drop chances.

Simulate at least10,000 seeded progression runs per representative policy cohort after a smaller calibration run. Compare baseline and proposed systems using paired seeds where meaningful. Include ordinary, informed and deliberately poor routes; new accounts, returning characters and wealthy/overprepared legal builds; multiple races/paths; at least a main weapon plus a practical counter. Report actual gold balance and interest, XP/training, energy waiting, healing, ammo, repairs, death, both material bottlenecks and contribution to bosses. No infinite bags of gold or per-round energy refill. Separate personal economic effort from the availability of a concurrent party. Do not promise a season duration from the current income formula.

## How teamwork grows

These are reference tuning targets, not a headcount gate. Fit a smooth rising group-demand curve and validate each floor rather than introducing a sudden jump at a table boundary.

| Floor range | Intended experience |
|---|---|
| 1–9 | Solo learning; healing low enough for the intended starter/reference path |
| 10–25 | Small groups become necessary at frontier strength; roughly 2–5 prepared players |
| 26–50 | More combined damage and complementary tools; roughly 5–12 |
| 51–75 | Organized concurrent attacks; roughly 12–25 |
| 76–100 | Large groups; roughly 25–50, with floor 100 initially tuned around 50 reference players |

At floor 100, roughly 35 well-prepared specialists winning where about 50 ordinary prepared players are needed is a useful test case, not a guaranteed result. Do not resize the boss when the actual party improves its equipment. An overprepared character defeating some early gates is acceptable; the late solo ceiling must include legacy items and all legal bonuses.

The necessary check is:

`time to kill = remaining HP / (actual group DPS − healing per second)`

It must fit the group's energy and survival window. Final proof uses timestamped individual attacks, misses, setup, status ticks, withdrawal, reconnect and ordinary UI latency. A positive average margin alone is insufficient.

Keep server acceptance cadence explicit and playable through both Luna and web cards. More browser tabs or faster duplicate clicks do not buy extra turns. Boss DoT clocks are real-time and independent of how many players click; stun resilience is shared; push only changes the acting player's gap. Preserve the research's simple healing rule rather than layering stored contributions or timezone windows over it.

## Release and migration safeguards

Before migration, inventory all old weapons, honing, styles, oils, wear, held/equipped slots, pack/storage, offers and pending rewards. Preserve instances individually. When no fair new state exists, retain a functional legacy item and an explicit conversion path; do not silently round down paid power or bypass an unopened gate. Include those retained items in the endgame solo-ceiling check.

Keep compatibility readers and append-only migration/transaction receipts. Never restore an old whole-database snapshot after players have earned new progress. After new writes, rollback means disabling the new mutations while keeping readable items and using idempotent compensating operations where required. Exact commands and receipt identifiers are recorded before each implementation phase is executed.

Wardens require a separate conversion boundary: no mid-fight silent HP reset; resolve/migrate active wounds explicitly, refund unconsumed pledges once, and preserve historical kill/era records. The real floor 100 death must invoke era closure once.

Canary the new shared rules in an isolated QA world first. Do not put old and new combat rules on different participants in the same production boss. Production stays on the existing single-instance deployment topology. Deploy the pinned plugin implementation, matching worldd vendor, clients and wiki definitions together; verify the actual serving version after deployment.

## Operational notes and ownership

The runtime work spans the plugin engine/content/cards and worldd's authoritative actions, ownership, rewards and persistence. Use the project devprocess: committed plans and dojo scenarios first; implementation branches in the owning repositories; plugin commit → parent pointer/vendor → targeted tests → full suites → real Luna walkthrough → explicit deployment → post-deploy verification. The local and HTTP backends must obey the same rules.

The runtime content becomes the canonical source for live definitions and the wiki generator. Preserve a separately labeled proposal where necessary; do not maintain two competing live balance tables. Rebuild tool descriptions and card payloads, not just HTML. Existing PvP, trade, gifts, pawn, storage and rewards must understand the new item instance schema. Monster-control mechanics must not silently become untested PvP effects.

## Sources and prior decisions

- [Current published wiki](https://linearascent.net/wiki) and [released model](https://github.com/huemorgan2/luna-linear-ascent/blob/4e052b184f15177dd8f8c40b13893d23582a7e33/worldd/static/site/wiki/model.json): source levels, condition, loot and64 art records.
- [Combat proposal](../../research/combat-atlas/PLAN.md): family roles, counter matrix, damage and effect timing. The wiki supersedes its eight-species prototype and older frame colors.
- [Progression tables](../../research/weapon-upgrades/PROGRESSION-TABLES.md) and [validation limits](../../research/weapon-upgrades/VALIDATION.md).
- [Boss-system analysis](../../research/weapon-upgrades/BOSS-SYSTEMS.md): timing, energy-unit mismatch, pledge replacement and finite-energy group math.
- Source anchors at release 4e052b1: `worldd/vendor/plugin_linear_ascent/economy.py`; `engine/state.py`; `engine/combat.py` (Shield wall, per-swing energy, exchange report); `worldd/app/social.py` (shared pool and `_fx_boss_commit`).
- [Mining stays separate](../013-mining-and-gathering/PLAN.md).

## Verification and rollback of this planning task

Check every local Markdown reference and each phase's Goal/Steps/Verification/Rollback/Execution status. No runtime tests or player walkthrough can validate unimplemented mechanics; those remain mandatory phase gates. This task only writes plan/research documents. Its rollback is reverting this documentation-only commit, preserving all unrelated work.

## Execution status

Planning complete. Phases1–8 are not started. No engine changes, migrations, balance simulations, gameplay dojo or production deployment were performed for this plan.
