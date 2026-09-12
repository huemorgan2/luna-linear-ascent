# Phase 3 — Local run explorer

## Goal

Provide a readable game-styled website where the user can launch simulations, inspect saved runs, compare strategies and read progression and warden-demand graphs with honest uncertainty and missing results.

## Steps

1. Implement `python3 simulation/serve.py --port 8766`, serving only simulator assets/results and a bounded background run API on localhost.
2. Add controls for run size/horizon/seed, policy selection and numerical assumptions; show progress/errors and persist completed run files.
3. Build interactive graphs for cumulative days-to-readiness, floor readiness coverage, difficulty and the relationship between qualified player count and required warden party size. Include per-floor/cohort details, run comparison and raw download.
4. Use the existing IBM VGA font and a coherent dark game palette. Ship all assets locally with no external chart/CDN dependency.
5. Run coded server/data validation checks and the planned real browser scenario. Record numbered results with screenshots, runtime measurements and source/implementation commits. Fix observed regressions and rerun affected checks.

## Verification

`python3 -m unittest discover -s simulation/tests -v`; `python3 simulation/serve.py --port 8766`; GET `/api/runs`; create/read a run through the website. Execute `../dojo/01-run-explorer.md` and save evidence under `simulation/verification/001/`. Check narrow and wide layouts, null floors, run switching and invalid input feedback.

## Rollback

Stop the local server, revert the recorded phase implementation commit and leave saved runs intact. There is no public deployment to revert.

## Execution status

Complete. Implementation: `576feb9`. The localhost explorer launches automatic-CPU runs, keeps history, compares runs/cohorts and shows days, coverage, hunt difficulty, finite-energy warden demand, resource pressure and individual decks. Twenty simulator tests pass (3.186 seconds); the input snapshot checks and Python compile check pass. The real in-app browser first action created a 24-player/120-day run in 11.6704 seconds; a one-factor half-HP comparison completed in 4.1276 seconds. Real Chromium screenshots and DOM/JSON comparisons pass at 1440×1080 and 390×844, including tooltip data, missing floor-100 values, download, invalid input, history and focused graph axes. Evidence: `simulation/verification/001/summary.md` and adjacent images/observations. No public deployment or game runtime change. Rollback: stop the local server and `git revert --no-edit 576feb9`; generated runs remain intact.
