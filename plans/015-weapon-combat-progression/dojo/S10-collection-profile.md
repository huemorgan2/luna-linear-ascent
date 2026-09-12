# S10 — Collection and profile across users/clients

## Preconditions

Phases 2,3,7. PlayerA owns several same-family/grade items; playerB has a different deck; desktop and390px web plus Luna. One account has stored items and private bank data.

## Scenario

Open A profile→collection; filter grades and paths, replace each battle cell, inspect source/ability/cost by tap and keyboard, then view B. Start a group as A, act as B elsewhere, return/reconnect A and try a stale edit.

## Expected behavior

Three cells remain visible without School locks; frame shapes and art distinguish grades; accessible details and selected instances agree in all clients. Stored items obey retrieval rules. B does not inherit A actions/data; active A deck stays locked.

## Fail conditions

Cross-user state leak, hidden fourth slot, hover-only costs, different UI and text-selected weapon, obscured mobile Escape, identical rarity drawing, mixed font sizes or dropdowns for the four grades.

## Verify

Inspect scene payloads, public versus private fields, selected/committed IDs and all item locations. Capture collection/profile/preview/battle at desktop and390px with readable icons and16px game font.

The LLM tester walks the real browser, reads the DOM and screenshots, and records PASS/FAIL with evidence. Coded checks complement this walkthrough. Record date, root/plugin/client SHAs, environment, accounts/fixtures, timings, screenshots and regressions in a numbered results folder; file failures before fixing and rerun the affected scenario. This scenario is planned, not executed by the current documentation revision.
