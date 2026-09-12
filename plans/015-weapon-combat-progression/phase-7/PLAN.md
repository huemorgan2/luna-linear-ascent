# Phase 7 — Full playtesting and migration rehearsal

## Goal

Validate that the complete game is understandable and recoverable through actual player interfaces, including returning saves and concurrent play. Numbers passing alone do not complete this phase.

## Steps

1. Run the full plugin and worldd test suites, local/HTTP contracts, content lint and client builds against the same pinned candidate.
2. Conduct real multi-turn Luna conversations and web/mobile walkthroughs for fresh, mid-game and late-game players. Include a player following ordinary advice and one deliberately choosing efficient routes.
3. Execute all dojo scenarios, including plain-text options, stale cards, dual tabs, deaths, repairs, grade transitions, deep hunts and shared wardens. Read screenshots, deltas, server events and receipts.
4. Rehearse conversion on preserved representative saves and a sanitized snapshot where available. Run it twice, exercise post-conversion transactions, then rehearse rollback without losing new progress.
5. Invite a small QA player pilot when available; record whether players can explain the counter, choose a useful upgrade, find missing materials and recover after losing. Do not treat a mathematically legal flow as proof it is enjoyable.
6. Re-run whole-account comparisons after boss tuning, since raid energy, consumables, deaths and rewards alter hunting/upgrade pace. Fix regressions and repeat only affected checks plus required release suites.

## Verification

The LLM drives and judges the browser scenarios; coded tests cannot replace them. Record a numbered dojo/results folder with SHAs/environment, per-scenario PASS/FAIL, screenshots, measured outcomes and regressions. Require every launch gate in the parent plan to pass or be deliberately revised with evidence before release. Do not report gameplay complete while a required real multi-player scenario is pending.

## Rollback

Reset only disposable QA fixtures from their preserved baseline; retain failure evidence. Revert the responsible implementation phase and replay its dependent scenarios. No production rollout occurs in this phase.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
