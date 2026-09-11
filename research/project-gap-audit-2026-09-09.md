# Linear Ascent — what we planned versus what exists

Audit date: 2026-09-09, updated 2026-09-11 for plan 085. Release candidate game version: `0.111.0`.

**The game has content definitions for all 100 floors, but the finished experience stops at different floors for different systems.** Standard maps cover floors 1–10; turn-based 3D combat covers floors 1–20; the new monster-kind story data and floor NPCs cover floors 1–10. The map expedition system has not been built.

This is an audit of the local repository, its plans, assets, implementation, and recorded verification. Plan 085 subsequently implemented and browser-tested the floors 1–10 map scope; its production status is tracked in that plan. Existing unrelated admin/feedback work and onboarding research are not assumed deployed.

“Exists” below means an implementation or asset was found. “Missing” means the planned implementation/content is absent in this checkout. “Deferred” and “proposed” distinguish deliberate future work from unfinished delivery. Historical completion claims were checked against current files where possible.

## 1. The main comparison

| Area | What we wanted | What exists now | What remains / status |
|---|---|---|---|
| **Floor maps** | Each floor's camp becomes a map with usable location markers. | Ten distinct 492×369 map assets and layouts cover floors 1–10 as the standard experience. Labels, instant explanations, keyboard numbers, and residual action rows passed desktop and phone browser review. | **90 floors unmapped.** Floors 11–100 retain their working menu fallback. Reconcile later-floor lore before the next bulk art rollout. [Plan][map-vision] · [layout][map-code] · [gate][labs] |
| **Floor-1 expeditions** | Mother Ditch / Sluice Maw; Burnt Steading / Char-Troll; Fairstone Green / Fair-Day Wyrm. Paid paths, bosses, prizes, retreat, saved progress, and an hour-away surprise. | The map routes existing actions such as hunt, camp, gate, and keep. No `engine/quest.py`; no floor YAML has a `places` block. | **All three quests remain unimplemented.** Phase 1 deliberately shipped the map without quests; the subsequent 1b–1h polish phases did not add them. [Floor-1 plan][map-plan] |
| **Quests across the tower** | Three places of interest and easy/medium/hard expeditions per floor. | Lore files contain a “Places of interest” section for 99 floors. These are prose seeds, not executable quests. | Build and validate the first floor's quest system, then author floor-specific bosses, rewards, paths, and assets. The nominal vision is roughly 300 quests; floor 100 needs an explicit treatment because its lore lacks that section. [Vision][map-vision] |
| **3D fights on every floor** | Arena enabled for every player on floors 1–100, including each floor's creatures and wardens. | Enabled by default on **floors 1–20**; all 122 required foe IDs in that range have models and both backdrop types. | **Floors 21–100 remain.** 403 models + 403 finisher backgrounds + 403 arena backdrops; eight rollout phases. The rollout gate still ends at 20. [Rollout][arena-plan] · [code][arena-code] |
| **Lore → playable content** | The 100 distinct stolen countries in the newer lore, with matching keepers, creatures, wardens, and liberation outcomes. | All 100 playable YAML files exist. The mercy engine exists, but only **59 encounters on floors 1–10** have `native` / `pressed` / `wrongmade` data; **366 encounters on floors 11–100** lack it. | **Partial story migration.** Reconcile later-floor rosters and geography with the newer lore, then supply monster kinds and true forms. Do this before bulk-generating art for those rosters. [Story plan][story-plan] · [schema][schema] |
| **Floor NPCs** | A distinct voice/keeper at each floor's camp. | NPC blocks on **10/100 floors**, all floors 1–10. | **90 NPC blocks missing**, plus dialogue integration/verification for those floors. The schema currently requires NPCs only through floor 10. [World plan summary][world-summary] · [schema][schema] |
| **Distinct floor presentation** | Each country feels different through its environment, arrival, and warden reveal. | Floor 1–10 arrival animations exist. Later floors use still banners; many share a tier banner, with a different milestone banner. | Later-floor arrival animation and country-specific scenery remain a content expansion. A shared banner is a working fallback, not a unique map. [World summary][world-summary] · [story plan][story-plan] |
| **3D player portrait** | A breathing climber wearing actual equipped gear. | Implemented. Shared character rig, equipment sockets, and gear models are also used in combat. Profile rendering is still an opt-in `figure3d` Labs feature. | **Built, experimental.** Default-on rollout is a product decision, not a missing renderer. [Labs][labs] · [shared rig plan][rig-plan] |
| **Guided onboarding** | A short first-session guide that points to the next action, teaches a paid fight, and later teaches new features. | Intro, race choice, tooltips, unlock hints, beginner pity, a level-up explainer, and encounter hints exist. No spotlight/tutorial state machine was found. | **Research proposal, not implemented.** Build the guided layer if retained. The onboarding research predates some completed 081 fixes, so its entire “missing” list should not be copied into the backlog. [Research][onboarding] · [completed smoothing][smoothing] |
| **Retire the shardmind bubble** | Remove the retired bubble UI while preserving useful refusal/advice text elsewhere. | `render_scene_fragment` still appends `_shard_html(scene.shard_note)`. | **Cleanup remains**, according to the local onboarding research. Move functional text into refusals/card copy before deleting the channel. This retirement is documented in currently uncommitted research. [Deletion inventory][shard-residue] · [renderer][render] |
| **Sidekick mechanics** | Scout, carry protected loot, develop as a companion, and perform richer offline jobs. | Insight-driven advice and a daily death save exist. Player state includes `sidekick.carried = None`; no functioning carry/scout action was found in current game code. Basic nightly work exists. | **Partial / deferred vision.** The intro still promises scouting and carrying. Either implement those promises or revise the copy; richer companion stats, encounters, and jobs remain design work. [Original ideas][ideas] · [state][state] · [intro/code][core] |
| **Full-tower balance** | A playable, paced 100-floor climb across weapon paths and multiplayer populations. | Formulas and traits extend through floor 100; there are historical simulations. `TUNED_FLOOR_CAP = 10`, and the 11–100 bestiary test module skips by default unless `ASCENT_FULL_SIMS=1`. The later climb simulator models a melee/common-enemy case and simplifies deaths/deep sieges. | **Validation incomplete.** Re-run the current full tower across blade/bow/magic, archetypes, gear, death costs, and group sizes; measure the actual era pace. Existing formulas are not proof that every floor is finished. [Deferred ledger][continue] · [test gate][bestiary-test] · [simulator][sim] |
| **Later-level shop progression** | Carry the more frequent early-game purchase choices into deeper bands. | Band 1 has tenth-step rungs; later bands retain a coarser ladder. Style generation is limited by `STYLE_MAX_RUNG = 2.0`. | **Explicitly deferred.** Design deeper rung names/choices and retune the reference gear alongside them. [Backlog][later] · [economy][economy] |
| **Tactical items / heal progression** | Additional tools such as smoke pots, whetstones, throwing nets, sling stones, and more graduated healing/relic choices. | Existing consumables and relics work; the named additional items were not found. Medgel remains the fixed `heal_25` item. | **Deferred expansion**, requiring combat rules as well as item rows. Do not treat every old item suggestion as an approved launch requirement. [Backlog][later] |
| **Regression tests and browser acceptance** | Clean checks and recorded browser verification before declaring phases complete. | Plan 085 records all-ten-map desktop/phone browser coverage, live Luna conversation, **1440 plugin passes with 9 baseline failures**, and **223/223 worldd passes**. The older shop-arrow plan still says its dedicated dojo walkthrough was not run. | Reconcile the nine pre-existing plugin failures and the older outstanding shop-arrow acceptance separately. [Map result][map-dojo] · [arena test][arena-test] · [shop arrows][shop-arrows] |

