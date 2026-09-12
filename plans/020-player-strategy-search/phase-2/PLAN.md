# Phase 2 — Bounded search and independent validation

## Goal

Find reproducibly stronger legal strategies using ordinary deterministic software and available CPUs, and preserve every trial for inspection.

## Steps

Enumerate a bounded grid of weapon focus, investment priority and farming risk. Run matched initial players/seeds and schedules, save full candidate outputs, rank milestone coverage and time including unfinished players, then repeat finalists on separate seeds. Store training/validation sets explicitly and report variability and failures. Select a normal-swarm planner profile only after validation.

## Verification

Same search seed/worker-count gives the same ranking and semantic outputs; every report points to a valid saved actual-engine run. Held-out seeds do not enter selection. Report observed, not proven optimal, speed.

## Rollback

Revert phase commit; preserve candidate/validation results and the previous default profile.

## Execution status

Search software implemented: 18 choices, no nested CPU pools, persisted trials and disjoint validation. Initial serial/parallel regression passed. The first 48-trial experiment was explicitly disqualified after the phase-1 long-run action bug was found. Corrected 30-day canary 20260912T194921Z-4a41d100 reaches floor 7 (character level 7), 645 kills, 6 deaths, no refused actions or decision loops in 22.548 seconds. Fresh training seeds 1901/1902 and validation seeds 2001/2002 are reserved for the corrected search. Final execution evidence pending.


Completed corrected search 20260912T195050Z-185ec874: 48 trials, 120 player trajectories, 1,800 simulated player-days, 386.560 seconds across 8 CPUs. All 18 profiles were screened on seeds 1901/1902; three finalists and three audit baselines used fresh seeds 2001/2002. No refused actions or decision loops in the accepted trials. The preselected staff/levels/margin-2 path reaches median final floors 7.5 and 8 versus corrected Mage 4.5 and 4. It remains selected independently of validation ranking; training-first ties it in this sample. This validated profile is now the default planner. Implementation: 932aa50; phase-3 default setting change recorded in its commit.
