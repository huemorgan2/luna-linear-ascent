# Phase 3 — Results and browser verification

## Goal

Show understandable, traceable fastest/typical progression and independently validated strategy differences.

## Steps

Compare the old measurement mode, corrected baseline and planner. Summarize gains, resource causes, day-one progress and remaining bottlenecks. Surface the recommended planner and search report on the dashboard. Keep historical outputs separate and clearly identify changed runner settings.

## Verification

Full simulator suite; real-browser current/compared runs, both day curves, fastest strategy identity, report, trace replay and narrow/wide layout. Record numbered evidence and inspect screenshots before claiming completion.

## Rollback

Revert phase commit and refresh local dashboard; retain all run files and reports.

## Execution status

Implemented and verified. Search 20260912T195050Z-185ec874 and mixed run 20260912T195925Z-5edc5381 are saved. The latter ran 24 players/30 days in 80.284s on 8 CPUs, all traces retained, zero rejected actions. All 56 tests pass in 35.242s. Both winning validation cohorts reproduce identical complete semantic fingerprints on four workers after stable tie ordering. Browser walkthrough at 1440×1000 and 390×844 verifies matched comparison, fastest identity, missing medians, full 100-floor range, recommended settings, archived diagnostics, direct links and full replay. Evidence: simulation/verification/005/summary.md; findings: research/simulation-strategy-search/RESULTS.md. Game source unchanged. Default planner uses staff / levels / margin 2 after validation.

Rollback archive cleanup: for each filename in simulation/verification/005/archived-test-files.txt, move simulation/game-runs/test-artifacts/<filename> back to simulation/game-runs/<filename>, only if the destination is absent. Other rollback: revert the phase-3 commit, then 932aa50 and 69bf1cc, restart simulation/serve.py; retain run/search JSON.
