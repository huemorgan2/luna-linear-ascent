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
