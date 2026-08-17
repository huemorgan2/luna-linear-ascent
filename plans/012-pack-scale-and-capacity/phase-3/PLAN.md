# Phase 3 — release 0.87.0: vendor, deploy, publish, dojo

## Goal
Both halves live at 0.87.0 (prod `/health` + marketplace index), dojo
walkthrough recorded.

## Steps
1. Bump `version.py` + `luna-plugin.toml` → 0.87.0; commit plugin; push.
2. `worldd/tools/vendor_game.sh`; worldd tests; commit root; push.
3. `worldd/tools/deploy.sh` → poll to live; `/health` game 0.87.0.
4. Package + publish to marketplace (memory: marketplace-publish-flow);
   compare index sha256 with the zip.
5. Dojo: scenario `luna/dojo/tests/pack-capacity/scenario.md`, run on
   local worldd (same code paths) with screenshots; results
   `dojo/results/0035-012-pack-capacity-<date>/summary.md`.
6. Append execution status to each phase PLAN.md; commit.

## Verification
- `/health` → `{"ok":true,"game":"0.87.0"}`
- marketplace index 0.87.0 sha256 == `shasum -a 256 <zip>`
- dojo summary PASS table.

## Rollback
Redeploy previous worldd commit (`deploy.sh` at a3ba1f7 lineage);
marketplace: yank 0.87.0.
