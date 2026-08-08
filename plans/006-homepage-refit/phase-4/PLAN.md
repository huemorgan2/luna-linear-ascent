# Phase 4 — ship

## Goal

Production serves the refit homepage with `/health` game `0.51.0`; the
same wizard face ships in the plugin for Luna chat play; a dojo
walkthrough against production passes with evidence.

## Steps

1. Plugin repo: bump `version.py` + `luna-plugin.toml` → 0.51.0; run
   plugin tests (`uv run --project ../luna python -m pytest tests`);
   commit ONLY the wick portrait + version files (parallel session's
   dirty files excluded); push as huemorgan2, switch back.
2. Vendor: stash the parallel session's plugin working tree changes →
   `./worldd/tools/vendor_game.sh` → stash pop.
3. worldd tests: full suite with `ASCENT_TEST_DATABASE_URL=postgresql://ascent:ascent@localhost:5433/ascent_world_test`.
4. Secret-pattern scan over the staged diff; commit outer repo (site +
   vendor + plans), push with token-masking sed.
5. Package plugin zip; attempt marketplace publish (expected-recovered
   or note the 500 again).
6. `render deploys create srv-d9ha3csvikkc73ff5rg0 --confirm --wait`;
   poll `/health` until `game` = 0.51.0.
7. Dojo walkthrough `plans/006-homepage-refit/dojo/01-homepage-refit.md`
   against https://linearascent.net in a fresh isolated browser
   context; archive summary to `luna/dojo/results/006-homepage-refit/`
   via the origin/main worktree dance; bump the outer gitlink.
8. Append Execution status to each phase PLAN.md; commit.

## Verification

- `/health` → `{"ok":true,...,"game":"0.51.0","db":true}`.
- Homepage live: story player advancing, trio with the giant, six
  vertical floors, Stone copy — all per the dojo scenario's evidence.
- Signup → /play regression check passes (dojo scenario step).

## Rollback

Redeploy the prior outer SHA (`git revert` the ship commit, push,
`render deploys create srv-d9ha3csvikkc73ff5rg0 --confirm --wait`).
Plugin: revert the 0.51.0 commit; marketplace still serves 0.47.0 so
no unpublish is needed.

## Execution status

**DONE 2026-08-08.** Plugin: my portrait committed as 0a17571 on top of the parallel
session's committed 0.51.0 (95c2e86 mercy revamp + c3c37c5 tools — already on origin/main,
so the vendor ships them by design); their uncommitted work stashed around vendor_game.sh
and restored (7 files they re-regenerated mid-dance kept their newer live copies; stash
"006-ship" retained as backup). Tests: plugin 920 passed/1 skipped; worldd 130 passed.
Shipped a26c952, deploy dep-d9re35740ujc73b947ig → /health game 0.51.0.
REGRESSION caught by dojo: Cloudflare served 4 h-stale site.js against new HTML (origin
sent no Cache-Control). Fixed b6ea68f (?v=0.51.0 asset URLs + origin max-age=60
must-revalidate on /static code files, test added), deploy dep-d9re5kv40ujc73b99g30.
Dojo 006-01 full walkthrough on production: ALL PASS (results archived at luna
00901f36, dojo/results/006-homepage-refit/). Marketplace upload still 500 (external) —
0.51.0 zip packaged from clean HEAD archive; publish retry pending.
