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

## Boundaries

Shared warden required-party outcomes remain unavailable; the dashboard reports actual library HP/regen/quorum without turning a quorum into an invented victory estimate. Proposed group fights/fixed decks require implementation in the real engine first. Future forecasts should add an isolated worldd service environment and observed player-session calibration. No game balance change or production deployment is made here.
