# Actual engine play and result inspection

## Preconditions
Local simulator server; actual-engine test suite passes; a saved actual-engine cohort exists. No production credentials or documents.

## Scenario
Open the default dashboard. Confirm actual imported engine path/hash and mechanics limitations. Open the inspector, create a synthetic character through real options, enter floor 1, start a hunt and make combat choices until a verdict. Observe engine-generated meters/options/refusals. Run a small cohort through the UI, inspect a floor, download its JSON and open a recorded player's action trace. Open historical proposals and confirm they are separately labeled. Repeat layout inspection at 390px.

## Expected behavior
The UI reports actual core actions, costs, RNG and results; no copied or proposal combat layer. Saved graphs agree with JSON. Unreached floors and unsupported multiplayer demands have no fabricated values.

## Fail conditions
A current-engine run claims proposed groups/fixed slots; damage/rewards bypass core; time leaks between players; stale-source replay passes; historical data is relabeled as actual; browser errors or horizontal page overflow.

## Verify
Exact-state replay checks, immutable downloaded hash, server run status, source manifest, browser screenshots and qualitative action-flow observations. This is local actual-engine play, not a production/Luna deployment test.
