# Measured legacy game baseline

13 September 2026. Root integration `1f45fb1`; plugin alignment `1f1b661`; vendor0.112.0. Full package comparison found only the published renderer marker dots, eight maps and version ahead of plugin; these were copied to source. No combat, income or player progression rule was retuned.

## Measurements

`python3 simulation/run.py --config simulation/configs/stronger-paths.json` ran24 actual-engine players over30 simulated days using8 workers in48.21 seconds. Run `20260912T210523Z-7932e98d`, deterministic result hash `f8e915439ec1e45494214b9897a4733b76336ca2d074d7c52fcd960436c4847a`. Population median reaches floor3 in2 days, floor4 in4 days. Eleven of24 reach floor5; four reach floor8; no one reaches floor9. This is capability under an explicit world-access fixture, not actual multiplayer unlock time. Missing population medians stay missing.

One complete saved player was replayed:1,452 inputs reproduced state hash `947bfe920c6365eb2b5d424bface7d8b829895028fd36d7058a4c7976de9274b` exactly. Run source hash is `33c2a64cfb9acd9fbbd82b51c2764a76aca02c129086ecf0ae26b41efc58ce91`.

Actual Vault actions with the injected game clock: deposit1,000, one day yields50 collectible gold, collection yields1,050 principal. Repeated look leaves1,050 unchanged. At day2, collection yields1,102 with0.5 carried fractional gold. No simulator investment income was invented.

Finite-energy probes at floors1/10/31/50/99/100 used one initial reference-kit fixture and no per-swing energy/HP restoration. Ordinary entry is free, closing distance is free, each damaging swing costs3. Floor1 gets8 paid swings from25 energy and then refuses without another enemy turn. Floor31 gets9 from28. Floor99 loses the exchange before emptying its bar. Milestone floors10/50/100 spend5 for a pledge and have no live private encounter. Emitted world effects in these local probes were recorded, not settled; these probes do not measure shared victory or party size.

The web retry defect was reproduced against a fresh local PostgreSQL test world. Two `deposit_half` requests carrying the same `scene_id=s0` change1,000 carried gold to250 and bank750. A single accepted action should leave500/500. `webplay.act` ignores the supplied scene ID; worldd checks idempotency before the player lock and keys it by tenant without player identity. Phase2 must enforce stale-scene checks and serialize repeated requests before any currency/energy mutation.

## Verification

| Command | Result |
|---|---|
| `python3 -m unittest discover -s simulation/tests -v` |56 passed;17.710s |
| `python3 worldd/tools/gen_wiki.py --check` | Current |
| `ASCENT_TEST_DATABASE_URL=postgresql://roy@127.0.0.1:5432/ascent_change_tests …/worldd/.venv/bin/python -m pytest tests -q` from `worldd` |224 passed;313.37s |
| `PYTHONPATH=. …/worldd/.venv/bin/python -m pytest tests -q` from plugin before alignment |1,440 passed;10 failed;1 skipped;1 xfailed;20.01s |
| Same plugin suite after published asset alignment |1,440 passed;the same10 failed;1 skipped;1 xfailed;193.38s |
| Map/durability/slot targeted suite after alignment |115 passed;the same two baseline failures;4.33s |

The10 plugin baseline failures are not silently treated as passing. They concern: a victory prose expectation, shoe chase wear, threat XP, exchange ending, two residual class-field reads, quiver consumption, two early kill/XP expectations, and two kill3d banner expectations. Several combat fixtures assume a kill/round without controlling the current resolver and RNG. They will be reconciled against the new explicit contracts when those consumers change, with regression assertions for real outcomes. No new failure appeared from the asset alignment. Real browser results are recorded separately; coded checks alone do not complete phase1.

## Evidence and rollback

`baseline-measurements.json`, `finite-energy-baseline.json`, `stale-action-baseline.json` retain the bounded results. Full raw run stays in the local simulation run directory. Historic0.111.0 results remain untouched. Original workspace dirt stays on `codex/preserved-workspace`.

Before candidate writes, plugin alignment rollback is `git revert 1f1b661`; root integration rollback is `git revert -m 1 1f45fb1`. Test databases are isolated from production and existing QA. No real player state or production service was modified.
