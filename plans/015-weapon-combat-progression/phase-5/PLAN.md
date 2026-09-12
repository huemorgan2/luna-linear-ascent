# Phase 5 — Personal progression and complete economy

## Goal

Measure and tune actual whole-account progression toward the reviewed gentle slowdown, while preserving large legitimate advantages from deck, route and spending choices. Publish median and fastest observed capability without hiding stalled players.

## Steps

1. Extend existing simulation agents/planner/search for three-slot preparation, group completion, resource carry-over, exhaustion/escape decisions, arrows/effects and source-aware upgrades. Same real game library; no new balance resolver or hypothetical standalone harness.
2. Replace single-enemy readiness with recorded full-group probes and add repeated-hunt sustainability tests. Preserve immutable disposable probes, per-player event timing, cohort denominators and independent world-access fixtures.
3. Screen legal policies under matched seeds/schedules: generalist, several specialists, cautious/greedy continuation, focused versus broad upgrades, counter-ammo substitution, normal/deep and deliberately weak choices. Reject refusal loops as diagnostics; retain all run files. Freeze winners before fresh-seed validation.
4. Measure gold after all recovery/ammo/repair/death costs, XP reserve and training, both recipe materials, three useful weapons, grade access, optional guarantees, exhausted XP, partial-group farming and zero-resource recovery. Trace actual bottlenecks before retuning costs/supply/threat.
5. Use the proposed pacing envelope in `PROGRESSION-AND-SIMULATION.md` only after review. Keep exponential reference anchors, but measure group-level net outcomes. Record every coefficient change and reason; do not manufacture a smooth line or equalize routes.
6. Add/verify cumulative median+fastest, per-player extra-days intervals, reached counts, route costs and stall explanations in the dashboard. Start small, then extend horizon to cover the reviewed curve (e.g.365 days), with cohort size chosen for uncertainty and practical runtime. Use all available CPUs without nested oversubscription.
7. Publish source-pinned findings, replay samples, raw-run/config locations and remaining limitations. World-gated end-to-end conclusions wait for phase6; this phase measures personal capability and sustainability.

## Verification

Run `python3 -m unittest discover -s simulation/tests -v`. Extend existing `simulation/game_search.py` and `simulation/run.py` config/CLI only for implemented rules; record exact new reproduction commands in README and the phase report. Verify identical semantic outcomes at 1 worker and automatic workers, copied-probe non-mutation and replay. S13 checks both lines/tooltips, fastest identity, full-range missing values, per-player interval definitions and late-floor horizons. Grade/resource recovery scenarios S07/S08 must also pass through actual game play, with no test grants used as progression evidence.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Revert tuning/config/policy/chart commits in QA and rerun the same seeds on the previously pinned rules. Preserve all historical runs, search reports and changed-source hashes. Never rewrite completed player transactions or old reports to match new prices. Do not roll back the shared-engine architecture to the historical proposal simulator.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Not started. Rewritten for the three-weapon/group design on12 September2026; awaiting the user's plan review. This document is not evidence that runtime changes or tests have run.
