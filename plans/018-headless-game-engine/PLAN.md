# 018 — Simulate through the actual game engine

## Problem and evidence

12 September 2026: the user clarifies that the swarm must execute the game's exact libraries without the UI. The existing proposal simulator imported numeric snapshots but duplicated combat and economic transitions, so its curves could not establish live-game behavior. Plan 017 corrected some drift but did not solve the architectural problem.

## Root cause

The first implementation chose an independent resolver to explore mechanics not yet implemented in the game. The repository already exposes `plugin_linear_ascent.engine.core.apply_choice` and `current_scene`, called by `worldd/app/game.py`. Rendering and HTTP are not required for these entry points. The game has deterministic RNG and a replaceable `state.now()` clock.

## Mitigation already taken

Stopped the proposal matrix after 11 saved runs. Preserve historical runs and proposal code, clearly labeled. No production data or game rules changed.

## Phases

1. Import the engine through the same gamepath resolver used by worldd; add an isolated clock/player adapter and exact-state replay tests. Hash the actual code and floor content; reject mixed-revision runs. No copied damage, loot, repair, XP or regeneration formulas.
2. Drive legal game actions with several heuristics; reuse automatic CPU scheduling and censoring-aware graphs. Make actual-engine runs the default CLI and website. Keep historical proposal runs in a separate view. Add per-action replay/inspection through the same adapter.
3. Run seed/CPU parity, source-mutation and invariant tests, a real browser walkthrough of actual-engine play and result inspection, and a measured short cohort. Document observed bottlenecks and engine/host boundaries. Keep the engine mechanics unchanged; new deck/group rules must later be implemented once in the game, then inherited here.

## Verification

Every recorded action must be accepted by the actual core. Direct core execution of the recorded actions at the same times must reproduce the complete player state, scene and RNG counter. CPU count must not change semantic outputs. Use actual character creation and purchases; no free equipment or skipped costs in the player trajectory. Readiness probes use disposable copies and explicitly disclose restored meters/open-floor test conditions. Unsupported worldd-backed multiplayer outcomes must remain unavailable rather than reuse proposal formulas.

## Operational notes

Simulator-only code changes. Production service imports are resolved the same way as gameplay, with path/hash/version in every run. Scheduled activity, decision heuristics and virtual time are simulator inputs; game outcomes come from the engine. Isolated player documents replace persistence for local engine play; PostgreSQL-backed shared-world services are outside this headless personal progression scope and must be named where their absence affects interpretation. Existing current-engine mechanics remain current; do not silently inject proposed decks, group fights, overflow XP or healing-warden laws.

## Rollback

Revert the phase commits in reverse order, restart only simulation/serve.py, and preserve both run directories. No database rollback is required: the runner uses only synthetic documents.

## Execution status

Plan committed as 252afec before implementation. Phase 1: 667f237. Phase 2: 8935fb8. Phase 3 policy correction: 45b97a5; final verification/UI commit recorded below after committing. All three phases are complete for the explicitly defined personal-engine scope. Final checks: 45 passing simulator tests, exact replay and CPU parity, six repeated 30-day cohorts, and a passing 21-step real-browser walkthrough with desktop/mobile screenshot judgment. No production service or game-library code changed. Shared-world warden execution remains outside this local runner and is clearly labeled unavailable; this plan does not claim full MMORPG or proposed-mechanics coverage.
