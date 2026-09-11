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

Complete 2026-09-11. Dojo result: `dojo/results/0062-085-floor-maps-standard-2026-09-09/summary.md`. All 30 desktop/phone map views, all-floor CAMP/keep/GATE routes, mixed number rows, instant tooltips, Labs graduation, floor-11 fallback, opaque input-locked rides, and the real three-turn Luna conversation passed after the recorded fixes. Plugin focused: 84 passed. Plugin full: 1440 passed with the same 9 failures reproduced at baseline, plus 1 skipped and 1 xfailed. worldd full: 223 passed against the isolated `ascent_maps_tests` database. Source and vendor match.

Plugin commit `20b0b71` and parent release commit `b23d7bf` were pushed to `main`. Render deployment `dep-daht319594qs738g3f50` became live at 2026-09-11T10:06:32Z. `/health` reported `ok=true`, `db=true`, game `0.111.0`. Production maps 001–010 each returned an opaque two-color 492×369 PNG byte-identical to the reviewed local asset; floor 1 retained SHA-256 `2b47403f…be5b5`, and Roy's approved resized floor 2 retained `36c8e54a…4a61`. No production player data was written during verification. The authenticated presentation path was covered against the same vendored package in isolated browser QA rather than creating a permanent production test account.

> retro(phase-1, 2026-09-09): Roy approved the original floor-2 design and requested only lower resolution. Keep map_002_v1 composition, ship 492×369 like floor 1, and use its geography/scale alongside floor 1 as a reference. Do not perform the proposed texture redesign.

> retro(phase-2, 2026-09-09): Art coverage is complete. Use `art/anchors.json`; edge keep chips sit at x=91–93%, so align their right edge to the anchor. Verify tooltips against viewport edges and top of map, especially 320px phones. Baseline browser confirmed destination controls visible through the old lift veil.

> retro(phase-3, 2026-09-09): Browser smoke confirms the web behavior. QA Luna's real ascent_scene turn works, but its game iframe remains “waking the lift” without sending a scene request. The pane posts luna-ui-ready, while the shell sends its token on iframe load or luna-request-auth; a missed load handshake strands startup. Reproduce and verify the shell contract, then make the pane request auth on ready if confirmed. This stays in the shared pane, preserving unrelated dirty Luna host code. Rollback is reverting the additive auth-request message. Validate with an actual Luna map render and bare-number response before completion.
