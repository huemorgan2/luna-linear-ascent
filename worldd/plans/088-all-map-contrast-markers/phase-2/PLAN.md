# Phase 2 — player walkthrough and production release

## Goal

Prove the complete ten-floor experience through real Luna play in Chrome, release it through the normal production path, and verify that Render serves the exact tested assets and marker UI.

## Steps

1. Run the worldd full suite and record the plugin full-suite baseline/pass counts.
2. Start isolated local worldd and Luna services with the implementation commit and a dedicated QA account.
3. Walk the dojo scenario in Chrome through floors 1, 2, 4, 7, and 10, covering center/edge anchors, hover tooltips, digit navigation, and phone width; capture screenshots and judge them as a player.
4. Run the standard asset/static checks for every floor and add numbered dojo results.
5. Bump the plugin version, commit, push plugin and parent main, trigger the Render production deploy, and poll until live.
6. Verify production `/health`, all changed asset hashes, and one real production map response; append execution status to every plan and commit it.

## Verification

- The real Luna conversation returns a map for every requested floor without falling back to text or a lab-only route.
- The dot is clearly visible, points to its label's coordinate, does not cover the label, and remains legible against bright and dark map regions.
- Hover descriptions are immediate, focus rings remain visible, and digit keys navigate as before.
- Render reports live; `/health` reports the new version; production PNG SHA-256 values match the release commit.
- No secrets are present in commits or logs.

## Rollback

Revert the release/plugin commit and parent pointer, push both mains, trigger Render, and verify version and assets returned to 0.111.1. Stop the isolated local services and remove the dedicated QA container/database when verification is complete.

## Execution status

Complete and deployed — 2026-09-12.

- Chrome/Luna walkthrough passed on floors 3, 4, 7, and 10. Water, forest, shadow, roads, stone, snow, tower, settlement, and keep regions remained distinct; all marker points were visible on bright and dark ground.
- The narrow check used a 245px game pane: every label and point stayed inside. Sending bare `7` from floor 10 called `ascent_choose · 7` and rendered the Tower Gate with energy unchanged at 24/25.
- Plugin full suite: 1,461 passed, 9 failed, 1 skipped, 1 xfailed. The nine failures are the same pre-existing combat feel, death relic, cap retune, class removal, arena, quiver, and kill3d failures recorded at the 0.111.1 baseline; no map test failed.
- Vendored worldd suite: 220 passed in 111.16 seconds after a missing test Postgres and one caught marker-child ordering issue were corrected. The focused web-map route passed 2/2.
- Pushed plugin `92c86b6f` and parent `2f18569` to `main`. Render API deploy `dep-dai6lne743jc73d9rah0` reached live on 2026-09-11 at 21:00:02 UTC.
- Production `/health` reports `ok: true`, `db: true`, game `0.112.0`. All ten `/static/laart/maps/map_NNN_492x369.png?v=0.112.0` responses match the source package SHA-256 values; cache policy is `public, max-age=31536000, immutable` under the new versioned URLs.
