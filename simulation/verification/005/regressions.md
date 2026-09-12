# Regressions observed during verification

1. Long-run planner could request unavailable close_in with ranged lead / side blade. Recorded in original search 20260912T193841Z-1cedebc9; disqualified, regression test added, fixed in 932aa50.
2. Browser at 1440×1000: saved-run loading failed with `window.history.replaceState is not a function`. Existing global function named history shadows the browser navigation API. Reproduced in the rendered page before correction; rename the function to refreshRuns and rerun walkthrough.

3. A direct #game-quantiles link opened above the charts because results were hidden during initial fragment navigation. Reproduced in the 24-player browser view; scroll to the requested anchor after asynchronous results and reports have loaded.

4. Static review found equal-power inventory choices could inherit set iteration order across spawned processes. Sort owned slugs before tie-breaking; add a cross-process hash-seed regression and repeat both winning validation cohorts to verify the published outcomes remain unchanged.
