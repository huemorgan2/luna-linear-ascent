# Simulator verification — 001

12 September 2026. macOS ARM64; Python 3.9.6. Local simulator server on port 8766. No production data or game endpoints changed.

## Source and execution

- Phase 1: `3352c35`; phase 2: `8ab97f9`. Phase 3 implementation commit is recorded in its PLAN.md after this report is committed.
- Pinned release: game 0.112.0 / wiki 089.3, source `1897edd615682c6a960101adaa5299b986f681df`.
- Input SHA256: `8d948158ece17a8939789243d45bbca567eb552400c4d667bc612e53c9a36341`.
- Browser baselines and comparison use identical code SHA256: `4824851925684539997bb49ecd480a08d0aa3cb86f3f7b9349fb66fba07696d7`.

## Coded verification

`python3 -m unittest discover -s simulation/tests -v`: **20 tests PASS**, 3.186 seconds. Includes automatic CPU detection dispatch, serial/parallel seeded identity, 128-worker Windows sharding dispatch (mocked, not an on-device run), HTTP creation with spawned workers, busy/failure handling, input rejection, persisted history/download, resource conservation, censoring and combat contracts. The complete standalone simulator suite ran; unrelated worldd/plugin suites were not part of this change.

`python3 simulation/export_inputs.py --check`: **PASS** — 100 floors, 425 species, 16 families, 84 upgrade states; exact pinned input hash. `python3 -m compileall -q simulation` and `git diff --check`: **PASS**.

## CPU benchmark

Same 24 players, 120 days, seed 1601, all 100 floors, three warden trials per candidate party. Wall time includes player progression, warden analysis and aggregation. Separate runs on this shared 8-CPU machine; this is a single comparison, not a controlled multi-machine benchmark.

| Mode | Seconds | Run |
|---|---:|---|
| Serial, one CPU | 45.5661 | `20260912T170830Z-50622b48` |
| Automatic, eight CPUs | 16.7289 | `20260912T171013Z-e2e2bb42` |

**2.724× speedup**. Every player, floor and warden result matched exactly, as did the semantic SHA256 `29b42d540901ef7d8f4222c2add8a185ce67c542be86ed4fd4f4d66db90a2c05`. Earlier four-process execution with serial warden work took 21.0438 seconds versus 33.7722 seconds serial (1.605×). Hardware load/startup affect timings; speedup is not promised to scale linearly.

## Browser walkthrough

The first user action in the in-app browser was **Run simulation**, with the visible 24-player, 120-day, 100-floor settings. It used 8 CPUs, saved `20260912T171623Z-b5e298bf` in 11.6704 seconds and loaded the result. Then **Use this run's settings**, expand model settings, change only group enemy HP to 0.5, and **Run simulation**: `20260912T171714Z-140fca47`, 4.1276 seconds. Both runs remain local in `simulation/runs/` (Git-ignored user artifacts).

Additional real Chromium interactions and screenshots are reproducible with `verification/walkthrough.mjs` (Playwright is needed only for development QA). The agent inspected the screenshots as well as the DOM/JSON observations; software assertions alone are not the visual verdict.

| Scenario | Verdict | Evidence |
|---|---|---|
| First run, progress, saved result | PASS | In-app browser Run action; 8-CPU progress and saved run ID verified through API and visible page |
| Floor / strategy / graph hover | PASS | Floor 6 tacticians: 4/4 reached, mean 56 days; tooltip agrees with saved JSON. [Screenshot](02-tooltip.png) |
| Run comparison and focused axes | PASS | One setting difference only: enemy HP 0.5 versus 1. [Full charts](03-charts.png), [focused charts](07-focused-charts.png) |
| Unreached floor and boss qualification | PASS | Floor 100: 0/24 reached, no observed peer estimate, null mean; 53-reference-peer estimate explicitly fails hunting readiness. [Screenshot](04-unreached-floor.png) |
| Switch / restore / download | PASS | Downloaded baseline semantic hash matches its file after switching runs twice |
| Invalid input | PASS | Zero players refused visibly by native validation; saved-run count unchanged |
| Desktop / narrow layout | PASS | 1440×1080 and 390×844; no horizontal body overflow, four charts readable, IBM VGA loaded. [Desktop](01-desktop.png), [mobile](05-mobile-top.png), [mobile chart](06-mobile-chart.png) |
| Browser errors | PASS | No page errors; observations in [browser-observations.json](browser-observations.json) |

## What the initial experiment says

| Strategy | Baseline median final ready floor | Half-HP median final ready floor |
|---|---:|---:|
| Learner | 8.0 | 9.0 |
| Tactician | 6.0 | 6.0 |
| Material hunter | 6.0 | 6.0 |
| Saver | 6.0 | 9.0 |
| Rusher | 3.0 | 3.0 |
| Specialist | 5.5 | 6.0 |

Overall median remains floor 6; the maximum rises from 9 to 11. No player reaches floor 100. These 24 actors (four per policy) are an exploratory sample, not a population estimate. The baseline records 29,478 gold-blocked investment checks and 3,839 all-weapons-broken checks. They are check counts, not unique players or days. Inspect upkeep, survival and acquisition assumptions before attributing the stall to a specific live-game feature.

The mean preparation time for baseline tacticians to floor 6 is 56 days under the explicit calendar assumptions. That is not a forecast for live players. Read [MODEL.md](../../MODEL.md) for the derived defensive/repair economy, finite readiness probes, open-floor assumption and omitted School/race/quest/trade mechanics.

## Regressions and limits

- No unresolved browser or coded failures.
- During visual inspection, the full 100-floor view compressed the early progression into a narrow strip. Added **Focus reached floors**, verified it changes only the graph axis and preserves the all-floor results.
- Mean among reached can fall at a later floor because slower players are censored; coverage and population quantiles remain available beside it. Population quantiles use nearest rank and reached-only quantiles interpolate.
- Warden reference gear can fail ordinary hunts. The UI labels this and does not claim those reference peers are qualified players.
- Real execution tested on macOS with 1, 2, 3 and 8 workers. No physical many-core Linux/Windows benchmark was available here.
- Long runs store player histories in memory before writing their final atomic run file; memory and serial aggregation limit scaling. No mid-run resume/checkpoint is implemented.

## Rollback and operations

The local server is a standalone process (`python3 simulation/serve.py --port 8766`). Stop with Ctrl-C; an active simulation finishes saving before server exit. Revert phase commits in reverse order as recorded in the plan. Saved run files remain intact. No production deployment or database rollback is involved.
