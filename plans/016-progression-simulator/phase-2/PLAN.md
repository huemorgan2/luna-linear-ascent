# Phase 2 — Swarm, progression and boss demand

## Goal

Run a reproducible swarm without LLMs, persist each run, and measure elapsed days, active time, readiness coverage and finite-energy warden party requirements across all floors.

## Steps

1. Implement six named policy families with inspectable decision rules for route, deck, spending, retreat and exhaustion. Derive separate seeded random streams for training, readiness probes and bosses.
2. Simulate persistent gold, XP, materials, equipment condition, repair/ammo/healing costs, energy regeneration and daily play sessions. Log resource bottlenecks and per-player floor milestones.
3. Define readiness against repeated fixed representative group probes. Record successful-cohort mean/median/P90, all-cohort reach fraction and censored observations separately; no invented full-population average.
4. Probe reference equipment and the actual newly-qualified cohort against one shared healing HP pool using timestamped strikes, finite energy/HP, a bounded party search and visible failure reasons.
5. Implement `python3 simulation/run.py` and a versioned JSON run file with config, seeds, source/model hashes, runtime, per-player outcomes, floor aggregates and boss trials. Implement `--config`, `--players`, `--days`, `--seed`, `--output-dir` and deterministic replay.
6. User extension, 12 September: use portable CPU process workers for independent players and warden floors. Support explicit large worker counts and `--workers 0` for automatic CPU availability, including Linux affinity. Preserve deterministic player/floor ordering and identical seeded output across worker counts. Record execution hardware and worker count separately from semantic result hashes. Document headless operation and browser access through an SSH tunnel for another computer.

## Verification

Run the simulator's complete unit suite, repeat a small run with the same seed and compare deterministic payloads, change the seed and verify stochastic outcomes can change, and benchmark a representative swarm. Verify null/unreached floors, partial energy costs, resource non-negativity, independent probes and monotonic warden-HP/regen sensitivity. Report runtime and any model bottlenecks without adjusting inputs to conceal them.

## Rollback

Revert the recorded phase implementation commit. Preserve generated JSON runs and phase-1 input snapshots; they remain inspectable artifacts.

## Execution status

Complete. Implementation: `8ab97f9`; Windows many-CPU pool sharding and automatic-dispatch verification completed in `576feb9`; 16 tests pass, including serial versus three-process exact replay, money conservation, censoring, per-enemy energy and finite-resource warden trials. A 24-player, 120-day, 100-floor serial run completed in 45.5661 seconds; automatic eight-CPU execution completed in 16.7289 seconds (2.724×), with the same semantic hash. The final comparison is recorded in the verification report. Earlier four-worker execution matched every player/floor/warden result and took 21.0438 seconds versus 33.7722 serial (1.60×). Default proposal results stall around floor 6; this is retained as evidence of resource/group pressure, not tuned away. Rollback: `git revert --no-edit 8ab97f9`.
