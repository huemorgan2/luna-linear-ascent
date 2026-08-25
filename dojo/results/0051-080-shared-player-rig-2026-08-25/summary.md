# dojo run 0051 — 080 shared player rig (judgment run)

- **Date:** 2026-08-25
- **Environment:** local worldd (uvicorn :8600, Postgres 5434), Cursor browser
- **Parent repo:** a4ca959 (080 phase-3)
- **Plugin submodule:** ca65155 (080 phase-3)
- **Scenarios:** `worldd/tests/080-shared-player-rig/`
- **Player:** DojoEighty (fresh account, human warrior, starter gear:
  gate_jerkin + gate_buckler + rusted_sword)

## Verdicts

| Scenario | Verdict | Evidence |
| --- | --- | --- |
| portrait-regression | PASS | `portrait-human-elf.png`, `portrait-giant.png` |
| finisher-ink | PASS | `finisher-ink-harness.png` |
| finisher-gear | PASS | `finisher-gear-live-kill.png` |
| arena | PASS | `arena-live-combat.png` |

## Notes per scenario

**portrait-regression** — figure3d harness after the port to `lib/character.js`.
Human holds the sword gripped in hand with shield on the forearm; elf carries
the bow on the back and sword on the hip; giant grips the staff. Continuous
dither, crushed blacks, no banding. No visual change from the pre-080 portrait.

**finisher-ink** — fight3d harness (grey_wolf stand-in). The finisher now
wears the portrait tone curve: smooth `smoothstep(0.28, 0.75)` ramp inside the
card's tint, climber reads as a crushed-black silhouette with the blade
clearly separated. No 6-step banding anywhere in the sky or ground.

**finisher-gear** — live `/play` kill as DojoEighty. The fragment shipped
`data-rig3d="human:blade:gate_jerkin+gate_buckler+rusted_sword"` (verified in
DOM); the finisher played with the geared climber and the wolf went down with
the XP/gold overlay ("The Grey wolf goes down — no match for your Rusted
Sword."). Gear GLBs pre-warmed from the rig attribute — no visible pop-in.

**arena** — the same live fight, arena stage during combat: geared climber
faces the grey wolf on the 320×300 canvas, HUD bars live, tone curve matches
the finisher. Strike → damage lines → kill handoff all rendered.

## Suites

- **worldd:** `215 passed, 0 failed` in 76.68s. (The 7 failures in the
  2026-08-24 overnight run all pass when run cleanly — two suites had been
  hammering the same Postgres concurrently; one had a stuck
  idle-in-transaction backend that had to be terminated.)
- **plugin:** `8 failed, 1369 passed, 1 skipped, 1 xfailed` in 21.71s. All 8
  failures re-run identically at the pre-080 commit dc0742e (verified in a
  detached worktree), so none are regressions of 080: three stale PLAN4-era
  `test_kill3d.py` tests (floor-1 victories now ride `data-arena` per 067, so
  the card carries no bare banner slot and no `data-kill3d`), plus
  `test_017_speed_chase::test_pre_002_docs_mid_fight_default_to_close`,
  `test_022_002_retune::test_kill_xp_still_accrues_at_cap`,
  `test_048_no_classes::test_no_clazz_reads_outside_migrations`,
  `test_067_arena::test_distance_move_and_chase_recorded` — these last four
  passed in the 2026-08-24 run of the SAME commit, so the drift is
  environmental (shared `luna/.venv`), not this plan's code.

## Regressions

None found in this run. The three stale kill3d tests above are filed in
`MUST_BE_DONE_LATER.md` (plugin) rather than quietly fixed mid-run.
