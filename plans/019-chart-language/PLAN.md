# 019 — Explain progression charts in player language

## Problem and evidence

12 September 2026: the user's floor-5 tooltip says `Selected run: 28` under `Calendar days to hunting readiness`. The value has no unit or population meaning. Earlier screenshots confuse the percentage chart with the days chart. The user explicitly asks that it say days to become able to kill floor-5 monsters.

## Root cause

`simulation/web/game.js` reuses a generic series label and numeric formatter for days, percentages and counts. Statistical controls use terms such as `Population P90`. Missing values say `Not reached` without explaining who has not reached the floor or how long the simulation lasted.

## Emergency mitigation

Explained the screenshot in conversation. No game, simulation, saved result or production changes made.

## Fix — single phase

Update the actual-engine dashboard's chart titles, controls, units, floor details and tooltips. State days since starting, the floor, and whether the value describes half the players, 90%, or the average among finishers. Explain missing observations and show reached/total counts. Identify compared simulations only when a comparison exists. Keep the same data, statistical calculations, axes, rules and bot behavior. Fit longer tooltips within the viewport and support tapping a floor to read its explanation.

## Verification

Run JavaScript syntax checks and the existing full simulator suite. Perform the local browser scenario in `dojo/01-chart-language.md`; inspect desktop and narrow screenshots, actual floor-5 data, all three statistical modes, missing values, percentages/counts and comparison wording. This is a simulator presentation change; no game engine or worldd endpoint is changed, so the browser target is the local simulator rather than a production Luna session.

## Rollback

Revert the implementation commit (record its SHA after execution), refresh the local page, retain saved simulation JSON. No server restart or database operation is required.

## Execution status

Implemented and verified: plain-language titles, axes, statistical controls, units, missing results and floor explanations. Fastest-observed line uses existing milestone dates and names the winning player per floor. Existing 45-test suite passes; in-app browser confirms median/average/90%, percentage/count and comparison sentences, and readable narrow tooltips. Evidence: simulation/verification/004/summary.md. No gameplay or simulation calculations changed. Broader desktop/responsive verification continues with plan 020.

## User scope addition during execution

The user asks for the fastest player alongside the median. Add an earliest-player line computed from existing per-player milestone dates, preserving the median and missing values. Name the fastest player and strategy per floor; explain that the identity can change between floors. Verify both lines against saved JSON. Optimization of bot paths is tracked separately in plan 020.
