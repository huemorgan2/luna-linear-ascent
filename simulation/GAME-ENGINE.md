# Actual game-engine simulation

The default simulator imports `plugin_linear_ascent.engine.core` through `worldd/app/gamepath.py`, the same resolver called by `worldd/app/game.py`. Every player choice goes through `core.apply_choice`; reads go through `core.current_scene`. It does not translate a choice into a copied damage, reward, upgrade, repair, training, death or energy formula. The existing proposal resolver is retained only as a historical experiment under `/proposal` and `proposal_run.py`.

## What is exact, and what is a test setup?

| Responsibility | Implementation |
|---|---|
| Combat, enemy selection/specimens, counters, wear, loot, XP limits, death | Imported game engine |
| Purchases, equip/hold gates, honing, repairs including XP, School, character training | Imported game engine |
| Energy regeneration, sleep, dawn, interest and banking | Imported game engine, reading virtual time |
| Action choice, attendance, route preference and session duration | Deterministic software heuristics |
| Time and persistence | Synthetic local player documents; clock isolated per thread/process |
| Shared-world frontier | Explicit scenario input, recorded in replay |
| Shared warden victories, pledges, database effects, other players' social actions | Not executed; party-demand outcomes are unavailable |
| Readiness probes | Disposable copies with owned equipment/condition, full HP/energy and test-floor access; real engine hunts |

A Scene is a plain data object returned by the engine. Building that object does not require its HTML renderer, a browser, HTTP, a game account or an LLM. The headless runner retains engine scene construction for correctness. It can later be optimized in the game library with parity tests; it is not replaced with a second resolver here.

The imported checkout initially reports **0.111.0**, loaded from `worldd/vendor/plugin_linear_ascent`. That is an observed local source revision, not a claim about the currently deployed website. The package path, version, every Python/YAML/JSON source hash, Python version and runner hash are saved in each run. The game's existing `ASCENT_GAME_PATH` override is honored by the same import resolver. To simulate another code revision, check out/build that revision in the repository and start a fresh process. Source changes during a run cause a refusal to save mixed-source results.

## Current versus proposed mechanics

The current imported engine starts at one weapon slot and sells additional slots through the School. Its ordinary/deep hunts are individual encounters; current deep-hunt energy and capped XP rules remain in force. The proposal's fixed three-weapon decks, group reward escrow, overflow XP, four upgrade grades and replacement warden healing law are **not injected**. To simulate those rules accurately, implement them once in the actual game library, then have both the live service and this runner import that library. Existing adapter tests should be updated as intentional game contracts change.

## World access and calendar days

Default `world_frontier=0` is an explicitly staged **personal-readiness experiment**. After a player qualifies for a floor, the synthetic host opens the next floor. This external setup stands in for world unlocks and excludes time waiting for a multiplayer world to advance; it is recorded as `@world_frontier` in the action trace. It can affect the game's real frontier-dependent prices and reward fade and therefore must not be confused with live-server elapsed progression.

Set a positive `world_frontier` to keep that frontier fixed for the whole run. Bots may only travel to accessible floors; readiness probes can test later floors on disposable copies. No probe grants its rewards, repaired gear, XP or time to the real simulated player. The default gate is seven wins from eight sampled hunts, not proof of an 80% true win probability. Readiness is tested daily at session boundaries; first-detection delay is bounded by the configured probe cadence, attendance and active encounters. A run-end check is also made when no fight is active.

Calendar time assumes the supplied attendance, minutes/day, sessions/day and seconds/action. Navigation, shops and training consume the same configured action time as combat. Between sessions the virtual clock advances; the real game decides what regenerates. There is no invented hourly/daily reward. Equal allocation to named strategies is an experimental sample, not an estimate of the real player population.

## Bots and diagnostics

Learner uses the lead weapon; Tactician reads the game's attack hints and learns counters; Saver banks and chooses a lower floor; Rusher pushes accessible/deep hunts; Archer and Mage buy/train their chosen path. All start through the actual character-creation flow with normal resources. Purchases are chosen from actual shop availability and actual library prices, then submitted to the engine for validation. These are fallible heuristics, not optimal players. They do not read future RNG or copy disposable probe rewards.

The run contains per-floor hunts, kills, deaths, gold/XP and actions, milestone dates, signed game ledgers, decision blocks, daily timelines, the last readiness probe's creature-level verdicts, recent action receipts and complete final player documents. Game ledger bank deposits/withdrawals are transfers, not wealth destruction/creation. A historical milestone records that the player qualified once; it is not a promise they can sustainably farm at that floor forever.

The first `trace_players` players (six by default) retain all engine reads, choices and external clock/frontier inputs. Replay executes those inputs again through the current engine, rejects source mismatches, and compares the **complete final document including the scene and RNG counter**. Other players retain final state and recent actions. Re-run with more complete traces if investigation needs them; this avoids retaining millions of navigation records for every large swarm member.

## Wardens

The inspector shows the real library's warden HP, hourly regeneration fraction and milestone quorum. Those parameters are not a simulated party victory. The server's shared pool, pity, pledges, rewards and unlock transactions live in PostgreSQL-backed worldd services; they are not replaced with local formulas. Required party size is `null` and is labeled not measured. Floor 100 therefore keeps its current milestone distinction in this inspection. The proposed simultaneous-healing design must first be implemented in the actual shared service, then tested through that same service using isolated world storage.

## Verification and portability

`python3 -m unittest discover -s simulation/tests -v` includes direct-core document/scene/RNG parity, actual entry charges and XP-gated repair, thread-local clock isolation, source guards, source-mutation rejection, CPU parity, probe non-mutation, fixed frontier and HTTP lifecycle. Browser evidence lives under `simulation/verification/003/`.

Run on Python 3.9+ with the game's PyYAML dependency (`python3 -m pip install -r simulation/requirements.txt`). Automatic CPU detection respects affinity where available. Spawned processes isolate player state and use deterministic logical IDs; Windows pools are sharded past the per-pool 61-worker limit. Engine code/content remain in the same repository as the simulator. No PostgreSQL or production access is needed for the personal-engine runner.
