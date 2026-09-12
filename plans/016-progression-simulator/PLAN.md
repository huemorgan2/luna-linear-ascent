# 016 — Player swarm and progression simulator

## Problem, evidence and timeline

12 September 2026: the weapon/deck/group proposal has no executable account-level model. Existing `plugin-linear-ascent/tools/sim046.py` explicitly ignores deaths, weapon-honing XP and most weapon choices, and substitutes one scheduling day for later multiplayer gates. Its outputs cannot answer the current request: calendar days to hunting readiness under different heuristics, failure rates, or finite-energy parties against continuously healing wardens.

The user requests ordinary fast software, not LLM agents, in the project-root `simulation/`, with reproducible run files and a results website. The latest fixed rule is one energy per begun enemy; unfunded enemies cause exhaustion, retreat does not charge queued enemies, and full-group victory secures loot while each kill retains XP.

## Root cause

Reference power tables measure equipment strength, not the time needed to earn a sustainable deck. Solo combat averages and stored-pledge boss formulas do not model the proposed encounter or concurrency rules. Censored players must remain visible rather than disappearing from averages.

## Emergency mitigation

None. This is a standalone development simulator; no production state or game resolver is changed.

## Fix split into phases

1. [Pinned inputs and executable combat contracts](phase-1/PLAN.md): source snapshot with provenance, explicit proposal assumptions, three-weapon combat and per-enemy energy/rewards.
2. [Player swarm, readiness and wardens](phase-2/PLAN.md): six deterministic policy families, seeded stochastic outcomes, calendar/active-time resource simulation, per-floor readiness measurements, timestamped finite-energy boss trials, versioned run JSON and CLI.
3. [Run explorer and verification](phase-3/PLAN.md): standalone localhost website, run creation/history/comparison, progression/difficulty/party graphs, meaningful coded checks, performance measurement and a real browser walkthrough of this interface.

## Verification

Use Python's standard library for the simulator and its tests. Run `python3 -m unittest discover -s simulation/tests -v`. Exercise CLI deterministic replay and a timed swarm; verify file validation, aggregates, resource conservation, exhaustion and warden healing. Open the local website, create a run, select another saved run, compare cohorts/floors, inspect tooltips and narrow-screen layout. The scenario is written before implementation in `dojo/01-run-explorer.md`.

The simulation itself makes no LLM, browser or network calls. Its UI is inspected in a browser as a development verification step. It does not modify plugin tools, actual game combat, content or worldd endpoints; a Luna gameplay session would not exercise this standalone program. Proposal numbers are explicitly identified as a model, not production measurements or proof of subjective fun.

## Operational notes

Owner: root repository, branch `codex/016-progression-simulator`; all executable/output files live under `simulation/`. Preserve unrelated working changes. No deployment to production is in scope. Pin the wiki 089.3/game 0.112.0 input from the existing release checkout, including source checksums. Record source laws and approximation boundaries; never silently tune results to a desired number of days or players.

Default study assumes hunting floors become available when personal readiness permits; shared-world unlock calendars are not silently counted as personal preparation. Show measured available qualified players separately from reference party-demand estimates. A threshold crossing uses independent fixed probe encounters, not the lucky training kill that happened to win. Never substitute zero days for an unreached floor. Wall time is an assumption based on sessions, action cadence, rest and energy, and is exposed with each run.

## Rollback

Each phase adds isolated simulator files. Revert its recorded implementation commit with `git revert --no-edit <phase-commit>`; preserve generated runs as user artifacts. Stop the local server using its recorded terminal session or Ctrl-C. No player database rollback is involved.

## Execution status

Plan recorded before implementation. All phases not started.
