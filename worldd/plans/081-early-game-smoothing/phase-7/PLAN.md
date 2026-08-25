# 081 phase-7 — dojo walkthrough + judgment

## Goal

All six scenarios in `worldd/tests/081-early-game-smoothing/` walked in
a real browser against a local env running the same code paths as
production, judged with evidence. Results folder under `dojo/results/`
with summary.md (date, worldd + plugin SHAs, environment), per-scenario
PASS/FAIL table, screenshots, regressions list. Execution status
appended to every phase PLAN.md and committed.

## Steps

1. Bring up local env (same code paths as prod), seed three players:
   sender (level ≥ 2, funded), receiver (fresh level 1), bystander.
2. Walk scenarios 01–06 in order (01-relay-collect, 02-pity-misses,
   03-directed-toasts, 04-levelup-hint, 05-gear-clarity,
   06-encounter-type-clarity), screenshotting each Expected-behavior
   checkpoint and running each Verify block (DB queries, ledger reads).
   Scenarios 05 and 06 are walked on BOTH a desktop and a mobile
   viewport.
3. Any FAIL is filed as a regression in the results folder — not fixed
   mid-run.
4. Write `dojo/results/00NN-081-early-game-smoothing-<date>/summary.md`
   + screenshots.
5. Append "Execution status" to phases 1–7 PLAN.md files; commit.
6. Deploy (explicit: push, trigger via API, poll to live), then
   post-deploy verification: re-run scenario 01's Verify queries against
   prod, confirm huemorgan4's ledger evidence recorded in phase-1.

## Verification

The results folder itself, plus green full suites at the walked SHAs.

## Rollback

Not applicable (no system change in this phase); deploy rollback is the
standard revert-and-redeploy of the offending phase commit.

## Execution status

Executed 2026-08-25. Results: `dojo/results/0053-081-early-game-smoothing-2026-08-25/`
(summary.md, 36 screenshots, s02-rounds.txt). Env: local uvicorn :8600,
worldd 66e12ad, engine b3dc9e9 (vendor in sync), Postgres 16 :5434,
Playwright headless Chromium. Six players seeded via real web signup.

Verdicts: 01 PASS, 02 PASS, 03 PASS, 04 PASS, 05 PASS (desktop+mobile),
**06 FAIL — regression R-0053-1 filed**: the phase-6 foe sheet (grid +
swap hint) never renders on the web pane — `Scene.to_dict`/`from_dict`
(engine/scene.py:381/440) do not carry the new `foe_sheet` field, and
worldd's `/play/api/*` round-trips every scene through them
(app/webplay.py `_card`). Reproduced both ways: live opener fragment
has `data-arena phase:"opener"` and no `.foesheet`; a direct
vendor-code render of the identical opener (no dict round-trip) draws
the sheet. Working parts of 06 verified live: verdict prose gone from the
opener body, `pack` row at sizing-up, `wear_<slug>` swap accepted in
the window and refused with the re-rig reason after the first attack,
`foehint_close` flag server-side. Plugin `test_081_foe_sheet.py`:
10 passed (sheet renders off-arena).

Numbers: s02 — DojoPity1 (L1) 60 rounds, 11 misses, maxMissStreak 1;
DojoCtrl4 (L4) 60 rounds, 12 misses, maxMissStreak 4.

Deploy is NOT taken from this phase: R-0053-1 blocks "complete" —
fixed in phase-8 (planned + executed same day), s06 re-walked there,
then the deploy step of this phase runs at 0.104.0.
