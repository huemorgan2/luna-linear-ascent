# 080 phase-4 — judgment run, docs, learnings

## Goal

The whole plan is judged end to end in a real browser and the learnings are
written down. Measurable: a dojo results folder with per-scenario verdicts
and screenshots; 1bit-images.md and the scene READMEs updated; execution
status appended to every phase PLAN.md.

## Steps

1. Run the four scenarios in `worldd/tests/080-shared-player-rig/` against
   the local worldd (uvicorn :8600), screenshots at every judged step.
2. Write `dojo/results/NNNN-080-shared-player-rig-<date>/summary.md`
   (commit SHAs, environment, PASS/FAIL table, regressions list — check the
   existing `dojo/results/` numbering for the next NNNN, other agents also
   allocate numbers).
3. Full suites: worldd pytest + plugin pytest; compare against the recorded
   baseline — regressions are filed, not quietly fixed.
4. Docs: `plugin-linear-ascent/vision/1bit-images.md` gains the fight-scene
   learnings (tone curve in a tinted scene, lift-vs-curve coupling, one-rig
   pipeline); figure3d/fight3d READMEs describe the lib split.
5. Append "Execution status" to each phase PLAN.md; commit.

## Verification

The results folder exists with evidence for every verdict; suites' failure
set is a subset of the baseline; docs committed.

## Rollback

Docs/results only — `git revert` if ever needed.

## Execution status

**Done** (2026-08-25). Dojo run 0051
(`dojo/results/0051-080-shared-player-rig-2026-08-25/`): all four scenarios
PASS with screenshots — portrait harness (human/elf/giant dressed through
lib), finisher-ink harness (continuous ramp in tint), live finisher-gear and
arena as fresh account DojoEighty (kill of grey_wolf, rig attr carried the
starter gear). Suites: worldd `215 passed, 0 failed`; plugin `8 failed, 1369
passed` — all 8 fail identically at pre-080 dc0742e (checked in a detached
worktree), so the failure set is a subset of baseline; the 3 stale kill3d
tests are filed in the plugin's MUST_BE_DONE_LATER.md §8. Docs:
`vision/1bit-images.md` gained "One rig pipeline, two stages (080)";
`fight3d/README.md` written; `figure3d/README.md` already updated in
phase 1. No regressions found.
