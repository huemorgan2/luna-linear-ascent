# Quiver readiness probe correction

13 September 2026, before execution. Candidate engine8b26030/0.115.0.

## Evidence and root cause

The opening eight-player ten-day run aborted with `Probe hunt refused: That isn't one of the paths`. Reproduced by creating a candidate character through the ordinary engine, choosing `forge`, then `quiver_shop`, then calling `assess`. The disposable readiness clone changes location to the floor camp but retains `quiver_view`; the game therefore correctly renders the arrow rack and refuses `hunt`. This is simulator setup, not a combat refusal to bypass in the live game.

The probe signature already retains exact quiver supplies and weapon condition, but omits selected arrows. Replenishment emits the new `arrows` ledger kind, which is absent from immediate improvement checks. A legal arrow purchase should be eligible for a new capability measurement at its actual time. No emergency mitigation or production change.

## Steps

1. Clear quiver presentation state on the disposable probe together with the other presentation flags. Keep owned supplies and selected arrows; never replenish ammo or repair weapons in the probe.
2. Include arrow selection in the combat signature and arrow replenishment in immediate improvement checks. Preserve the existing source-pinned rules, deterministic seeds and whole-group success criterion.
3. Add regressions: camp/rack assessments agree with identical supplies; neither changes the owned document; a legal replenishment triggers a check and current arrow choice participates in the signature.
4. Run focused and full simulator tests, then rerun the failed opening configuration. Retain the failure record; record the new source hash and measured results without changing old runs.

## Verification

`ASCENT_GAME_PATH=$PWD/plugin-linear-ascent /Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/.venv/bin/python -m pytest simulation/tests/test_game_collection.py simulation/tests/test_game_planner.py -q`

Then the full `simulation/tests` suite and `python -m simulation.run --config simulation/configs/collection-opening-smoke.json --quiet` with the same interpreter/environment.

## Rollback

Revert the implementation commit's changes to `simulation/game_agents.py` and its regressions. Retain all run evidence and engine readers. This changes no persisted live-player state. The current failed run produced no result artifact; its traceback is `/private/tmp/ascent-phase4-opening-run.txt`.

## Execution status

Reproduced; implementation pending.
