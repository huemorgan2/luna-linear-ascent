# Phase 3 — Complete opening and first-ten-floor loop

## Goal

Deliver the first reviewable playable slice: profile → collection → group opening → sequential combat → per-kill XP / final haul → Forge / recovery, using real engine actions in web and Luna on floors 1–10.

## Steps

1. Implement authored starter blade/bow/staff access and two-enemy Common opening groups. Teach reach before mandatory flyers, then affinity and one control/status interaction. No School slot fee or rare-drop dependency.
2. Implement the full waiting/active/defeated group loop with a committed three-instance deck. The first valid action against each member charges one energy or latches exhaustion; normal/deep groups have no additional entry fee. Show the next enemy without charging it or requiring Continue.
3. Implement pending haul, once-only kill XP/reserve, full-clear settlement, retreat/death/rescue/overflow claims and provisional objective credits. Include all side paths that could cash out unfinished-group rewards.
4. Implement the minimal coherent combat rules: independent reach/affinity, explicit Air Power exception, four gaps, partial shield protection/wear, one lasting effect and one push/control option. Carry HP, condition, cooldowns and supplies between enemies.
5. Implement profile/collection/preview/battle/results screens through shared Scene/render/pane/tool contracts, following `PLAYER-EXPERIENCE.md`. Numbered replies, clicks, tap and keyboard use the same actions and instance IDs. Show actual paid-versus-exhausted state. Add per-hit resistance feedback from authoritative events: the Power shield or distinct Magic shield rises in pixels above the defender beside actual HP damage, with matching log text and a static reduced-motion alternative. Do not infer resistance from low damage alone.
6. Connect real material rolls, dedicated material storage, +1 Forge upgrade, source condition, repair and zero-gold recovery. The outside card links to the Forge; transaction validation stays there.
7. Adapt the existing headless policy to complete this exact slice. Test under an explicitly recorded QA frontier fixture so phase 3 does not claim multiplayer unlocks are implemented. Do not grant player gold/XP/energy to rescue the test. Verify the working slice before expanding it.

## Verification

Target tests cover group transitions, energy receipts, settlement and effect carry-over, followed by full relevant suites. Run S03/S04/S05/S06/S08/S10/S11 in web and multi-turn Luna, including 390px mobile. Five enemies/two energy must spend two total and exhaust only members 3–5; five energy/retreat after two must leave three. A zero-energy legal kill keeps XP. Retry final kill, reconnect during a waiting member, fill the XP bar, cross dawn and use a full pack. Record real start/end ledgers, actions and time for opening → upgrade → next hunt. Fail on a required fourth weapon, free wave heal or duplicate payout.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Stop new candidate hunt entry in QA. Drain or settle active groups once and preserve their receipts/claims. Revert phase-3 presentation/combat changes, retaining the phase-2 state reader and compensation tools needed to read earned items. The old personal rules stay available only for pinned legacy fights. No partial phase-3 production release.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

Essential opening/group/Forge/gathering gate verified on0.114.5. Rewritten for the three-weapon/group design on12 September2026; authorized for implementation by the subsequent user request. Broader content and integration findings remain assigned to their later gates; this is not a complete release claim.

### Execution start —13 September2026

Phase2's essential state/collection browser gate passed on0.113.5. Implementation now follows `ENGINE-CONTRACT.md`, committed before runtime edits. Preserve the baseline legacy failure list and source-pin new group tests separately; phase3 must supply actual-engine group progression evidence, not reinterpret prior single-enemy runs.

### Candidate checkpoint —0.114.0 / plugin18a3956

The actual engine now resolves sequential groups and per-enemy energy, XP/pending haul, owned-weapon Forge work, paid repairs/practice recovery, Drowned Copse/Bog-Iron Field expeditions, and shared pixel battle/collection/catalog cards. Candidate source and vendor match. QA was restarted with its existing databases and earned players preserved; `/health` reports0.114.0. Production is unchanged.

Verification so far:39 focused engine/style checks passed;8 HTTP action checks passed;4 local PostgreSQL checks passed. The server-wide suite passed232 tests in409.89s. The plugin follow-up passed1480 tests with8 previously recorded legacy failures,4 skips and1 expected failure in114.69s. No newly attributed engine regression remains in that suite. The simulator initially passed60 tests; additional full-group accounting and automatic-CPU/replay tests passed (12 focused accounting/swarm and6 candidate checks); its final full follow-up is running.

The real browser/Luna gate is in progress under `/private/tmp/ascent-phase3-browser/001-phase3`; its first query is `hunt a monster group`. It has no final verdict yet. See `MEASUREMENTS.md` for provisional runs; no100-floor balance or shared-warden claim follows from this checkpoint.

Rollback: before any candidate writes, `git -C plugin-linear-ascent revert 18a3956` reverses the plugin implementation. **Candidate QA writes now exist**, so do not run that inverse against the progressed database. Stop only the two owned QA processes listed in `/private/tmp/ascent-change-qa/pids.json`, keep their databases and current collection/group/expedition readers, and fix forward or implement a receipt-preserving compensation first. No restored snapshot may overwrite earned state. The concrete launcher/PID procedure and its pre-execution rollback are in `/private/tmp/ascent-change-qa/ROLLBACK.md`.

### Browser and natural upgrade gate —0.114.5

Main reviewed the actual browser evidence and390px mobile pass in `dojo/results/0066-015-groups-and-gathering-2026-09-13`. The natural Luna character earned its money, paid35gold for an axe and45 for a pick, secured6Wood/2RawMetal and spent171gold on Hawkeye+1. Final8gold/13XP/58HP,1304/1332bow condition and the same owned instance survived reconnect and authoritative read. Nine Wood attempts and one Metal attempt were paid individually. No personal grants/time advance; the shared QA frontier was separately staged to3. Group energy/partial XP/pending haul, partial shields, resistance, fixtures' ambush/extract/retry, and selected weapon/Forge cards passed their recorded checks.

The main390px Chromium pass confirms332px generic row content/scroll width and151px combat button content/scroll width, wrapping tool requirements and all3cards/four grade choices. Current natural account and the original BaselineAsh were preserved. The browser runner's final report follows separately; its underlying completed screenshots and safe snapshots already substantiate this scope gate.

Open findings are retained: P3-008 Luna exceeded a narrower two-gather request with three gathers before extraction (four total actions), although each was correctly charged. Phase7 must address assistant action-bound behavior. Existing trait labels omitted from scene_text produced a casual “no special traits” reply; phase4 supplies canonical trait descriptions. These are not hidden by the passed engine/transaction gate. The broad death/migration/all-content/wardens matrix remains later work.

Coded verification:70focused,6CPU/replay,1512full-plugin passes with8known legacy failures,62simulator and8HTTP passes. Current full worldd231pass/1stale-wiki-stamp failure; after generating current data,4wiki tests passed. Two current actual-game traces replayed exactly1055/2313actions. Further100-floor policy/economy tuning remains necessary: the corrected ten-day run reachedfloor10 with3/8players and still has a steep early delay. Proceed to the committed phase4 implementation decisions; do not deploy this partial candidate.
