# Actual-engine measurements — 12 September 2026

The simulator now runs the checked-out game through `core.apply_choice`, not the proposal resolver. Engine source: 0.111.0, SHA256 `3217d52ec623a7b41376921310173bf681573edbe6c9e9d730fccc6a7ae29dae`. These are personal-engine experiments with an explicit staged-world frontier; they do not execute shared-world unlock/warden services.

## Initial repeated cohort

12 players × 30 days × three seeds; six policies allocated equally; 30 minutes/day, three sessions/day, 90% attendance, eight readiness trials. Engine rules identical throughout. Runner implementation 8935fb8.

| Seed | Median ready floor | Highest ready floor | Wall seconds | Run |
|---|---:|---:|---:|---|
| 1601 | 3 | 5 | 93.1335 | 20260912T182213Z-3ba602ac |
| 1602 | 4 | 5 | 106.1228 | 20260912T182400Z-a6afbf82 |
| 1603 | 3 | 5 | 51.2670 | 20260912T182451Z-268e4047 |

These timings include concurrent development/browser work and are not a CPU scaling benchmark. The original separate model's floor-12 stall and corrected floor-22 result are not interchangeable with these results.

## Findings requiring a policy follow-up

Most initial players stop sessions for low health; for seed 1601, eleven policies record 59–81 health-wait checks (the Rusher instead exhausts energy and repeatedly dies). Source inspection identifies a concrete omitted player choice: repeatable stew heals five HP for two gold (`core._eat_stew`, `economy.STEW_PRICE` / `STEW_HEAL_HP`). The initial heuristics offered full healer purchases but did not buy this cheaper partial recovery. This is a bot limitation, not evidence that the game's healing rule should be changed. The next verification changes only the smarter policies' recovery choices to consider this existing action and repeats the seeds.

## Matched recovery-policy experiment

Commit 45b97a5 adds the existing stew action to Tactician, Saver, Archer and Mage decisions. Learner and Rusher keep their original choices. Repeat every seed with identical settings and the same engine fingerprint; the runner fingerprint changes because its decisions change. The complete pair/config/result hashes are in [engine-comparison.json](engine-comparison.json).

| Seed | Median ready floor before → after | Highest after | Wall seconds after | Run after |
|---|---:|---:|---:|---|
| 1601 | 3 → 4 | 5 | 43.1678 | 20260912T182844Z-76f20825 |
| 1602 | 4 → 4 | 6 | 50.8905 | 20260912T182935Z-5430ac5f |
| 1603 | 3 → 4 | 5 | 58.1891 | 20260912T183033Z-6cd25faa |

Pooled across 36 players, median readiness after 30 days is floor 4. Zero of these 36 players qualify for floor 10 within the horizon. This describes these bots and settings; it does not establish a floor-4 game wall or predict average human progression. The observed readiness curve depends on recovery choices as well as game rules.

| Policy (six players each) | Median before → after | Mean paired floor change | Health-wait checks before → after |
|---|---:|---:|---:|
| Learner | 3 → 3 | 0 | 465 → 465 |
| Tactician | 3 → 4 | +0.50 | 459 → 339 |
| Saver | 5 → 5 | −0.17 | 394 → 344 |
| Rusher | 3 → 3 | 0 | 0 → 0 |
| Archer | 3.5 → 4.5 | +1.17 | 453 → 355 |
| Mage | 4 → 5 | +0.67 | 468 → 383 |

Health waits count bot decision checks, not days. All six Learner and all six Rusher outputs are exactly unchanged between matched runs. Several smarter policies progress further by using an available recovery option; Saver's small mean loss shows that spending more time and gold recovering can have a tradeoff. The six-player samples do not establish a stable ranking of strategies. No damage, reward, price, regeneration or training rule was changed.

## Verification

45 simulator tests pass in 10.059 seconds, including direct-core full document/scene/RNG parity, serial/two-worker equality, replay, isolated clocks, unchanged probe subjects, source-change refusal and real purchase costs. A dispatch test covers 128 logical Windows workers split across pools of 61, 61 and 6; this is not a 128-CPU hardware benchmark.

The real Chromium walkthrough passes 21 recorded steps with no JavaScript errors. It creates an actual-engine character, enters and resolves a hunt, observes real rewards, submits a two-worker run, downloads matching results and replays 33 recorded inputs to an exact state match. Desktop/mobile screenshots and agent observations are in [verification 003](../../simulation/verification/003/summary.md). The narrow viewport has 390px content width at 390px viewport width. Earlier failed attempts and their corrections are preserved.

## Next measurement work

Before changing game balance, expand and compare legal-action policies for pawn sales, interest, consumables and progression purchases; investigate trajectories and resource ledgers when a policy stalls. Keep game rules in the imported library and use paired seeds to distinguish better decisions from rule changes. When the proposed deck/group/material changes are implemented in that library, both gameplay and this runner inherit them; update intentional engine-contract tests at the same time. Calibrate attendance and action-time inputs against real players before presenting calendar-day curves as a human forecast.

## Boundaries

Shared warden required-party outcomes remain unavailable; the dashboard reports actual library HP/regen/quorum without turning a quorum into an invented victory estimate. Proposed group fights/fixed decks require implementation in the real engine first. Future forecasts should add an isolated worldd service environment and observed player-session calibration. No game balance change or production deployment is made here.
