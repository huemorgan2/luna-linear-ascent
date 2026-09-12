# Phase 1 — Measure the game and establish the balance harness

## Goal

Produce a reproducible baseline for floors 1–100 and a measured action clock for hunts and wardens. Record how long progress takes in energy, gold, materials where applicable, actions and elapsed time. Reproduce the suspected warden energy-unit mismatch before choosing replacement HP or healing.

## Steps

1. Pin the current plugin/server/client SHAs and capture the reference loadouts,100 floor definitions and actual economy constants. Read-only production measurements, if used, must be separated from test fixtures.
2. Run fresh, returning and overprepared legal characters through normal/deep hunts and ordinary/milestone keeps in the QA browser. Measure request-to-visible-result latency, energy charged per action and when shared HP changes. Do not refill energy between swings.
3. Add a planned comparison harness at `tools/progression/run.py` with baseline/candidate rules, seeded policies, discrete timestamps and machine-readable reports. Its configuration explicitly budgets training, armor, counter weapons, ammo, bank interest, sleep, repairs and death.
4. Use a small calibration run first. Capture milestone distributions and non-completion, then freeze the main plan's proposed gates or record a justified revision before adding candidate behavior.
5. Commit baseline fixtures, reports and scenarios. These artifacts are inherited by every later phase; they are not another combat implementation.

## Verification

Run `python tools/progression/run.py --rules baseline --floors 1-100 --runs 10000 --seed 1501 --output output/progression/baseline` after the planned harness exists. Compare a sample of simulated actions against engine events and actual QA browser play. Run dojo S01. Explicitly show entry energy, swing energy, allowed swings, elapsed time and damage committed for floors 1/10/31/50/99/100.

## Rollback

Remove/revert only the harness/report implementation commit. No player or shared-world writes belong to baseline collection; retain evidence if a pre-existing issue is found.

## Operational notes

This is future work. Planned harness/tool paths named above must be implemented before their commands can run. Record exact implementation SHAs, deployed revisions and any migration arguments before executing a release or conversion. The plugin owns engine/content/cards; worldd owns authoritative shared state. Both inherit the versioned definitions. See the parent plan and DOJO-SCENARIOS.md.

## Execution status

Not started. This planning task does not claim runtime verification.
