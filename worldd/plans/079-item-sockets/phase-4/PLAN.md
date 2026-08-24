# Phase 4 — E2E judgment run + learnings

## Goal

Both scenario walkthroughs pass with screenshot evidence in a numbered
results folder; the placement learnings are appended to
`plugin-linear-ascent/vision/1bit-images.md`. The plan is only reportable
after this phase.

## Steps

1. Run `scenario-portrait.md` and `scenario-finisher.md` end to end in the
   browser (screenshots at zoom, per-check verdicts).
2. Write `dojo/results/NNNN-079-item-sockets-<date>/summary.md` with the
   PASS/FAIL table, environment, commit SHAs, and screenshots; regressions
   found are FILED in the summary, not silently fixed mid-run.
3. Append to `1bit-images.md`: the socket/character-space lesson, the
   no-finger-bones grip illusion, the flat-normalization rule for discs,
   and the prop emissive-lift floor against the crushed-black curve.
4. Append "Execution status" to every phase PLAN.md; commit.

## Verification

The results folder exists with evidence for every scenario check; each phase
PLAN.md carries its execution status; final commit pushed to `origin main`.

## Rollback

Documentation-only phase — `git revert` of its commit.

## Execution status (2026-08-24)

DONE — dojo run `dojo/results/0049-079-item-sockets-2026-08-24/`
(9 screenshots, per-check PASS tables for both scenarios). Learnings
appended to `plugin-linear-ascent/vision/1bit-images.md` ("Item
placement — sockets, not offsets"). Pre-existing regression filed in the
run summary: test_leaderboard_marks_only_you fails at clean HEAD.
