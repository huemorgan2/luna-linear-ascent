# Dojo scenarios for plan 015

These scenarios are written before runtime implementation. They are not executed by this planning task. Every scenario is a separate file with Preconditions, Scenario, Expected behavior, Fail conditions and Verify. The LLM must drive real Luna/web browsers and judge screenshots and cross-system evidence; coded tests complement these walkthroughs.

- [S01: Current-game baseline](dojo/S01-current-baseline.md)
- [S02: Returning players and item identity](dojo/S02-item-conversion.md)
- [S03: First session and first upgrade](dojo/S03-opening-loop.md)
- [S04: Reach, counters and effects](dojo/S04-combat-decisions.md)
- [S05: Create an opening and survive a hit](dojo/S05-movement-shields.md)
- [S06: Forge, inventory and accessibility](dojo/S06-forge-concurrency.md)
- [S07: Sources and grade transitions](dojo/S07-grade-boundaries.md)
- [S08: Unequal loot routes and recovering from losses](dojo/S08-loot-recovery.md)
- [S09: Concurrent wardens and the true finale](dojo/S09-shared-wardens.md)

Before a runtime phase begins, mirror its scenarios into the owning repository's tests/015-weapon-combat-progression/ and register any local runner required by the stack. The first user query is “play linear ascent”; the first feature action is the phase-specific choice in the relevant scenario. Existing unrelated walkthrough coverage remains required when shared infrastructure changes.
