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

Not started. Rewritten for the three-weapon/group design on12 September2026; authorized for implementation by the subsequent user request. This document is not evidence that runtime changes or tests have run.

### Execution start —13 September2026

Phase2's essential state/collection browser gate passed on0.113.5. Implementation now follows `ENGINE-CONTRACT.md`, committed before runtime edits. Preserve the baseline legacy failure list and source-pin new group tests separately; phase3 must supply actual-engine group progression evidence, not reinterpret prior single-enemy runs.
