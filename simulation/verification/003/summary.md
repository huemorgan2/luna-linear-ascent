# Verification 003 — actual game-engine runner

Date: 12 September 2026. Branch: `codex/018-headless-game-engine`. Plan: 252afec; adapter: 667f237; swarm/explorer: 8935fb8; recovery policy: 45b97a5. The final UI/evidence revision is the commit containing this file. Environment: local macOS, Python 3.9.6, real Chromium via Playwright, synthetic player documents, `http://127.0.0.1:8766`. This is not a production deployment or live Luna-conversation test.

Imported engine 0.111.0: SHA256 `3217d52ec623a7b41376921310173bf681573edbe6c9e9d730fccc6a7ae29dae`, loaded through the world's gamepath resolver from `worldd/vendor/plugin_linear_ascent`. No engine rules changed.

## Verdicts

| Scenario | Verdict | Evidence |
|---|---|---|
| Direct core/document/scene/RNG parity and costs | PASS | Adapter tests, actual hunt energy and XP-gated repairs |
| CPU independence, replay, isolated clocks and probes | PASS | Serial/two-worker semantic equality; full-state replay; non-mutation tests |
| Large CPU dispatch | PASS (dispatch only) | Mocked 128-worker Windows pools: 61 + 61 + 6, every logical player once |
| HTTP job/download/replay and inspector isolation | PASS | API tests plus browser-created two-worker run |
| Real-browser actual-engine hunt | PASS | Grey wolf art/stats, movement, attacks, victory receipt |
| Saved results, censoring and multiplayer scope | PASS | Floor 10 shows 0/2 ready, missing day estimates and unmeasured party requirement |
| Browser full-state replay/download | PASS | 33 inputs reproduce document/scene/RNG; downloaded semantic digest matches |
| Desktop/mobile rendering | PASS | Agent-inspected screenshots; VGA font; 390px viewport and 390px document |
| Historical proposal distinction | PASS | Separate `/proposal` disclosure names the independent resolver |
| Shared-world/production behavior | NOT TESTED | No database-backed multiplayer environment used |

Full simulator command: `PYTHONWARNINGS=ignore::ResourceWarning python3 -m unittest discover -s simulation/tests -q`. Result: **45 tests, 10.059 seconds, OK**. The warning filter covers existing game-loader resource warnings; it does not suppress test failures.

Browser command: set `PLAYWRIGHT_PATH` to the installed Playwright `index.mjs`, then run `node simulation/verification/game-walkthrough.mjs` against the local simulator. Final result: **21 recorded steps, PASS, zero JavaScript errors**. [Raw observations](browser-observations.json) include receipts and run IDs. [Regressions](regressions.md) describe earlier failures, their causes and the verified corrections; evidence remains in `attempt-1` through `attempt-4`.

## Agent observations

The monster view displays the actual Grey wolf artwork and 18 HP, 6 ATK, 3 DEF and speed 5. Its game options include movement, attacks and a visibly locked rank-gated Shield Wall. The completed fight leaves 72/80 HP, 23/25 energy, 63 gold and 2 XP; the receipt reports +13 gold and +2 XP and offers the real next actions. Story transitions omit unavailable meters instead of retaining stale values. Mobile provenance wraps without overflow, and fractional day-axis labels remain distinct.

Screenshots: [dashboard](01-engine-dashboard.png), [monster](02-actual-monster.png), [verdict](03-engine-verdict.png), [charts](04-actual-charts.png), [mobile source](05-mobile-source.png), [mobile chart](06-mobile-chart.png).

Browser-created run: `20260912T183125Z-dfef8ead` (two players, one day, two workers). Replay state SHA256: `29bb0f51476623f37487ceae8a7d64cca57795b0405075bc5b798dba0d04dc50`.

The repeated-cohort study and interpretation are in [ENGINE-RESULTS.md](../../../research/simulation-audit/ENGINE-RESULTS.md). Game-engine authority is verified for local personal actions; heuristic choices, synthetic time/world access and sampling remain experimental inputs. Required shared-warden party sizes are unavailable, and proposed group/deck mechanics are not silently inserted.
