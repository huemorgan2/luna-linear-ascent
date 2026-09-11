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

Complete locally — 2026-09-11.

- Added the explicit `--tone-mode preserve-source` path to the existing converter; the default legacy path is unchanged.
- Rebuilt only floor 2 and bumped the source/vendored package to `0.111.1`. Source and vendor are byte-identical at SHA-256 `d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e`; the isolated HTTP response has the same hash.
- The new regression check proves 492×369 dimensions, full opacity, the exact two-color palette, source/vendor equality, tone range `>=0.470`, tone standard deviation `>=0.095`, and source correlation `>=0.970`.
- Targeted verification: plugin static-art `5 passed`; floor-map and contrast tests `3 passed`.
- Full worldd suite: `220 passed` in 107.30 seconds. Full plugin suite: `1441 passed, 9 failed, 1 skipped, 1 xfailed` in 22.75 seconds. The same nine unrelated combat/class/3D failures were present at the 0.111.0 baseline; this change introduced no new failures.
- Chrome desktop and narrow-layout review passed. The source-scale dark lakes and shadow masses remain distinct, structures and roads remain legible, all five markers remain visible, and the output remains crisp two-color art.
- QA Luna used this branch's plugin and isolated worldd. `Show me my current Linear Ascent scene. Do not choose an option.` called `ascent_scene`, rendered floor 2 without spending energy, and a plain-text `6` called `ascent_choose` and moved to the gate.
- Local QA rollback: stop ports 8610/8800 and remove Docker container `ascent-map-contrast-qa` plus `/tmp/ascent-maps-qa87`; production rollback remains the commit revert described above.
- Pushed plugin `c9877ae` and parent `cbe7c85` to their `main` branches. Render API deploy `dep-dai60h8jo6nc73fhvco0` reached `live` at 2026-09-11T20:15:27Z.
- Post-deploy `/health` reports `ok: true`, `db: true`, and game `0.111.1`. The production versioned PNG is 492×369, fully opaque, exactly two colors, and byte-identical to the selected local asset at SHA-256 `d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e`.
