# 015 — Three-weapon collections, group battles and progression

12 September 2026 · Revision 2 · Branch: `change_everything`

**Ready for design review. Implementation has not started.** This replaces the original eight-phase implementation draft and its group addendum. The user asked to review the complete change before execution. No new combat rules, migrations, deployment or balance tuning are authorized by this planning task.

## The change to review

A player builds a **weapon collection** and chooses **three weapons for the next hunt**. A hunt is one continuous scene against a group. The player's preparation, attack choice, movement and use of effects determine whether they can finish the group and bring its haul home. Weapons are intentionally better and worse against different monsters; knowing the route should pay.

The first version is proposed as **sequential enemies**, with the next enemy visible in the same scene. It removes repeated town → hunt → loot screens without multiplying the number of enemies attacking after every click. Simultaneous two-enemy waves are a later prototype, not a prerequisite for this release. Shared wardens remain real concurrent multiplayer battles.

| Area | What will change |
|---|---|
| Opening and first session | Teach the collection and three battle slots; an easy two-enemy hunt; XP versus pending haul; obtainable bow/magic access before required counters; first Forge upgrade. |
| Profile and equipment | Three always-available weapon cells, separate defensive gear, readable current condition and abilities. Open the collection from the profile or battle preparation. Remove School slot purchases and associated locks. |
| Weapon collection | Browse everything owned; choose specific instances for three slots; compare role, reach, grade, level, durability and arrows. Selection stays fixed through the hunt. |
| Encounter opening | Show the actual ordered group, images, affinities, flight, traits, arrival distance, possible drops and energy coverage before the first attack. |
| Battle scene | One active enemy, group progress and next portrait; three weapon actions; visible gap, intent, effects and cooldowns. Preserve wounds, ammunition and wear between members. |
| Rewards and recovery | One energy when each enemy begins; meaningful exhaustion at zero; XP immediately per kill; gold/materials/items pending until the full group is defeated. Retreat/death keeps earned XP and forfeits the pending haul. |
| World content and economy | Retain 16 families / 64 grade variants and 425 creatures; +0–20 upgrades, eight materials, source-specific condition and levels, unequal routes and drops, and Forge-only upgrading. |
| Wardens and endgame | All floors, including 100, use actual accepted attacks against shared HP that heals with time. Replace pledge and combined-power victory. |
| Simulation and wiki | Execute the same game rules in headless runs; graph median and fastest observed progress, days per next floor, sustained hunting costs and measured concurrent player needs. Wiki and game use the same definitions. |

Read [Player experience](PLAYER-EXPERIENCE.md) for the screens and example hunt, [Rules and migration](RULES-AND-MIGRATION.md) for combat/data contracts, and [Progression and simulation](PROGRESSION-AND-SIMULATION.md) for the curve, evidence and release gates.

## Decisions already given by the user

- Three available weapon slots from the beginning. No School purchase of a fourth slot or of access to the existing three. A player can choose any combination, including specialists.
- Monster groups have at least two members. Group size and composition develop over the tower. Weapon choice must matter across the group.
- Normal and deep hunts cost **one energy per enemy when its fight begins**. No whole-group prepayment. With two energy against five enemies, the first two are normal and the later three significantly weaker, assuming no regeneration. Leaving avoids charges for unstarted enemies.
- XP is earned per kill. Gold requires defeating the whole group. This plan recommends putting material/item drops in that same final haul.
- Common / Power / Magic is separate from Ground / Air. Give monsters readable counters and traits, and retain the large, visually varied roster.
- Distinct weapon families, four grades with different art and pixel frames, weapon levels 0–20, growing gold/material costs, source-specific starting levels/condition, and upgrades performed only in the Forge.
- Clever deck building and farming should create substantial advantages. Do not equalize every weapon, route, drop probability or chance of winning.
- Fast early improvement, followed by a gradual slowdown. The measured curve must emerge from legal play, not a graph drawn to a desired shape.
- Wardens heal against actual concurrent damage; no stored pledges or timezone compensation. Mining remains separate in [plan 013](../013-mining-and-gathering/PLAN.md).

## Concrete recommendations awaiting this review

These are design choices, not assertions that the user already selected their exact details.

