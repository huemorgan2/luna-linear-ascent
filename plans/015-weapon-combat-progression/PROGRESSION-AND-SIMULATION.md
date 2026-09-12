# Progression, strategic advantage and proof

Companion to [plan 015](PLAN.md). This replaces its old single-monster success targets, main-plus-counter budget and hypothetical `tools/progression/run.py` harness. Reuse the working `simulation/` implementation and the actual game library.

## What the completed runs establish

The improved legal planner has meaningful advantages under the old imported engine. Across eight validation trajectories, median days to floor 5 is 4.668; six reach floor 8 and none reach floor 9 within 30 days. The matched Mage cohorts progress less. The 24-player mixed-strategy run deliberately includes weaker bots; its median is not a demographic prediction of human players who learn. [Full evidence and reproducible commands](../../research/simulation-strategy-search/RESULTS.md).

These runs use individual encounters and old equipment rules in game 0.111.0. They do not tell us the outcome of new three-weapon groups. They also exclude actual shared-world victory/waiting and social ambushes. First integrate the newer published baseline, then repeat a small comparison at that exact source revision. A changed source hash invalidates replay of the older run; keep its code and results identifiable rather than relabeling it.

A flat/missing curve has several possible causes: nobody reached the next readiness threshold within the run, the policy mishandled a legal action, recovery consumed all income, a gate was unavailable, or the probe definition failed to capture capability. The report must identify these cases with actual traces. Do not infer a game hard wall solely from one bot cohort.

## The intended shape

The player should improve several floors in the first day. Later improvement should take progressively longer, with a gentle increase in the **time for the next floor**, not an early jump from hours to weeks. This is a pacing requirement, not a request for linear monster power.

Keep the existing neutral references visible: power/capital factor 1.3, income factor 1.25, their ratio 1.04, warden extra factor 1.02, character cap 30 and ten equipment/energy bands. Growing prices alone need not produce a steep time curve if productive income grows too. The game must measure **net** income after healing, ammo, repairs and failed groups. A 1.04 sticker-price ratio is not proof that the account advances 4% more slowly.

### A concrete target for review, not a result

For the current reference schedule of 30 active minutes/day across three visits, a useful initial target envelope could start with 0.15 calendar day for the first floor improvement and grow that marginal delay by 4% per floor:

`target extra days to floor f = 0.15 × 1.04^(f−2), for f ≥ 2`

`target total days to floor f = 0.15 × (1.04^(f−1)−1) / 0.04`

| Monster floor | Target extra days from the previous floor | Target total days from creation |
|---|---:|---:|
| 2 | 0.150 | 0.150 |
| 3 | 0.156 | 0.306 |
| 5 | 0.169 | 0.637 |
| 10 | 0.205 | 1.587 |
| 25 | 0.370 | 5.862 |
| 50 | 0.986 | 21.875 |
| 75 | 2.627 | 64.562 |
| 100 | 7.004 | 178.359 |

**These are illustrative hunting-capability targets awaiting review.** They are not measured, not a committed six-month season, and not time to actually unlock/defeat floor 100. Party availability adds separate world time. Attendance, session spacing, first-session instant gains and energy timing can create real steps/plateaus around this smooth guide. Do not draw fabricated intermediate observations to match it. Changing the starting delay or growth rate is a design decision before tuning, not a secret adjustment to a graph.

Record a review threshold for sudden changes in marginal delay: for example, investigate a greater-than-2× jump at adjacent ordinary floor steps when supported by enough arrivals. Early near-zero samples, session boundaries and intended grade/teaching steps require interpretation. This flags a bottleneck; it is not a universal law forcing every floor/deck to have equal progress.

## Tune the account, not individual weapons to equality

The target is a viable, understandable progression path and several profitable specialist routes. A player should learn which monsters, trails and upgrades suit the available collection. They need coverage across the world, not mandatory ownership of all 64 variants or an imposed sword/staff/bow recipe for every hunt.

