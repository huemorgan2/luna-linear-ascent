# Read days needed to defeat floor-5 monsters

## Preconditions

Local simulator on port 8766, completed actual-engine runs available. Preserve the user's current run selection and any active simulation. Read that run's saved floor values before judging labels.

## Scenario

Open the days chart and point to floor 5. Read the complete sentence. Switch between half the players, average among those who reached the floor, and 90% of players. Inspect an unreached floor, then the percentage and hunter-count charts. Enable a second saved simulation and identify each value. Repeat the interaction in a narrow viewport. Refresh the user's page to show the delivered wording.

## Expected behavior

The user can answer: which floor, how many days since starting, which players, and how many qualified within the simulation duration. Percentages and counts name what they measure. Missing values explain the unmet threshold. Text fits and uses the existing game font.

## Fail conditions

`Selected run: 28`, a bare number without units, an average described as a population median, a missing result rendered as zero, invented data, unreadable or clipped tooltips, or lost ability to inspect a floor.

## Verify

Compare saved JSON with visible sentences. Read screenshots and browser text, record PASS/FAIL and exact run IDs under `simulation/verification/004/`. Preserve game and simulator calculations unchanged.
