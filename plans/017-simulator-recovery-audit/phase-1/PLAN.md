# Phase 1 — audit

## Goal

Create a source-linked assumption ledger and a selectable audited rules revision; keep v1 reproducible.

## Steps

Freeze original swarm behavior. Correct running-cost repair basis, absolute missing wear on upgrade, lower-floor fade, damage floor and shield endurance using the pinned sources. Label condition/death/training/defense/acquisition assumptions; no fabricated parity with production.

## Verification

Run repair/wear/damage/fade/legacy replay fixtures; compare original baseline outcomes; check input hashes.

## Rollback

Revert the phase implementation commit recorded below; preserve saved runs and baseline files. Stop/restart only the simulator server if its API changed.

## Execution status

Complete. 24 tests pass (22.403s under concurrent run load). The preserved v1 run `20260912T174103Z-7084aad9` matches original player, floor and warden digests exactly. Audit at `research/simulation-audit/AUDIT.md`; pinned input unchanged. Implementation: `f6c4c5b`. Rollback: `git revert --no-edit f6c4c5b`; keep old run files.
