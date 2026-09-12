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

Not started.