| System to measure | What can break progression | Useful response |
|---|---|---|
| Three useful weapons | Pricing three equally upgraded items can triple the former opening burden | One main investment plus affordable counters; authored starter access; test asymmetric spending. |
| Full-group completion | Retained wounds and an unsuitable finisher erase most hauls | Preview readable threats, provide obtainable counters and affordable recovery; tune the whole group's threat rather than every enemy to an equal win rate. |
| Repairs/healing/ammo | Gross gold rises while net income stays zero | Trace actual costs and secured income; fix the demonstrated sink or route. Avoid free refills in tests. |
| Two-material recipes | A plentiful material hides starvation of its partner | Show bottleneck counts, carrier-specific routes and time to each material separately. |
| Grade transition | New materials require the weapon they are meant to craft | Prove a previous-grade deck can collect both materials; craft at native gates before later shop stock. |
| XP | Removal of slot/honing costs and overflow retention accelerate levels | Simulate normal training, reserve spending, cap 30 and gold costs together. Do not discard kill XP to hide excess supply. |
| Exhaustion | Easy enemies at zero energy become the best route or halved damage rounds away | Measure earned XP/net haul per active minute and elapsed hour, not only per energy. Preserve smart easy-XP routes if their time/opportunity costs are intentional. |
| Deep routes | Better displayed odds cannot compensate for losing almost every haul | Prepared specialists should show a net benefit; other decks may fare badly. Recalibrate each rarity separately after the old two-energy fee is removed. |
| Choice diversity | One deck wins every comparison cheaply and safely | Inspect universal interactions and redundant family roles. Strong local winners and large strategic advantages are desirable. |

Deliberate partial-group XP farming is a legal choice: the player spends energy only on begun enemies, keeps actual kill XP and abandons gold/items. Repeating a receipt or rerolling an unstarted offer is a bug. Do not treat an efficient legal route as a bug merely because it beats a generalist.

No automatic P90/median drop-time cap and no compulsory 25–50% smart-player advantage. Show measured tails, reach counts and uncertainty. Keep early Epic/Legendary discoveries exceptional. If a mandatory native resource creates an unreasonable dead end, first fix route/craft/opening access; adopt and publish a dry-streak rule only after a separate decision.

## Headless implementation

1. Keep personal actions through `core.apply_choice` / `core.current_scene` and actual state/economy/content. New groups, sources, Forge, XP reserve and exhaustion enter the game engine once; the adapter does not emulate them.
2. Extend bots to build three-instance decks before entry, inspect offered groups, choose a weapon/technique/arrow, use movement/control/heals, decide whether to continue exhausted, compare upgrades/repairs and choose species/material routes. They may inspect only information a real player can obtain; never future RNG, hidden loot or disposable probe results for free resources.
3. Preserve complete action reasons, effective deck, energy receipts, kill/haul settlement, costs and refusals. Disqualify looping/invalid policies from search rankings but retain their diagnostic artifacts. Poor but legal decisions remain a comparison cohort.
4. Change readiness from a single enemy probe to **full group clear** under a recorded route/group distribution. Use owned condition/training/deck and disposable restored HP/energy for capability tests; never return probe rewards or repairs. Lock each probe deck within its group. Report sample size and uncertainty; seven wins out of eight is not proof of an 80% underlying win rate.
5. Add sustained hunting tests using actual current HP, energy, wear, earned supplies and paid recovery. Distinguish “can clear this floor when prepared” from “can farm it profitably for repeated visits.” Check readiness after real improvements and at session boundaries without artificially delaying already-qualified floors.
6. For wardens, add an isolated-world adapter through the same `worldd` shared action/effect services and transaction/storage contract, including actual frontier unlocks and era closure. Inject virtual server time through a tested clock seam. A copied DPS formula or sum of player attack stats is not a replacement. Keep PostgreSQL-backed parity/concurrency checks against the service used in production.
7. Parallelize independent player experiments or whole isolated worlds across available CPUs. Within one world, preserve timestamp ordering and real transactional competition; do not split its shared HP into independent player copies. Keep deterministic IDs/seeds, bounded memory, checkpointed jobs and hashes of plugin, vendor, service, policy and inputs. Run serial/parallel parity after changes.

Existing `simulation/run.py`, `game_search.py`, `game_study.py`, `serve.py` and saved-run display remain the entry points. Add settings only after the real rules support them. The historical `/proposal` resolver remains visibly historical and is never used to claim the new production model has been tested.

## Experiments and graphs

Start with a small calibration, then matched policy comparisons on multiple seeds. Freeze the selected strategy before testing fresh seeds. Increase cohort/horizon until the intended range is measured; an unfinished floor remains censored, not zero days and not an extrapolated line. Around 10,000 seeded trajectories per representative cohort is a scale target after the fast screening pass; choose actual sample sizes from uncertainty and runtime. Tiny Legendary odds need exact distribution checks and targeted tests, not a claim that a large-looking run count is sufficient.

Keep attendance and action times equal when isolating strategic skill. Separately compare light/regular/heavy schedules and empirical human timings from web/Luna. A fastest player among more sampled players has a statistical advantage; record population size, seed and attendance when comparing that line. The fastest player can change identity at each floor, so the envelope is not one player's single continuous path.

