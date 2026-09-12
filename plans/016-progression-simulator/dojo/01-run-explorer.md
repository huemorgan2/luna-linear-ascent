# Run explorer walkthrough

## Preconditions

The local simulator server is running on port 8766. At least one saved run exists. No production credentials or LLM are required by the simulator. Record the current implementation commit and environment.

## Scenario

1. Open `http://127.0.0.1:8766`. The user's first action is **Run simulation** with a small swarm.
2. Observe progress and completion, then inspect the new saved run and its input settings.
3. Select a policy and a floor; read the days-to-readiness, reach fraction, difficulty and boss panel. Hover a graph point and verify its text against that floor's saved JSON.
4. Choose a late floor with no qualified players, if present. Inspect its missing values and reference-versus-observed boss distinction.
5. Switch to another run, enable a comparison and return to the first run. Download its data.
6. Enter an invalid setting and check the refusal. Inspect the page at a narrow window width.

## Expected behavior

Graphs and numbers match the selected saved run. Loading/running state is visible. Floor and policy filters update consistently. Unreached floors read as unreached, with their fraction visible; they never become zero-day successes. Reference boss estimates are distinct from actual qualified-player observations. The UI remains legible and usable at narrow widths.

## Fail conditions

Frozen progress, stale graphs, mismatched run data, clipped controls, an empty error screen, a fabricated late-floor average, an unlabeled approximate rule, or a supposedly finite-energy boss calculation that silently replenishes players.

## Verify

Inspect the persisted run file and manifest, compare displayed figures to JSON, capture wide/narrow screenshots, record per-step PASS/FAIL and any regressions. Rerunning identical seed/settings must retain identical simulation outputs after excluding run metadata such as timestamps and runtime.
