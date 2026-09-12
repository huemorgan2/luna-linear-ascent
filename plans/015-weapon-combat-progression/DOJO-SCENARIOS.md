# Browser verification — revised group/deck plan

These scenarios replace the original single-hunt verification. They are future execution requirements, not completed tests. Run the actual web game and a multi-turn Luna conversation through the shared engine/service; simulator results alone cannot judge the experience. Each scenario has Preconditions, Scenario, Expected behavior, Fail conditions and Verify.

| Scenario | Phases |
|---|---|
| [S01 — Current behavior and source baseline](dojo/S01-current-baseline.md) | 1 |
| [S02 — Returning players and ownership conversion](dojo/S02-item-conversion.md) | 2,7 |
| [S03 — First session: collection, group, Forge](dojo/S03-opening-loop.md) | 3,7 |
| [S04 — Three selected weapons and contrasting groups](dojo/S04-combat-decisions.md) | 3,4,7 |
| [S05 — Movement, effects, shields and arrivals](dojo/S05-movement-shields.md) | 3,4,7 |
| [S06 — Forge/source settings and concurrent item actions](dojo/S06-forge-concurrency.md) | 3,4,7 |
| [S07 — Material routes, grade access and recovery](dojo/S07-grade-boundaries.md) | 4,5,7 |
| [S08 — Kill XP, pending haul and all outcomes](dojo/S08-loot-recovery.md) | 3,5,7 |
| [S09 — Actual overlapping attacks and floor100](dojo/S09-shared-wardens.md) | 6,7 |
| [S10 — Collection and profile across users/clients](dojo/S10-collection-profile.md) | 2,3,7 |
| [S11 — Per-enemy energy, waiting and exhaustion](dojo/S11-energy-boundaries.md) | 3,7 |
| [S12 — All creatures, weapon art and honest drop odds](dojo/S12-wiki-content.md) | 4,7 |
| [S13 — Median, fastest and extra days using the real game](dojo/S13-simulator-results.md) | 5,7 |
| [S14 — Migration, rollback and serving verification](dojo/S14-release-rehearsal.md) | 7,8 |

Use isolated QA data and the matching plugin/vendor/service revision. Before the walkthrough write the most likely player query (opening example: “play linear ascent”), then actually use it. Where fixture floors/resources are necessary for edge cases, label them and exclude them from calendar-progression claims. Fresh-account playability scenarios use ordinary authored resources only.

Each run writes a new numbered folder under `dojo/results/` with `summary.md`, date/SHAs/environment, per-scenario PASS/FAIL and timings, screenshots, receipt/query evidence and a regressions list. When a scripted browser runner is introduced, keep its scenario source here and its project-standard runner under `luna/dojo/tests/015-weapon-combat-progression/`; its exact invocation is recorded before execution. A script's exit status does not replace the agent's visual judgment.

Phase1 records baseline behavior and freezes timing thresholds. Phases2–6 execute their relevant scenarios before expanding scope. Phase7 runs the complete candidate suite plus the pinned-old baseline comparison; S14 is its QA release rehearsal. Phase8 repeats S14 and affected core flows on the actual serving release after explicit deploy authorization. Do not mark an implementation phase complete if its required walkthrough or backend checks are missing.
