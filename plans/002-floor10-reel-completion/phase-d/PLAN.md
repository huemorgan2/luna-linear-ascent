# 002 Phase D — ship 0.51.1 (worldd + marketplace)

## Goal
Version 0.51.1 (Phase C reels, landscapes, contrast grade, lore swaps) live on
BOTH halves of the play surface: `ascent-worldd.onrender.com/health` returns
`"game": "0.51.1"` AND `marketplaces.com.ai/mp/official/index.json` lists
plugin-linear-ascent 0.51.1 with sha256 matching the local zip. User go
2026-08-08: "yes deploy it both to the website and the plugin". Note the
marketplace is currently 4 versions stale (0.47.0 vs worldd 0.51.0 — the
disk-blocked backlog), so this publish also heals an existing hybrid surface.

## Steps
1. **Clean parked takes from the working tree** (they'd be zipped otherwise):
   back up the 11 parked slugs' gifs to scratchpad, `git checkout --` the
   tracked ones, remove the untracked ones. Raw mp4 masters stay (gitignored,
   outside the package dir).
2. **Bump** `plugin_linear_ascent/version.py` + `luna-plugin.toml` → 0.51.1.
3. **Tests**: `uv run --project ../luna python -m pytest tests` (full plugin
   suite; combat.py change is text-only, no economy → difficulty gate n/a).
4. **Commit + push plugin repo** (gh account huemorgan2; check ls-remote
   first, merge don't force).
5. **Vendor**: `worldd/tools/vendor_game.sh`; verify vendored version.py says
   0.51.1. Worldd tests only if pg:5433 is up (no engine-contract change).
6. **Parent commit** vendor + submodule pointer; push → Render auto-deploy.
7. **Poll** `/health` for `game: 0.51.1`; if stale ~10 min, manual deploy:
   `render deploys create srv-d9ha3csvikkc73ff5rg0 --confirm --wait`.
8. **Marketplace**: `package_plugin.py` → zip; `publish_plugin.sh <zip>
   official` with `~/Documents/Luna/luna-plugins/.env` sourced. If the 1GB
   disk rejects the upload, STOP and report (user decision: delete-and-
   republish / grow disk / prune endpoint) — do not work around.
9. **Verify**: index.json version+sha256 vs local zip; /health game field;
   UA-headed probe (edge 403s bare curl). Dojo-style spot check of a shipped
   reel asset inside the published zip.

## Verification
- `curl -A probe /health` → `"game": "0.51.1"`
- `index.json` → plugin-linear-ascent 0.51.1, sha256 == `shasum -a 256` of
  local zip
- Published zip contains a Phase C gif (e.g. `native_freed_320x112.gif`) with
  the same bytes as the committed file, and NO parked-slug fresh takes.

## Rollback
- worldd: `git revert` the vendor commit in the parent, push, redeploy;
  /health returns previous game version.
- Marketplace: cannot re-publish a version (409) — rollback is publishing
  0.51.2 built from the pre-phase-C commit (0a17571).
- Plugin repo: `git revert` the bump commit.

## Execution status (2026-08-08)

WORLDD HALF SHIPPED, MARKETPLACE HALF BLOCKED ON FULL DISK.

- Working tree cleaned of 11 parked slugs' failing takes (22 files backed up
  to scratchpad); package dir verified clean vs HEAD.
- Bump 0.51.1 committed (plugin 7af71c3) and pushed; 921 plugin tests passed,
  1 skipped.
- Vendored 0.51.1 (30 py, 100 yaml); parent vendor commit pushed
  (a5000f8..4179304). Render auto-deploy did NOT fire (recurring known
  issue); manual deploy dep-d9rfi3qjnfac73fjmkng succeeded.
- VERIFIED: /health returns "game": "0.51.1", db true.
- Marketplace upload of plugin-linear-ascent-0.51.1.zip (45 MB, sha256
  99468ec4...) failed HTTP 500 twice + once via direct curl. Root cause
  confirmed in luna-marketplaces logs (srv-d8m7nct8nd3s73dofrm0):
  "OSError: [Errno 28] No space left on device" in
  app/routers/plugins.py:119 upload_plugin. The 1 GB disk is full.
  Render SSH inspection was classifier-blocked; stopped per plan step 8.
- Marketplace remains at 0.47.0 → players see a hybrid surface (0.51.1
  scenes, 0.47.0 renderer) until the disk decision unblocks the publish.
  Decision owed by user: delete-and-republish / grow disk / prune endpoint.