### A concrete lore mismatch

The newer [floor-11 lore][lore11] names **The Counting Halls**, **Ledgerstone**, and **Brassbone**. The playable [floor-11 YAML][yaml11] still names **The Rustwater Adit** and **Lampfall**, with its older mining roster. Some later-floor names already match, so this is a partial migration rather than evidence that every later floor must be replaced wholesale.

This matters for both requested expansions: a map drawn from the new lore and a combat model generated from the current YAML can describe different places and creatures on the same floor.

## 2. Exact floor coverage

Counts were recomputed from all 100 floor YAMLs and the current asset directories. A required foe is an encounter ID or `warden_NNN`.

| Floors | Required foe IDs | Models present | Finisher backgrounds present | Arena backgrounds present | Maps | NPC blocks | Encounters with new monster kinds |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1–10 | 69 | 69 | 69 | 69 | 1 | 10 | 59/59 |
| 11–20 | 53 | 53 | 53 | 53 | 0 | 0 | 0/43 |
| 21–30 | 50 | 0 | 0 | 0 | 0 | 0 | 0/40 |
| 31–40 | 51 | 0 | 0 | 0 | 0 | 0 | 0/41 |
| 41–50 | 50 | 0 | 0 | 0 | 0 | 0 | 0/40 |
| 51–60 | 50 | 0 | 0 | 0 | 0 | 0 | 0/40 |
| 61–70 | 50 | 0 | 0 | 0 | 0 | 0 | 0/40 |
| 71–80 | 50 | 0 | 0 | 0 | 0 | 0 | 0/40 |
| 81–90 | 52 | 0 | 0 | 0 | 0 | 0 | 0/42 |
| 91–100 | 50 | 0 | 0 | 0 | 0 | 0 | 0/40 |
| **Total** | **525** | **122** | **122** | **122** | **1** | **10** | **59/425** |

