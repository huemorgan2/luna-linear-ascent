# S01 — Current behavior and source baseline

## Preconditions

Phases 1. Pinned pre-redesign game and isolated QA world; fresh and representative higher-floor accounts with finite normal resources. Root/plugin/vendor/client hashes and observed timing settings recorded.

## Scenario

Type “play linear ascent” in Luna; play a normal and deep hunt, inspect School, fill an XP bar, use Shield wall and visit ordinary/milestone keeps. Record floors1/10/31/50/99/100 using declared fixtures where needed. Repeat representative actions on web. Capture a baseline simulator replay on exactly this source.

## Expected behavior

The report distinguishes actual old rules, proposed rules and explicit fixture access. Entry/swing costs, reward timing, XP clipping and shared HP updates are observed with finite resources.

## Fail conditions

Calling a source inspection a live test; refilling energy between boss swings; presenting an old-source replay as new; hidden frontier/resource grants; recording a failed action as a kill.

## Verify

Compare ledger deltas and timestamps to scenes, server state and imported hashes. Record active actions/minutes and request-to-visible-result latency. File pre-existing failures before edits.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
