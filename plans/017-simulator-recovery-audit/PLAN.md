# 017 — Audit recovery, diagnose stalls and test progression

## Problem, evidence and timeline

12 September 2026: user authorizes all five follow-up steps: audit assumptions, improve heuristic choices, explain stalls, run controlled experiments, set provisional pacing targets and test fights. Baseline v1: 24 players/120 days, full-HP median ready floor 6; half-HP run has 19/24 fully broken decks and only one floor-11 qualifier on day 117. Healing/repairs consume 56% of hunting gold in that comparison.

## Root cause

Source inspection already identifies discrepancies: cumulative upgrade spend used for repair quotes despite the research forbidding it; upgrades preserve wear percentage instead of absolute missing durability; all broken weapons become unusable while no retained starter recovery exists; lower-floor reward fading starts immediately instead of after five floors; attack damage lacks the proposal's 15% pre-defense floor; shield capacity differs from the written proposal. Bot policies spend healing/ammo before protecting recovery funds and generally return to the frontier despite repeated unprofitable groups. Further assumptions require explicit classification, not silent tuning.

## Emergency mitigation

None. Existing runs stay immutable and usable. No production resolver, player database, deployment or migration changes belong to this simulator follow-up.

## Phases

1. Audit and versioned corrections: source-linked assumption ledger, reproducible v1 reference, explicit audited rules and targeted contracts.
2. Recovery heuristics and diagnostics: reserve-aware shopping, affordable repair/replacement and route choices; explain readiness failures, resource flows and recovery intervals in saved results and UI.
3. Experiments and pacing: paired seeds and policies, one-factor comparisons, provisional target ranges and honest censoring; saved batch manifests and an evidence-based recommendation.
4. Fight lab and browser verification: interactive proposed group fights using the same combat function, not a second toy engine; verify counter choices, movement, exhaustion, reward escrow and failure/recovery. Include browser-visible batch/diagnostic results.

## Verification

Targeted tests, then the complete standalone simulator suite. Reproduce baseline player/floor outcomes before accepting comparisons. CPU counts must not affect outcomes. Match repair, damage and wear examples to local source. Browser walkthrough checks diagnostics against JSON and plays representative proposed encounters. The proposed rules have not been implemented in Luna/production; the local fight lab is their playable prototype, and must not be described as a production gameplay test. No claim that bots prove human enjoyment.

## Operational notes

Branch `codex/017-simulator-recovery-audit`. All code is in `simulation/`; audit/recommendation artifacts in `research/simulation-audit/`. Automatic CPU use remains the default. Runs retain seed, revision and complete assumptions. Initial comparison uses multiple seeds with equal policy allocations. Keep monster/weapon asymmetry. Provisional pacing for 30 min/day: floor10 7–14d,25 30–60d,50 90–180d,100 270–365d, pending user preference; never grant resources or alter growth to manufacture passing targets. Wardens keep fixed continuous healing and finite player energy; report their qualified cohort separately.

## Rollback

Each phase is an isolated commit. Revert phase commits in reverse order; preserve run JSON. Stop/restart only the local simulator server. Retain old-model code and source snapshots for reproducible comparisons. No public rollout is authorized by this simulator work.

## Execution status

Plan written before implementation. Audit evidence gathered; phases not yet executed.