There are 123 finisher-background files on disk; one is an extra legacy `warden.png`. Coverage of the 525 required IDs is 122. The 403 missing IDs consist of **323 ordinary encounters and 80 wardens**, requiring **1,209 additional asset files** if the current roster and three-file-per-foe design are retained.

All **425 encounter IDs and 100 warden IDs have portrait PNGs** in the current content tree. This checks presence, not silhouette accuracy, animation quality, or agreement with the newer lore.

## 3. Systems that already exist

These should not be put back on a “build from scratch” list just because their original plans are still present or have stale status text.

| System | Current evidence / scope |
|---|---|
| 100-floor base game | 100 YAML files, 425 encounters, 100 wardens, with progression/economy functions. Content depth and verification vary by floor. |
| Shared multiplayer tower | Authoritative worldd game loop, shared warden frontier, quorum bosses, presence and per-room player grids. [World effects][social] · [presence][presence] |
| Guilds/factions and social play | Guild/faction halls, profiles, messages, money transfers, item gifts, and looting are implemented. Plan 042's old “draft” status is misleading. [Profiles][profiles] · [world effects][social] |
| Daily/nightly/weekly rewards | Contract board, dawn behavior, night work, and weekly reward selection exist. Weekly choices are now honestly named Gold / Extra XP / Free repair / Luck charm. [Contracts][contracts] · [weekly][weekly] |
| Repair tokens | Award and spend paths exist; the older research claim that they cannot be spent is obsolete. [Forge implementation][core] |
| Weapon/equipment work | Weapon paths, training, gear slots, inventory capacity, sockets, shared rigs, and real equipped gear in 3D combat exist. [Shared rig][rig-plan] · [economy][economy] |
| Early-game smoothing | 081 records all eight phases completed, including directed notifications, level-up explanation, beginner pity, gear clarity, and the encounter-sheet fix. [Execution status][smoothing] |
| Web play and account entry | Browser game loop, account/authentication and Google OAuth code, homepage and funnel integration exist. This audit did not retest live sign-in or analytics delivery. |
| End-of-era machinery | Era closure, reincarnation records, ceremony, and a manual reset tool exist. Operational rehearsal and concurrency concerns remain below. [Era code][era] |

