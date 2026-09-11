# Research validation and implementation limits

This validates a design study produced on 11 September 2026. It does not certify a deployed weapon system or a completed gameplay plan. The research adds documents only; no engine, runtime state, vendor copy, or deployment was changed.

## Evidence examined

- Local economy and catalog, player persistence, inventory, Forge, combat, rendering, shared-world transactions, pledge schema, and relevant test source.
- Generated mechanics data: reference attack values for all 100 playable floors were compared with the current imported economy. The extra calibration bar 101 was not treated as a playable floor.
- Root source snapshot `c52fa21d546171e9e950a1c2c9155ebef6231dcb`; plugin source snapshot `2f9cfff5557cde824091e8e2ce9107171ba80024`. Existing uncommitted and staged work was present and was not included in a task commit.
- Kingdom Rush Battles community wiki, official beginner guide, developer Q&A, Summon Rift guide, and historical official patch notes. A wiki/official level-cap discrepancy is explicitly recorded instead of copying an unsupported cap.

## Arithmetic results

| Check | Result | What this proves |
|---|---|---|
| Four grades × 21 states | PASS: 84 acquisition/level states; 80 actual upgrades | Each grade spans +0 through +20. |
| Increasing gold charges | PASS: every upgrade after +1 costs more than its preceding upgrade | Acquisition is separate; the 200-gold Common +0 exception need not cost less than +1. |
| Increasing material requirements | PASS: all 80 steps increase Q | Every recipe uses more of both materials on the next level. |
| Increasing maximum durability | PASS: all 80 steps increase | No upgrade reduces the proposed neutral maximum condition. |
| Integral positive costs | PASS across all 84 states | Proposed costs and quantities do not rely on fractional inventory. |
| Attack mapping | PASS: 100/100 floor values equal the current neutral reference | A small catalog can represent the existing attack curve. Actual affordability is a different question. |
| Mechanics-page comparison | PASS: 100/100 stored reference ATK rows match the imported economy | The starting reference is consistent with the checked-in mechanics table. |
| Probability bounds | PASS on all 100 floors and all four grade columns | Baseline probabilities stay in [0,1]. They are independent rolls. |
| Legendary gate | PASS: zero probability on floors 1–49 | No accidental linear-interpolation leak below the intended gate. |
| Early Epic possibility | PASS: positive on every floor | Discovery is possible at low floors, including a baseline 0.001% at floor 1. |
| Material wait on a recipe-matched carrier | PASS: material P90 is below modeled gold wait in 83/83 non-tutorial states | Under the stated fixed-carrier assumptions, materials do not add another mandatory long wait. |
| Tutorial exception | IDENTIFIED: Common +0 random P90 is 114 eligible kills, or 3.80 modeled days | A one-time starting-path material bundle is proposed to avoid the opening dry streak. |
| Deliberately unfavorable carrier | Modeled separately; requires up to three times as many successful bundles for a blade/bow bottleneck | Route choice changes expected progress. The design does not flatten all sources. |
| Floor-35 worked example | PASS: Rare probability 39.285714%; bundle unit Y=2 | The route example uses the same probability and quantity rules as the table. |
| Two unchanged-attack upgrades | EXPLICIT: Epic +17/+18 at floors 72/73 | These currently add durability only; card copy must not imply an attack increase. |
| Source/vendor economy | PASS: byte-identical at inspection | The economy source used here was also present in the checked-in worldd vendor copy. |

The calculations used decimal constants for proposed integer charges and the engine's original functions for current-reference values. Material P90 was evaluated using the binomial distribution and integer search, not inferred from average yield. The formulas, gate omissions, interpolation knots, and rounding convention are recorded in [PROGRESSION-TABLES.md](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/weapon-upgrades/PROGRESSION-TABLES.md).

## Pacing conclusion and its limits

The explicit current reference weapon route costs **285.36 design-income days**. The proposed neutral route costs **285.88**, a **+0.18%** difference. Within grades the differences range from +0.06% to +0.70%. This is useful as an initial capital-effort anchor while permitting better strategies to progress faster.

However, the candidate spends **39.40% more nominal gold** over the complete route. Payments have moved to different floors with different incomes; equal effort is not equal currency destruction. This difference can change bank balances, compound interest, and the value of skipping upgrades. Whole-account economic simulation must assess it before freezing prices. The two figures must not be presented as interchangeable proof of economic parity.

At a 60% allocation of design income, the one-weapon gold effort index becomes about 476.5 days. That is not a forecast of season length: interest, existing balances, rewards, skipped purchases, death, the time spent at each floor, other equipment, character leveling, and players' choices are not modeled as a continuous account trajectory. The source's `daily_income` is itself an estimate, not live telemetry.

The recipe-matched probability model assumes every successful kill is the relevant carrier at that floor. A proposed 70/30 hunting trail, a random ordinary hunt, and a two-energy deep hunt are not that model. They need simulations that sample actual species and specimens, apply combat win/loss and costs, accumulate A and B separately, spend gold, and select upgrades over time. The unfavorable-carrier comparison demonstrates an opportunity for strategy, not a measured optimal policy for the entire bestiary.

## Items that require further work before implementation can be called balanced

1. **Whole-account pacing:** compare reasonable and optimized old/new routes, including three weapon paths, training, armor, repairs, bank interest, death, existing savings, and the removed weapon-honing XP sink. Track median and P90 time, not just means.
2. **Real route advantage:** make the proposed hunting trails and creature affinities concrete on all relevant floors. Demonstrate faster informed play without a universally dominant one-click route. Model ordinary and deep hunts per energy and per surviving trip.
3. **Legacy conversion:** quantify migration outcomes for every current weapon, hone, style, wear state, oil state, and storage location; retain retired instances when a forced mapping would lose paid value.
4. **Combat:** preserve the neutral reference while measuring upper-end specialization after defense, training, range, mastery, consumables, and wear. A matched reference attack table alone is not a win-rate simulation.
5. **Warden reality:** reproduce the existing per-swing energy versus full-exchange pool-calibration mismatch. The desired direct, continuously healing boss model requires its own real-time group simulation and implementation phase.
6. **Milestones:** current floors 10…100 are automatic pledge resolutions. The requested replacement must apply actual simultaneous damage, refund old unconsumed pledges, and connect a real floor-100 death to era closure exactly once.
7. **Death and storage:** the proposed persistent upgrades and safe Materials compartment alter current loss sinks. Price and test those changes explicitly; do not accidentally inherit whole-stack material loss.
8. **Browser behavior:** verify all four frame shapes/colors, material counts, keyboard focus, tap previews, Forge navigation, stale quotes, full packs, two tabs, two players, and migration messaging through real Luna/browser play.

No coded application test suite or dojo was run because application behavior was not implemented. Existing tests were read to establish what they actually cover. Dojo remains mandatory before any future implementation plan is reported complete. Research completion does not mean those release checks have passed.

## Document rollback

This task's artifact rollback is removal of the four new files under `research/weapon-upgrades/` (RESEARCH.md, PROGRESSION-TABLES.md, BOSS-SYSTEMS.md, and VALIDATION.md) and the two new files under `plans/013-mining-and-gathering/` (PLAN.md and DOJO-SCENARIOS.md), then removal of those directories if empty. Preserve all unrelated files and staged work. No runtime rollback is necessary.
