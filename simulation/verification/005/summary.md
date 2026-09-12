# Strategy-search verification — 12 September 2026

Environment: local simulator, Python 3.9.6, 8 detected CPUs, actual game 0.111.0. No production state. Engine SHA: 3217d52ec623a7b41376921310173bf681573edbe6c9e9d730fccc6a7ae29dae. Implementation commits: 69bf1cc (planner/observations), 932aa50 (search and long-run action correction); dashboard changes pending final commit.

The first user action to verify is opening a stronger path and pointing at floor 5 to read the typical and fastest days.

| Scenario | Result | Evidence |
|---|---|---|
| Actual-engine planner / search automated suite | PASS | 56 tests, final run 35.242 seconds; CPU identity, probe non-mutation, real costs, full-document replay, disjoint validation, run/report HTTP endpoints. |
| Browser defaults / copied radio choices | PASS | Rusher unchecked; Planner checked. Copying the 30-day canary selects Magic, levels first, margin 1 and improvement checks. |
| Browser starts a configured strategy | PASS | At 390 px, selected Bow, training first, margin 0; 1 player, 1 day, 1 minute/day, seed 2100. Saved in 2.9 seconds. |
| Browser replay of that run | PASS | 32 recorded inputs; complete document/scene/RNG match, SHA 26b497d13c4ed2ee3e8d5f3dcb54b93683562079056153d8a39a4c0be70a94d5. |
| Desktop and mobile | PASS | Inspected controls/charts at 1440×1000 and 390×844. Body scrollWidth equals 390; complete floor-5 tooltip stays inside phone viewport. Screenshots validated-floor-5-desktop.png and validated-floor-5-phone.png. |
| Validated strategy report and paired graphs | PASS | 48 trials, 386.560s. Browser table matches per-seed medians (selected planner 7.5/8, corrected Mage 4.5/4). Floor 5: planner median 5.3345d, fastest 5d, Mage median 23d on seed 2001. |
| Validated planner full replay | PASS | 12,131 inputs; full document/scene/RNG SHA 4f6a22a5a2395bbc24a6339b0d411080aa80b96005cdc7633aea6c61afe2614b. |
| Mixed swarm median + fastest / missing points | PASS | 24 players, seed 2201: floor 8 fastest 19 days, Planner #17, 4/24 qualified; no population median. Floor 9 no qualifier and no fastest point. Full-range button shows axis through 100; default view zooms to reached floors. |
| Diagnostic filtering / strategy reuse | PASS | 0 disqualified entries by default; 48 after opting in. Selecting one displays exclusion warning. Apply winner selects staff / levels / margin 2 / improvement probes. |
| Deep link | PASS | After correcting initial hidden-result navigation, direct ?run=...#game-quantiles opens at the rendered graphs. |

Browser access briefly disconnected, then recovered. A transient network error from the planned local-server restart remained in the page until reload; no run/replay failure. The saved-run loading failure found in the walkthrough was fixed by renaming the global history function; see regressions.md.

The 48 old test-only files listed in archived-test-files.txt were moved into simulation/game-runs/test-artifacts, preserving all bytes and removing them from normal history. Future search tests save within their temporary test directory. No production data or user run was deleted.

Both selected validation cohorts were repeated after fixing deterministic equal-power tie ordering, using four player workers instead of one. Complete semantic fingerprints are identical to the published cohorts: seed 2001 in 47.1415s and seed 2002 in 46.8114s. See repeated-winner.jsonl. Cross-process hash-seed regression also passes.