| Recommendation | Reason / consequence |
|---|---|
| Sequential groups first; normally 2–6 members, with short routes retained at high floors | Gives coverage and endurance choices without an unreadable multi-target launch. Larger challenges can be authored later. |
| Collection means all owned weapons; “Bring to battle” contains three slots | Avoids confusing ownership with the three-weapon limit. “Deck” is shorthand, not random card drawing. Empty slots and duplicate families are legal. |
| Starter blade, bow and staff access during the opening, through fixed starter grants/quests with no rare-drop requirement | Three available slots are useful immediately; the first hunt can teach only one weapon. The player does not need to upgrade all three equally. |
| Attack with any selected weapon as the normal action, without an extra switch action | Makes reacting to the next enemy quick. No extra attack is awarded; no fourth weapon can be pulled from the pack mid-group. |
| Exhaustion starts at 50% outgoing damage and −2 effective speed, minimum 1 | A measurable first tuning candidate. XP for a real kill is unchanged. Exhaustion is not a hard XP cap. |
| Preserve overflowing XP in a visible reserve; no automatic mid-hunt level-up or heal | Later kills still count at a full XP bar; normal advancement costs remain. |
| Gold, materials and items settle together after full victory; earned weapon levels and previously secured materials survive ordinary death | Protects long-term collection investment while making each hunt's haul genuinely at risk. Repair loss and the existing purse/death rules remain explicit costs. |
| Air Power keeps the proposed visible “Spell dispersal” exception | Preserves the user's particularly weak magic-versus-Power-air direction despite the general ground Power weakness to Magic. Explain this exception, never hide it behind a shield icon alone. |
| Native-grade guaranteed supply only where needed to prevent a mandatory acquisition dead end | Fixed opening rewards and craftable access first. Any later dry-streak protection needs separate evidence; do not automatically make rare discoveries predictable. |

Existing matrix, effect, recipe, source-gate and group-size numbers are starting candidates. Their inclusion is not proof they work together. The optional target curve in the progression document is for review, not a promised season duration.

## Problem, evidence and timeline

11–12 September: weapon/material research and the public wiki established the four-grade catalog, tactical families, creature art, drop settings and upgrade reference. The subsequent fixed-deck, group and per-enemy energy requests changed the state model and the reward boundary. Plan 015 only appended those requests; its phase instructions still referred to individual hunts, a main-plus-counter budget and a new standalone balance harness.

12 September: plans 018–020 instead built and verified `simulation/` using the actual imported engine. Better legal decisions greatly improve the result: on two independent validation seeds, the selected planner's median final monster floor in 30 days was 7.5 and 8, against the corrected Mage's 4.5 and 4. The pooled planner reaches floor 5 at a median 4.668 days; nobody in those eight trajectories qualifies for floor 9 within 30 days. This is evidence of remaining pacing work and limited policies, not proof that floor 9 is impossible. See [measured results](../../research/simulation-strategy-search/RESULTS.md).

Those runs use local game **0.111.0**, individual hunts and School slots. They do not measure the proposed groups. Published wiki source on `origin/main` at `1897edd` includes **0.112.0** and wiki revision `089.3`. This branch starts at completed simulator commit `65f3c1c`; integrating the newer published baseline and repeating a source-pinned comparison is phase 1, before any gameplay edits. Do not pretend old run hashes describe a newer checkout or production.

Source inspection confirms slug-based held selection, XP clipping in `engine/state.py:gain_xp`, per-enemy victory returning to town in `engine/combat.py:_victory`, and separate warden strike/pledge paths in `worldd/app/social.py`. The existing profile exposes equipment through `engine/profile.py` and the same scene renderer serves web and Luna. Changing only the battle HTML would leave the authoritative rules and other clients inconsistent.

## Root cause

The previous plan treated weapons, screens and economy as separate changes. Groups make them one system: three committed item instances must survive several enemy lifecycles; energy starts per member; XP commits per kill; the haul commits per group; clients must show those exact boundaries. The old plan also over-relied on neutral attack-table parity as a pacing guarantee. Survival, repair, healing, three useful weapons, training and failed hauls determine actual days of progress.

## Emergency mitigation already taken

No production intervention. Completed simulator/research changes and their plugin dependency are committed and pushed. Historical runs, the old proposal simulator and published wiki stay identifiable. This revision prevents execution of the obsolete phase instructions; it makes no player-state changes.

## Execution order after review

