# Linear Ascent simulation lab

Run from the game repository on any computer with **Python 3.9 or newer**. No pip installation, game server, database, credentials, LLM or internet connection is needed. The rules snapshot, engine, website and font are all in this folder.

```bash
python3 simulation/serve.py
```

Open **http://127.0.0.1:8766**. Click **Run simulation**. The program automatically detects available CPUs and distributes both players and warden floors across them. Each completed run is saved separately in `simulation/runs/`. Files remain after the server closes; they are intentionally ignored by Git. Copy that folder between computers to inspect their runs in the same website.

For a headless run using all available CPUs:

```bash
python3 simulation/run.py --players 600 --days 365 --seed 1601
```

The default `--workers 0` means automatic. For diagnosis or a deliberate limit, use `--workers 1` (serial) or e.g. `--workers 16`. Automatic detection respects Linux CPU affinity. At most one process per independent task is useful; a tiny run may be faster serially. Progress reports completed players and warden floors. Start with the website's 24-player/120-day study before increasing swarm size and horizon. More players sample chance more thoroughly; more days test later progression. Neither changes the game's rules.

The simulator is a script, so launch it through the supplied CLI or server rather than an unguarded interactive Python cell. Spawned processes work with these entry points. On Windows, use `python` instead of `python3`; the program automatically splits large worker counts across pools to respect Python's 61-worker limit per Windows pool. The actual execution tests were run on macOS; the Windows sharding path has a coded dispatch check, not an on-device benchmark.

## Compare a design change

Use **Use this run's settings**, change one setting, and run again with the same seed and policy list. Select the earlier run under **Compare against**. For example, lower *Group enemy HP ×* to test full-sized enemies in a sequence, or change *Full repair cost share* to test upkeep pressure. These are experiments, not silent changes to the baseline.

The graphs show:

- Calendar days to hunting readiness: reached-player mean and full-population median/P90.
- Fraction ready at each floor; missing late-floor results remain missing.
- Actual hunt wins versus fresh reference-equipment normal-group probes.
- Whole-swarm qualified hunters versus required peers against healing wardens, plus a separate reference-equipment benchmark. Reference gear may fail normal hunting; floor details explicitly identify this.
- Per-floor policy results, resource pressure and individual final decks.

Use **Focus reached floors** to inspect early progression without compressing it against the full 100-floor axis. **Full tower** restores the complete view, including unreached floors. Warden demand always uses the whole swarm; strategy filters apply to personal progression, hunt outcomes and resources.

Readiness requires seven wins from eight fixed probes by default. Current condition/ammo and owned equipment are retained; health/energy are restored only on disposable probe copies. It is a finite estimate of capability. Reaching a floor once does not establish that a player can afford to hunt it indefinitely. A player's milestone snapshot is not their final-day loadout.

Mean days **among those who succeeded** is not the average completion time of all players. Censored players remain in coverage and horizon-restricted statistics. Open-floor access excludes time waiting for other people to unlock the tower. The complete assumptions and omissions are in [MODEL.md](MODEL.md). Read that before treating a curve as a prediction of live player behavior.

## Saved settings and replay

Each JSON contains full config, provenance/code/input hashes, execution hardware, six heuristic definitions, individual histories, floor aggregates and boss trials. To replay a run:

```bash
python3 -c 'import json; from pathlib import Path; r=json.loads(Path("simulation/runs/YOUR-RUN.json").read_text()); Path("simulation/replay.json").write_text(json.dumps(r["config"]))'
python3 simulation/run.py --config simulation/replay.json
```

Or write a partial config; unspecified settings use model defaults:

```json
{"players":600,"days":365,"seed":1601,"group_hp_scale":0.5,"policies":["learner","tactician","farmer","saver","rusher","specialist"]}
```

Same inputs/code/config/seed produce identical result hashes across CPU counts. Worker count, runtime and timestamps are excluded from that digest. Cross-Python/architecture floating-point identity is not promised; provenance makes differences inspectable. Keep model code fixed during a run; a source change causes an explicit refusal to save mixed-code results. Keep one CLI run active per available CPU allocation to avoid oversubscription.

`--output-dir` on the CLI and `--runs-dir` on the server select another results folder. The website accepts one background job at a time. Ctrl-C closes the website and lets an active simulation finish saving before exit. Invalid settings and worker failures are reported without destroying older runs.

## Verification

```bash
python3 -m unittest discover -s simulation/tests -v
python3 simulation/export_inputs.py --check
```

Tests cover seeded replay across CPU counts, resource conservation, censoring, energy charged on enemy entry, partial-haul loss with retained XP, shield leakage, status timing, finite-resource healing wardens and the real HTTP run lifecycle. A separate browser walkthrough records UI evidence under `simulation/verification/001/`.

Source inputs are pinned to game 0.112.0 / wiki 089.3. Re-exporting is an explicit operation with `python3 simulation/export_inputs.py --source /path/to/released-checkout`; a normal run never imports a different live ruleset. This folder does not change production gameplay.
