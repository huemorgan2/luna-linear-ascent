# 085 — standard maps and opaque lift browser scenarios

## Preconditions

Local worldd is healthy with the current vendored plugin; QA Luna has the same plugin reloaded. Use disposable QA accounts, one with no Labs flags and one with a legacy false/true floormap flag, with floors 1–11 accessible. Record starting state/version. Desktop viewport approximately 1280×900; phone viewport approximately 390×844. Never mutate a real player's progression for tests.

First likely user query, recorded before browser entry: **show me floor 2**. Follow it in a real Luna conversation with the bare printed number for GATE.

## Scenario

1. Open Labs: only remaining experiments appear; no Floor maps toggle. Visit floor 1 without opt-in; inspect the preserved map and all labels.
2. Visit floors 2–10, completing arrival beats where present. Inspect each full map and its exact setting, scale, shading, labels and costs. Hover and keyboard-focus every marker: the correct short description appears immediately. Record screenshots and DOM after meaningful actions.
3. For each floor, press its printed GATE number; return and click CAMP, verifying NPC dialogue remains navigable; return and exercise the keep marker. On floor 10 verify GNARL reaches the milestone keep. Verify hunt/deep-hunt costs match existing rules on representative early/deep floors.
4. Visit floor 11: the existing menu remains usable. Change legacy map flags on the disposable fixture and confirm floors 1–10 look/behave identically.
5. Repeat map inspection at phone width. Read every chip; confirm no overlap or off-screen chip/tooltip, no horizontal page overflow, and successful direct touch action. Check typing in text inputs is not intercepted by number shortcuts.
6. Ride up, down and back to Roothollow. Observe the first painted frame and mid-ride: the entire viewport background is solid black outside the elevator ink. Try pointer/number input during the ride; hidden destination must not act. At the end, destination appears and inputs work. Repeat a ride and verify the GIF restarts.
7. Reload, peek/resync and attempt refused travel: no unwanted elevator. Check console/network for errors and missing assets.
8. In QA Luna, send “show me floor 2”, then the displayed GATE number, then “show me the scene”. Observe a real tool-backed conversation, matching cards, correct navigation and no read-side mutation. Check another player/consumer sees standard maps too.

## Expected behavior

Ten distinct district-scale maps, unchanged floor-1 image, tiny human-scale details around enormous landmarks, readable designed gradients. Same numbered chip vocabulary as floor 1. Instant descriptions on hover/focus; keyboard and touch usable. Full black elevator until the final reveal. Navigation and costs are unchanged and applied once.

## Fail conditions

Missing/incorrect map, opt-in still required, map on floor 11 without an asset, dead or clipped/overlapping chip, delayed/off-screen description, wrong number routing, milestone labeled KING, inaccessible conditional action, destination flash/show-through, hidden action during ride, stuck overlay/input, GIF replay on read/reload, raw JSON or agent-invented state, asset 404 or new console error.

## Verify

Record each floor's loaded image dimensions/URL, map markers and option IDs/numbers, tooltip computed visibility immediately after hover/focus, and layout bounds at both viewport sizes. For the lift record computed full-overlay background/opacity, screenshots during ride and restored input afterwards. Cross-check navigation and hunt energy delta in QA player state/ledger. Save observed pass/fail and screenshot descriptions under the numbered dojo result folder.