| Graph / report | Exact meaning |
|---|---|
| Days until players can defeat each floor's groups | Cumulative days since creation. Median of the entire defined cohort and fastest observed successful player, with reach count and identity/strategy in the tooltip. Missing median until enough players arrive. |
| Extra days needed for the next floor | For each player, `arrival(f) − arrival(f−1)`, then summarize those per-player intervals. Do not subtract two population medians or adjacent fastest-envelope points. Report who reached both floors and censored intervals; reached-only summaries must say so. |
| Actual floors reached in the shared world | Includes warden/frontier unlock waiting. Keep distinct from capability probes that grant test-floor access. |
| Players who can clear this floor | Eligible hunter count/percentage and roster at the relevant world time, with a stated capability criterion. |
| Players needed to defeat this warden | Smallest tested concurrent group that meets the agreed repeated-trial victory criterion using the actual service, not a guaranteed mathematical minimum. Overlay capable/eligible/available players; keep each count distinct. |
| Strategy and route comparisons | Same seeds/schedule, multiple specialist/generalist decks: time, victory, deaths, secured gold/materials, ammo/repair cost and energy. Show repeatability on fresh seeds. |
| Why progress slowed | Time spent hunting, recovering, waiting for energy, collecting each material, saving gold, learning, and waiting for world unlock. Include refused/looped action diagnosis separately. |
| Warden trace | Shared HP versus time, accepted hits, actual healing, status ticks, energy remaining and victory/failure, with overlap versus staggered attacks. |

Tooltips must say, for example, **“Floor 5 — half the players could defeat its groups after 0.8 days; fastest observed: 0.3 days, Player 12 / bow specialist; 83 of 100 reached.”** Those values are wording examples only. Never use “Selected run: 28” for a duration. Use a separate dashed **Design target** only if comparing against the reviewed target, clearly distinct from measured results.

## Warden demand

Use fixed reference profiles to tune increasing group demand, while allowing better preparation to reduce the actual required count. Proposed experience bands: solo learning on 1–9; small cooperating groups around 10; increasing demand toward dozens at 100. Earlier research's approximate 2–5 / 5–12 / 12–25 / 25–50 bands are test hypotheses, not hard quorums or a requirement to resize HP as players join.

A rough explanation is `sum(actual DPS) > healing`, with enough margin to finish before energy/HP runs out. Verification must use discrete accepted hits, misses, approach, control, healing, real action cadence and exhaustion/energy rules as applicable. Neither mean DPS nor a count of pledged players establishes a win. Check high-power legacy/legal builds against early and late wardens separately; overprepared early wins may be acceptable, while a legal solo floor-100 kill conflicts with the intended cooperative finale.

Simulation must show both the capable population and the party needed from it. If only 20 players qualify and the tested boss requires 35, the run reports insufficient capable players, not a fictitious victory. Availability/coordination assumptions are explicit inputs; no asynchronous pledge mechanism is added to solve time zones.

## Phase and release gates

- First session: clear the opening pair, obtain necessary counters and perform the first upgrade through ordinary authored resources; several early floor improvements below one day under the reviewed schedule.
- Whole-group survival: test the beginner route and designated prepared ordinary routes. Initial candidate goals are at least 90% and 80% completion respectively, with uncertainty reported. These do not apply to every deck or deep group.
- No resource dead end: each mandatory counter and both native crafting materials have a legal accessible route, including zero-gold/broken-weapon recovery and grade boundaries.
- Genuine specialization: every family has a reproducible useful situation. Compare general and specialist decks across contrasting routes; no forced equality and no required fixed gap between median and fastest.
- Gradual pacing: publish cumulative and per-player next-floor times with confidence/reach counts. Investigate cliffs with actual state and ledgers. Retune the real costs/supply/threats, then rerun identical and fresh seeds.
- Energy/reward integrity: five enemies/two energy; escape after two; zero-energy kills; failed escape; revive; dawn; reconnect; duplicate and simultaneous final requests all satisfy the exact contracts.
- Cooperative endgame: at-floor solo failure and feasible real concurrent wins from finite resources, including floor 100 and exactly-once rewards/era closure.
- Human playability: real browser/Luna testers can explain their deck choice, incoming threat, exhaustion and lost/earned rewards, and finish a group without repeated unnecessary screens. Record actions and active minutes, not only simulation outcomes.

The plan is ready for review when these goals and the screen flow are clear. The game is ready for release only after the measured gates pass. No amount of documentation or prettier graphs substitutes for either the actual-engine runs or human-readable playthroughs.
