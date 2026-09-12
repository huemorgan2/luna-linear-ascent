# Phase 2 — recovery

## Goal

Make recovery decisions inspectable and let knowledgeable policies preserve a viable deck without removing reckless play.

## Steps

Reserve recovery funds; buy partial repairs or cheap replacements when enabled; retain explicit starter recovery as a candidate. Evaluate sustainable routes using known stats and learned outcomes rather than future RNG. Record daily finances, recovery episodes, per-floor gate/readiness reasons and counterfactual diagnostic probes. Add UI breakdowns and legacy-run handling.

## Verification

Verify conservation, no free upgrades, broken-item recovery, route choices, mutually interpretable diagnostic categories and serial/parallel equality.

## Rollback

Revert the phase implementation commit recorded below; preserve saved runs and baseline files. Stop/restart only the simulator server if its API changed.

## Execution status

Complete. 30 tests pass (6.311s), including resource conservation, same-slot basic recovery, paid fractional repair, preserved reckless policy, lower-route choice, failed-probe diagnostics and parallel identity. A 24-player/120-day smoke run `20260912T174802Z-56e3dcd6` has median ready floor 22 (maximum28), versus original median6; this bundle is not a one-factor attribution. Four paid decks break completely, all Rushers. Code inspection found and corrected the CLI upper-middle statistic to a true median. Diagnostic UI added; full browser verification follows in phase4. Exact phase commit recorded after commit. Rollback: revert that phase commit and restart the local simulator; preserve runs.
