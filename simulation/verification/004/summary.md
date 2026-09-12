# Verification 004 — plain-language charts and fastest player

12 September 2026. Local simulator, branch codex/019-chart-language. Plan committed first as a3fe582. No game or simulation calculations changed.

45 existing tests passed in 32.991s. JavaScript syntax check passed. Agent-operated in-app browser verification used actual saved run 20260912T190733Z-fba5d7a7 (24 players, 30 days, seed 1601). The agent visually inspected the narrow browser screenshot and compared plotted point coordinates and visible sentences with saved JSON.

| Scenario | Verdict | Evidence |
|---|---|---|
| Median plus fastest line | PASS | Floor 5: median 28 days, fastest 8.6667 days, player 5 / Mage. Floor 4: median 13.6667, fastest 2 days. Two distinct colored/patterned lines. |
| Average wording | PASS | Floor 5 reads 20.53 days on average, explicitly only the 12 players who reached it. |
| 90% missing result | PASS | Says 90% had not become able to defeat floor-5 monsters within 30 days. |
| Percentage/count units | PASS | Says 50% — 12 of 24 players; hunter count explains the unmeasured warden requirement. |
| Comparison | PASS | Names comparison size, duration and seed; 12-player seed-1602 run has no population median at floor 5, 2/12 reached. |
| Narrow tooltip layout | PASS | Screenshot floor-5-days.png: complete sentences and both times visible inside the viewport, existing VGA font. |

The fastest line is earliest observed per floor and can change player identity. It does not prove an optimal possible speed. The main simulation remains selected after verification. Median/average/P90 values, missing-value rules and underlying game results are unchanged. Full desktop/responsive regression testing belongs to the subsequent optimizer dashboard verification; this pass inspected the current narrow in-app viewport.