## 4. Important unfinished reliability and endgame work

These are supported by current code or explicit unresolved verification records; they are separate from missing maps and art.

| Item | Evidence now | Remaining work |
|---|---|---|
| **Large-siege contributor accounting** | The live warden record still truncates to the last 40 strikers. A separate `ascent_warden_damage` table now exists, but `_warden_fall` still calculates rewards and the memorial from the passed striker list. | Use complete contribution data for rewards/memorials and verify a siege with more than 40 distinct strikers. This is more specific than the old backlog's claim that no contribution table exists. [Code][social] |
| **Era-close concurrency** | `close_era` still loads player documents and rewrites them to add the ceremony. | Reproduce/review concurrent acts at era close and move delivery to a race-safe mechanism if needed. The old backlog explicitly flags this; this audit did not run the race. [Code][era] · [ledger][continue] |
| **Permanent era history** | Frozen history still stores `stone[-400:]`. | Preserve the full history if “the Tower remembers every name” remains the requirement. [Code][era] |
| **End-to-end era reset rehearsal** | Reset code and tests exist; the deferred ledger says the complete announce → freeze → reset → return flow was not rehearsed. No later complete rehearsal was established in this audit. | Perform and record a full rehearsal on a disposable QA world. [Ledger][continue] |
| **Contract stability during a day** | The daily board is generated from `(day, live frontier)`; the code documents that a frontier change can change jobs. | Pin the generation frontier for the day if contracts must remain stable. [Code][contracts] |
| **Browser action deduplication** | `/play/api/act` passes an empty idempotency key, although the shared game runner supports deduplication. | Verify repeated/retried actions and add a stable per-action key if necessary. Existing row locks serialize actions but are a separate mechanism from deduplication. No live duplicate-charge bug was reproduced here. [Web route][webplay] |
| **Deep death costs** | The 20% weapon-loss rule remains; its deep-cost acceptance test is still marked xfail pending the design decision. | Decide the intended loss/repair policy at depth, then make that gate pass. [Open balance issues][balance-issues] |
| **Rumor reward** | `rumor_day` is still written by the present roll; no read was found in the game code. | Give it a gameplay effect or retire the promise/reward. [Core][core] |

Other entries in the old deferred ledger—reward tuning, dawn healing mid-fight, assist credit, flare feedback, and telemetry calibration—remain review candidates. They have not all been revalidated as current defects and should not be presented as confirmed bugs.

## 5. Deferred ideas, not current implementation failures

The [022 plan][clocks-plan] explicitly deferred these until the existing loops need expansion:

- Professions and ranks; gathering/salvage/crafting progression.
- Hirelings and richer offline missions.
- Per-fight quality bonuses and additional regeneration/energy systems.
- Player-built structures and the associated ownership/siege gameplay from the original vision.
- Full synchronized party combat. Existing flares, assistance, shared wardens, and quorum commits are smaller cooperative systems, not that planned shared-round combat.

The original sidekick vision also includes a richer companion sheet, growth, agent-specific encounters, and limited free-text persuasion. Those remain concepts unless deliberately brought into an execution plan. The existing nightly work loop should not be counted as missing simply because richer professions were deferred.

## 6. Stale plans that need reconciliation

- `MUST_BE_DONE_LATER.md` says later floors lack body/bite archetypes. **Current YAMLs do contain these traits throughout all ten bands.** The remaining question is quality/balance and wider lint coverage, not adding traits from zero.
- The old “repair token has no spend path” claim is false now: Forge spending exists.
- Plan 042 is labeled draft, but profiles, gifts, looting, and presence code exists.
- Old portrait/weekly plans say “not deployed”; later shared releases include their implementation. Their original status lines alone do not establish current deployment state.
- The initial 100-floor arena plan says only 14 arena backgrounds existed. **The current count is 122**, covering floors 1–20.
- The floor-1 map plan's original 640×480 specification was changed during later phases; the shipped map is **492×369**. This is not a missing resize task.
- Classes/off-class penalties in older ideas were superseded by the weapon-path work. Do not revive those older requirements automatically.

