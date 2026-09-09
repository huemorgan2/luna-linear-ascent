# Phase 4 — browser acceptance, full tests and release

## Goal

Release the verified standard maps and blackout transition, with evidence that a player can use them and a durable record of any incomplete external step.

## Steps

1. Run the plugin full suite and worldd full suite sequentially against an isolated local QA database. Record baseline failures and any new failures separately; fix new regressions before release.
2. Start/reload local worldd and QA Luna as described by run-dojo. Record version and health. Use disposable QA players with floors 1–11 available; never reset real player data.
3. Follow `worldd/tests/085-floor-maps-standard/scenario.md` in the browser. Capture and inspect desktop and phone screenshots for every map; hover/focus descriptions; exercise mouse, touch and number-key routing, camp conversation and floor-10 keep.
4. Record first-frame, mid-ride and final states for ascent/descent/Roothollow return. Confirm full black background, reliable input lock/release, no stale layers or unwanted replay.
5. In QA Luna, use the first query “show me floor 2”, then the displayed gate number as plain text; verify stateful tool/card behavior and the shared renderer. Exercise changed consumer categories rather than treating static HTML as sufficient.
6. Write `dojo/results/0062-085-floor-maps-standard-2026-09-09/summary.md` (or next unused number), evidence and regressions. Rerun affected scenarios after fixes.
7. Scan staged text for secrets, commit plugin and parent changes in scope, publish the intended release commits, explicitly deploy via `worldd/tools/deploy.sh`, and verify health version plus maps 001–010 served from production.
8. Perform production presentation checks using an authorized QA account. Update each phase/top-level status and the project gap audit to reflect only completed work. Report exact saved paths, generation method, tests, dojo and deployment result.

## Verification

All scenarios pass with screenshots/DOM evidence and backend state where actions spend or navigate. No new suite failures. Source/vendor agree. Production health reports target version, assets return correct image content, maps need no Labs opt-in and elevator background stays black. Unavailable required checks remain explicitly incomplete.

## Rollback

Revert release implementation commits (plugin plus parent vendor/pointer), push the rollback release and run `worldd/tools/deploy.sh`; verify restored health/version. Keep QA results and original plan history. Do not revert unrelated work or touch production player data.

## Execution status

Not started.
