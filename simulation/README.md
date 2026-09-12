# Linear Ascent / actual-engine simulation

The default runner executes the **actual game library**, through the same `core.apply_choice` entry point used by worldd. Bots choose actions; the game calculates the outcomes. It needs no UI, LLM, game account or database for personal play.

From the same repository on any computer:

```bash
python3 -m pip install -r simulation/requirements.txt
python3 simulation/serve.py
```

Open [the local dashboard](http://127.0.0.1:8766). It runs on all available CPUs automatically, saves each actual-engine run in `simulation/game-runs/`, graphs readiness/difficulty and lets you inspect/replay real game actions. **Create synthetic player** opens an interactive inspector using the same engine adapter as the bots.

For a headless cohort:

```bash
python3 simulation/run.py --players 120 --days 120
```

`--workers 0` (default) uses all available CPUs up to the number of players. `--workers 1` forces serial execution; a positive value sets a limit. Spawned processes work on macOS, Linux and Windows. Linux affinity is honored; large Windows worker counts are split across pools. More CPUs do not guarantee linear speedup, especially for small cohorts.

Every run records the exact imported package path/version, source/content hashes, runner hash, settings, policy definitions, player documents and measured outcomes. Source changes during a run are rejected. Saved runs are ignored by Git; copy `simulation/game-runs/` to carry them between computers. The game code itself stays in this same repository and is resolved exactly as worldd resolves it. `ASCENT_GAME_PATH` can select another game package using the existing gamepath mechanism; start a fresh process after changing source.

## What the curves mean

This runs the checked-out game's **current personal rules**. Proposed features do not appear until implemented in that game library. Clock, attendance and bot decisions are synthetic. Default staged world access excludes shared unlock waiting; a positive `--world-frontier N` instead holds the open world at floor N. Full details are in [GAME-ENGINE.md](GAME-ENGINE.md).

Readiness uses disposable real-engine hunt probes with owned condition/training/gear and restored HP/energy. Probes cannot grant resources. Population median/P90 remain missing until enough players arrive; the reached-only mean is conditional on success. These experimental bots do not establish human enjoyment or real demographic averages.

Shared warden victories require worldd's multiplayer database services. The page displays actual library parameters and qualified hunters, but **does not manufacture required-party counts**. Those remain unavailable until the shared service is included in the headless environment.

For a repeated cohort on three seeds (each run uses all available CPUs):

```bash
python3 simulation/game_study.py --players 12 --days 30 --seeds 1601,1602,1603
```

## Search for stronger player paths

```bash
python3 simulation/game_search.py
```

This tests 18 planner choices (sword/bow/magic focus, levels/training first, three farming margins), then validates the top three on different seeds. All available CPUs run independent trials, with no nested worker pools. Every trial is an ordinary saved actual-engine run. The search report is saved progressively in `simulation/game-searches/`; failures and invalid decisions are visible. The default screening uses 3 players × 7 days × 2 seeds per path; validation uses 6 players × 30 days × 3 fresh seeds per finalist and baseline. Override these with `--screen-players`, `--screen-days`, `--validation-players`, `--validation-days`, `--training-seeds`, `--validation-seeds`, `--finalists`, and `--workers`.

The winner is selected using the whole training population, including unfinished players: highest mean qualified floor, then the accumulated time qualified for each floor. Validation never changes that selection. The historical Mage, corrected Mage and corrected Learner provide matched comparison arms. A bounded search can find better methods; it cannot prove the fastest possible path. Different seeds and a larger cohort are needed before trusting small differences.

The dashboard’s **Stronger player paths** section opens matched strategy graphs and can apply the winning planner settings to the next swarm. Its cyan line shows when half the players can defeat each floor’s monsters; purple shows the earliest observed player, with identity in the tooltip. Saved searches and runs are ignored by Git: copy both directories to inspect those results on another computer, or rerun the commands there.

## Replay and inspect

The first six players retain complete action/time/world-input traces by default (`--trace-players N` changes this). Verify a player by replaying those inputs through the actual engine:

```bash
python3 simulation/run.py --replay simulation/game-runs/YOUR-RUN.json --player 0
```

The verification compares the complete document, scene and RNG counter. It refuses a different source revision. The same action is available on the website. Other players retain final state, daily summaries and recent actions; increase trace coverage for an investigation.

Use **Use these settings** and keep the same seed to compare activity assumptions or policies. Game balance changes belong in the game library; the actual-engine UI has no duplicate damage, repair-price or drop-rate knobs. JSON configs accept the fields in `GameConfig`; proposal-only knobs are rejected.

## Historical proposals

The earlier separate proposal simulator and saved data remain under [Historical proposal runs](http://127.0.0.1:8766/proposal). It is not the actual game. Its original CLI is now:

```bash
python3 simulation/proposal_run.py --players 24 --days 120
```

Its results remain in `simulation/runs/`, exploratory matrices in `simulation/studies/`, and assumptions in [MODEL.md](MODEL.md). They are not relabeled as actual-engine measurements. Plan 017's matrix was stopped when the user clarified the engine-reuse requirement.

## Verification

```bash
python3 -m unittest discover -s simulation/tests -v
```

Actual-engine tests check direct-core parity, costs, regeneration, deterministic CPU results, immutable probes, source guards and HTTP replay. Browser evidence is under `simulation/verification/003/`. The game loader currently emits pre-existing unclosed-YAML ResourceWarnings; the simulator does not modify that loader.