## 7. Suggested completion order

1. **Settle the canonical floor roster and geography**, starting with floors 11–20 and the next 3D batch, 21–30. This prevents new maps and expensive models from following conflicting content.
2. **Finish one complete map expedition on floor 1**, then all three difficulty paths, with saved progress, retreat, rewards, and browser verification. Use that as the template for later floors.
3. **Expand by floor batch:** canonical YAML + NPC + map + quest content + combat assets + arrival presentation + balance/visual acceptance. The next existing arena phase is [21–30][arena-phase3], currently 50 foe IDs.
4. **Finish the proposed onboarding flow** and relocate useful shardmind advice so a first-time player can discover the content already present.
5. **Close test and endgame accounting gaps** before deeper floors and larger populations depend on them. Keep speculative professions/structures on a separate future list.

## 8. Verification performed for this audit

- Loaded all 100 floor YAMLs and recomputed map, NPC, monster-kind, portrait, model, and backdrop coverage.
- Confirmed the floor YAMLs and the arena/map/Labs gate files match between the plugin submodule and the vendored worldd copy.
- Read the current gates and rendering paths, relevant phase records, the explicit deferred-work ledgers, and selected implementation/tests.
- Ran existing tests with the repository's available Luna Python environment:

  ```text
  ../luna/.venv/bin/python -m pytest -q \
    tests/test_082_floormap.py tests/test_067_arena.py tests/test_038_mercy.py \
    --disable-warnings --tb=short
  ```

  Result: **44 passed, 1 failed**. Failure: `test_067_arena.py::test_distance_move_and_chase_recorded`; the test expects the first event's actor to be `me`, but it is `foe`. Earlier dojo records mention this same failing test. This audit does not establish whether the present failure is obsolete test expectations or a gameplay defect.

- Did not run the full suites, deep simulations, fresh browser walkthroughs, or production verification. Historical dojo results are identified as historical, not rerun here.

[map-vision]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/plans/082-floor-maps/map-vision.md
[map-plan]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/plans/082-floor-maps/level001-plan/plan.md
[map-code]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/floormap.py
[labs]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/labs.py
[arena-plan]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plans/100floors-attack3dscene/PLAN.md
[arena-phase3]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plans/100floors-attack3dscene/phase-3/PLAN.md
[arena-code]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/arena.py
[story-plan]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plans/038-story-revamp/pre-plan.md
[schema]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/content/schema.py
[world-summary]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plans/030-the-world-you-can-see/execution_summary.md
[rig-plan]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/plans/080-shared-player-rig/PLAN.md
[onboarding]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/onboarding/RESEARCH.md
[smoothing]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/plans/081-early-game-smoothing/PLAN.md
[shard-residue]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/onboarding/shardmind-residue.md
[render]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/render.py
[ideas]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/vision/ideas.md
[state]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/state.py
[core]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/core.py
[continue]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plans/022-one-world-many-clocks/we_have_to_continue_this.md
[bestiary-test]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tests/test_017_bestiary.py
[sim]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tools/sim046.py
[later]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/MUST_BE_DONE_LATER.md
[economy]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/economy.py
[map-dojo]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/dojo/results/0061-082-floormap-1h-2026-08-27/summary.md
[arena-test]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tests/test_067_arena.py
[shop-arrows]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plans/079-shop-delta-arrows/PLAN.md
[lore11]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/vision/lore/floors/floor_011.md
[yaml11]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/content/floors/floor_011.yaml
[social]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/social.py
[presence]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/presence.py
[profiles]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/profile.py
[contracts]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/contracts.py
[weekly]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/weekly.py
[era]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/era.py
[webplay]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/webplay.py
[balance-issues]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plans/046-thirty-percent-a-floor/issues.md
[clocks-plan]: /Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plans/022-one-world-many-clocks/plan.md