| Phase | Deliverable and gate |
|---|---|
| [1 — Baseline and final contracts](phase-1/PLAN.md) | Integrate published work, pin source, reproduce current play, freeze the reviewed UX/rule choices and initial pacing target. Reuse `simulation/`; do not build a second combat model. |
| [2 — Item instances, three slots and safe state](phase-2/PLAN.md) | One shared schema for collection, committed deck, group, receipts and migration; both backends and old clients handle it safely. QA only. |
| [3 — Complete opening and first-ten-floor loop](phase-3/PLAN.md) | Profile → collection → group preview → sequential fight → XP/haul → Forge/recovery, using real production paths, with per-enemy energy and readable exhaustion. First player-review milestone. |
| [4 — All weapon identities and monster groups](phase-4/PLAN.md) | All 64 variants, 425 creature mappings, unequal routes, effects/arrows, acquisition settings and wiki. Prove useful niches rather than equal power. |
| [5 — Personal progression and economy](phase-5/PLAN.md) | Real-engine, multi-CPU strategy trials tune the complete account economy; publish median/fastest days and next-floor delays, including failures. |
| [6 — Concurrent healing wardens](phase-6/PLAN.md) | One timed shared battle service, real hit settlement, finite energy, measured party sizes, and exactly-once floor-100 era closure. Recheck phase-5 progression under actual world gating. |
| [7 — Full playthrough and migration rehearsal](phase-7/PLAN.md) | New/returning players, web/Luna/mobile, multiple users, recovery, stale cards, data conversion and rollback all verified. |
| [8 — Explicit release and observation](phase-8/PLAN.md) | QA canary, pinned plugin/vendor/site release, production verification and measured rollout. Deployment is a later explicit action. |

Execute phases in order. Later infrastructure can be designed early, but it cannot be reported validated before its dependencies pass. Phases 2–7 stay in an isolated QA world until the coherent release gate. Do not expose different battle rules to participants in the same shared warden.

## Verification

Each phase supplies concrete checks and a browser scenario in [DOJO-SCENARIOS.md](DOJO-SCENARIOS.md). Mathematical rules get coded tests; subjective readability and fun require actual multi-turn play. Before reporting any implementation phase complete, run its targeted checks, required full suites and the real web/Luna walkthrough. Record SHAs, settings, results, screenshots and failures in a numbered results folder.

Hard gates include zero duplicate energy/XP/loot/refund/kill receipts; no required counter locked behind the monster it must defeat; no lost earned progress during conversion; no fourth weapon through another client; real shield chip damage; measured group completion and sustainable costs; and real concurrent warden victory. The progression document defines how to compare strategies without inventing a fastest-possible claim or equalizing choices.

## Operational notes and rollback

The plugin owns engine/content/cards; worldd owns shared transactions, effects and the served vendor; `simulation/` imports those same rules; the wiki is generated from them. Future plugin work uses a corresponding `change_everything` branch in its own repository, commits there first, then updates the root pointer/vendor. The root branch name is the user's explicit choice; this existing plan keeps its stable number and links.

Before phase 1 integration, isolate or preserve unrelated workspace edits; do not include admin/feedback changes, local credentials, unrelated research or book drafts just to make the tree clean. Record exact source revisions and rollback commits before runtime changes. Before each commit run the secret-pattern scan and `git diff --cached --check`.

Documentation rollback before implementation: revert only this revision's documentation commit. Runtime rollback: stop new candidate entries, keep compatibility readers and transaction receipts, drain or explicitly settle active encounters once, then apply tested compensating operations. Never restore an old whole-player/database snapshot over newly earned progress. Phase 7 must record the actual runbook commands and their receipt IDs before production conversion is allowed.

## Planning verification

Checked all 27 plan/scenario documents, 49 local plan links, eight Goal/Steps/Verification/Rollback phase contracts, and fourteen five-part browser scenarios. Recalculated all eight rows of the illustrative target curve from its stated formula. Whitespace and secret-pattern checks run before this documentation commit. The historical simulator verification remains in `simulation/verification/005/summary.md`; it is not verification of these unimplemented rules.

## Execution status

**Planning revision complete; awaiting user review. Phases 1–8 not started.** The earlier research and simulator remain completed work, not evidence that this game redesign has shipped. No new gameplay, migration, balancing run, dojo playthrough or deployment was performed for this planning revision.
