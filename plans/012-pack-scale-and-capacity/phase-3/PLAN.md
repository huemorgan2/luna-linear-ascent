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

## Execution status

**Executed 2026-08-17. Complete — both halves live, dojo PASS 14/14.**
- Version 0.87.0 (`version.py` + `luna-plugin.toml`), plugin `0527f47`
  pushed to origin/main (on top of the parallel session's 0.86.1 / 063,
  which had not been deployed).
- Vendored via `tools/vendor_game.sh`; worldd suite 370 passed (one
  order-dependent flake `test_web_play.py::test_leaderboard_marks_only_you`
  passes alone; unrelated). Root `d214780`, pushed.
- `worldd/tools/deploy.sh` → `dep-da1js87qj5pc73d7iji0` live; prod
  `/health` → `game 0.87.0`.
- Marketplace publish 0.87.0, index sha256 `e3efc4357361b6c6…` == zip.
- Dojo run 0035: `dojo/results/0035-012-pack-capacity-2026-08-17/`
  (hybrid: prod HMAC probes + local walkthrough on the shipped code with
  Chromium measurements) — PASS 14/14. Scenario
  `luna/dojo/tests/pack-capacity/scenario.md`.
