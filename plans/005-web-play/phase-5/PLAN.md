# Phase 5 — dojo walkthroughs + ship

## Goal

The whole surface proven end-to-end in a real browser against
production, results archived. Measurable: all three dojo scenarios
PASS with screenshots; `/health` game matches the shipped version;
regressions (if any) filed, not quietly fixed.

## Steps

1. Run the three scenarios in `../dojo/` against production with a
   real browser (Playwright), fresh throwaway accounts
   (`webprobe-<hex>`), pacing under the signup/act rate limits:
   - [01-signup-to-first-hunt.md](../dojo/01-signup-to-first-hunt.md)
   - [02-two-accounts-one-world.md](../dojo/02-two-accounts-one-world.md)
   - [03-web-and-luna-share-the-world.md](../dojo/03-web-and-luna-share-the-world.md)
2. Archive a numbered results folder under `dojo/results/` —
   summary.md (date, commit SHAs, environment), PASS/FAIL table,
   screenshots, regressions list.
3. Ship ritual (if any fixes landed): plugin tests → bump →
   publish → sha verify → vendor → outer push →
   `render deploys create srv-d9ha3csvikkc73ff5rg0 --confirm --wait`
   → `/health` game check.
4. Append Execution status to every phase PLAN.md; commit.

## Verification

The dojo run IS the verification. Gate: a plan is not reported
complete without the walkthrough (workspace rule).

## Rollback

n/a — this phase only observes and records. Fixes it triggers get
their own commits with their own rollbacks.
