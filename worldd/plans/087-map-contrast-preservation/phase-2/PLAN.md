# Phase 2 — integrate, verify, and release

## Goal

Ship the selected contrast-preserving floor-2 image through both plugin and vendored worldd paths with no gameplay, marker, or other-map regression.

## Steps

1. Add the selected mode to the repeatable map converter and rebuild only `map_002_492x369.png`; record formula, metrics, and hash.
2. Add meaningful regression checks for size, palette, source-tone metrics, unchanged maps 1/3–10, and rendered map wiring. Bump the patch version.
3. Sync the vendored package and verify it is byte-identical to source. Run targeted tests, then the full plugin and worldd suites against isolated databases.
4. Execute `worldd/tests/087-map-contrast-preservation/scenario.md` in a real browser and real Luna conversation. Save source/old/new comparison, desktop/phone screenshots, DOM, and a result summary.
5. Commit, push, explicitly deploy through Render, poll to live, and compare the production asset hash to the selected local file.

## Verification

All top-level visual/metric checks pass, existing markers and number actions behave once, no new suite failures appear, source/vendor match, and production health/static hash match the intended release.

## Rollback

Revert the plugin and parent release commits and redeploy. Verify the previous version and floor-2 SHA-256. No player data changes are involved.

## Execution status

Not started.
