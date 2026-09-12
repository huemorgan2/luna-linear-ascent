# What this simulator measures

This is a proposal simulator, not a replacement for the production resolver. No LLM, network, production account or database is used by a run. Inputs are frozen from game 0.112.0/wiki 089.3; `data/inputs.json` records the source commit and SHA256 hashes. The run also records the complete configuration, input hash and simulator-code hash.

## Fixed design rules

Three weapon instances, sequential groups, one energy when each enemy begins, normal performance when the last point pays for that enemy, exhaustion when unfunded, XP per kill including overflow, and all-or-nothing group gold/materials/items. The default exhaustion proposal is half outgoing damage and minus two speed. Normal and deep enemies both cost one point. No energy regeneration occurs between individual attack steps in this fast model; elapsed attack time is accounted for after the group, and subsequent groups receive the resulting energy. This is an approximation for long encounters.

The 16 family factors, four grades, 84 upgrade states, six affinities, six arrow payloads, recipe ratios and unequal species/specimen/deep drop coefficients come from the pinned wiki. Each ordinary action resolves a hit or movement/escape, effects, pursuit and the surviving enemy's attack. Shields leak at least 25% of a landed hit; weapon wear is one endurance unit per attack. Techniques have cooldowns and control resilience. A new DoT ticks on later actions, not application.

## Explicit modeling choices

- Readiness means an empirically successful prepared player against a fixed seeded set of representative **normal groups**, using owned gear/ammo and current condition but restored HP/energy. Probes never award or consume real player resources. The default gate is at least 80% wins over eight probes (seven wins required). This finite probe estimate is not a confidence-certified 80% probability.
- The study assumes floors are available as the player becomes ready; next-floor equipment can be acquired while preparing for that floor. Shared-world unlock waiting is excluded. Days-to-readiness is not the date a live world will open a floor.
- Starter access gives three Common +0 tools, basic defensive gear, 50 gold, and limited ordinary/arcane ammunition. The first group victory grants the documented opening recipe bundle. It is not a recurring reward.
- Defensive equipment follows the existing reference armor/shield curve. Each paid floor step costs two-thirds of that floor's existing honing quote, scaled by `defense_cost_scale`. This is a **derived cost model**, not the actual armor shop catalog. It must be replaced with a live adapter before claiming production parity.
- XP overflow is retained; character training consumes the pinned level XP/gold costs through level 30. Weapon XP honing is absent. School skill-rank purchases, rested XP, race/faction bonuses, quests, PvP, player trade, pack travel, mines and consumable revives are not modeled.
- Recipe upgrades preserve condition fraction. Craft +0 and shop +0/+2/+4/+6 acquisition follow grade/source gates; drops are +0 at 40/30/20/10% condition. Repair is a configurable share of acquisition cost, discounted by the 1.04 pacing wedge. Shield endurance is `max(1300, shield bonus × 80)`; this is an explicit candidate, not a published live shield-pool formula.
- Arrow restocking has a disclosed gold price derived from local ordinary kill income and payload recipe-unit weight. It does not model arrow-material crafting. Drops which improve a deck are kept; redundant drops are salvaged at a small, disclosed price. No trading market is invented.
- The player can bank and withdraw between hunts. Interest is configurable, default 5% per simulated day. Carried-gold loss and condition loss happen on death; banked gold/materials and weapon levels survive. Outside combat, scheduled sleep/dawn recovery and healing purchases are modeled; no mid-group healing or leveling occurs.
- Groups draw unequally from the actual local roster, with count ranges from the research. Ground/carrier trails reweight that roster; they do not modify monster stats to match the deck. Deep specimen/stats/reward premiums are retained as input candidates, despite the changed energy rule. That may reveal a large deep-hunt advantage.
- Only existing trait tags are used, with Wrongmade treated as bloodless. The wiki's 425 new species-specific poison/control immunities are not fully authored; the program must not invent them from animal names.

## Boss model

All warden trials use a single continuously healing HP pool and timestamped individual strikes; no pledges, pooled-stat victory or timezone waiting. The default HP/attack/defense are the pinned base warden formulas on every floor, preserving their exponential growth; `legacy_shared` optionally uses the old enlarged pool instead. Neither option is the current milestone pledge resolver.

The proposed healing law begins at floor 10: `reference player expected direct damage / cadence × 1.05 × 1.035^(floor − 10)`, with both coefficients configurable and saved. It is fixed to reference gear, not resized to the actual party. Below that floor, healing is zero. Each player pays three energy per strike by default (the inspected live strike charge); players have finite HP and starting energy, and receive a retaliation after an accepted attack. Their cadence has small seeded jitter. No refills occur during a trial. Party search reports the smallest tested prefix roster that meets the selected success rate, with a maximum-party bound; it is not a proof over every possible combination.

Reference party demand uses explicit floor-reference gear and is labeled separately from the actual swarm. Observed-cohort demand uses recorded newly-ready players. If more comparable players than the swarm contains are needed, samples repeat as a labeled extrapolation; available actual players remain a separate number. Empty cohorts have no observed estimate. Future statuses on shared wardens (shared stun/Expose/DoT) are excluded from the first boss model; it measures direct attacks and protection. This may overstate specialist party demand, and is shown in the UI.

## Honest graphs

Report mean/median/P90 **among players who reached a floor**, alongside the fraction who reached it and the count still censored at the run horizon. Full-population median/P90 use nearest rank (the empirical CDF inverse) and are null until that fraction reaches the corresponding quantile. The reached-only table uses interpolated quantiles; small cohorts can therefore have different medians even at full coverage. Restricted mean time uses the run horizon for censored players and is explicitly a lower-bound horizon statistic, not a forecast of eventual completion. No late-floor line is extrapolated through missing results.

Readiness is checked at session boundaries when the gear/ammunition state changes; condition is bucketed in tenths and ammunition in sets of six to avoid repeating equivalent expensive probes. This can delay detection by a session or small condition changes. No milestone is awarded from a training win alone.

All-zero-energy runs still count. Report XP, rewards and readiness per active minute and calendar day as well as per energy. Separate overall hunt outcomes from the independent readiness probes. Statistical difficulty and resource pressure can be tested quickly; the model does not establish whether real players find the game fun or the interface understandable.

## CPU execution

Runs automatically use available CPU cores (including Linux CPU affinity) with portable spawned worker processes. Players and warden floors are independent work units; results are restored to ID/floor order before aggregation. Random streams depend on seed and logical IDs, never process order or worker count. `--workers 1` forces serial execution and a positive count overrides automatic selection. The semantic digest excludes worker count; execution metadata records it. Tiny runs can be faster serially because processes have startup costs. Scaling is bounded by the number of independent tasks, available memory and serial aggregation; more CPUs do not imply linear speedup.
