# 081 phase-2 — beginner pity: misses never stack past your level

## Goal

At level L ∈ {1,2,3}, a player can never suffer more than L sequential
misses — the next swing after L misses is a guaranteed hit. Level ≥ 4 is
untouched. Measurable: a simulated rank-0 level-1 player over 500 rounds
never logs 2 misses in a row; the same sim at level 4 still shows natural
25% streaks.

## Steps

1. **Constant in economy** (both copies), next to `TRAIN_MISS_PCT`
   (economy.py:782):
   ```python
   PITY_MISS_MAX_LEVEL = 3
   def pity_miss_run(level: int) -> int:
       """Sequential misses allowed before the next swing must land."""
       return level  # only consulted for level <= PITY_MISS_MAX_LEVEL
   ```
2. **Guard the roll** in `_resolve_round`'s attack branch
   (combat.py:2683-2696):
   ```python
   rank = _train_rank(p)
   miss = economy.TRAIN_MISS_PCT(rank) / 100
   pity = (p["level"] <= economy.PITY_MISS_MAX_LEVEL
           and e.get("miss_run", 0) >= economy.pity_miss_run(p["level"]))
   if miss > 0 and not pity and state.roll_ok(p, miss):
       e["miss_run"] = e.get("miss_run", 0) + 1
       ...existing miss branch unchanged...
   ```
   Counter increment goes BEFORE the at-range/close split inside the miss
   branch (both exits at combat.py:2698-2716 must see it).
3. **Reset on every non-miss path**: `e["miss_run"] = 0` immediately
   after the miss `if` block ends (~combat.py:2717), before `_victory` /
   `_player_hit` fan out. The counter lives in `p["encounter"]`
   (initialized combat.py:280-302), so it dies with the fight — no
   migration, no cross-fight carry, matching `"attacked"`/`"shot_used"`.
4. **RNG stream decision (accepted + documented in code comment):**
   short-circuiting `not pity` before `state.roll_ok` means a forced hit
   consumes no RNG draw (`roll_ok` advances `rng_counter`,
   state.py:678-681). Replay-exact tests that may move:
   `plugin-linear-ascent/tests/test_048_the_weapon_decides.py`,
   `tests/test_smoothness.py` — update expectations, do not weaken
   assertions.
5. **No special copy on the forced hit** — it should feel like skill, not
   charity. Surface the rule once in the mercy copy at unlocks.py:360
   ("while you're green, the tower won't let your swings go wide twice
   over").
6. **New test** in the plugin suite: level-1 rank-0 player, seeded so the
   first roll misses — assert round 2 hits and `miss_run` resets; level-3
   allows exactly 3; level-4 unaffected.
7. **Vendor sync**: submodule first, then `worldd/vendor` + parent
   pointer.

## Verification

- `pytest plugin-linear-ascent/tests/test_048_the_weapon_decides.py
  tests/test_smoothness.py` + the new pity test, then both full suites.
- Simulation script (scratch, not committed): 500 rounds at L1/L3/L4,
  print max consecutive misses — expect 1 / 3 / unbounded-ish.
- Client needs zero changes (combat is fully server-side; arena3d.js just
  replays `outcome`), confirmed by loading a fight and seeing normal
  hit/miss rendering.

## Rollback

Revert the commit. `e["miss_run"]` keys in live encounter docs are inert
leftovers and vanish when the fight ends (encounter cleared at
combat.py:1551/1715/2064).

## Execution status (2026-08-25)

- **Steps 1-3 implemented as planned.** `PITY_MISS_MAX_LEVEL = 3` +
  `pity_miss_run()` in economy.py; pity short-circuit before
  `state.roll_ok` in combat.py's default-attack branch (`miss_run`
  increment inside the miss block, reset to 0 right after it); counter
  lives in `p["encounter"]`, no migration.
- **Step 4.** Forced hit consumes no RNG draw (short-circuit before
  `roll_ok`), documented in the code comment. Replay-exact suites
  (test_048_the_weapon_decides, test_smoothness) needed NO updates —
  their fixtures never enter the pity window.
- **Step 5 evolved.** Rule surfaced as a third `protections_active`
  entry ("steady hands — … never go wide more than L in a row") plus a
  proper registry close entry `steady_hands_end` at level 4 — required
  by the 020 coverage guard, which caught the unregistered
  `PITY_MISS_MAX_LEVEL` constant. Level 3→4 level-up now also announces
  "steady hands end". Expectations updated in test_020_unlocks (×3
  asserts) and test_020_visible_gates (protections count 2→3);
  assertions strengthened, not weakened.
- **Step 6 tests.** `tests/test_081_pity_misses.py` — 6 tests:
  constants; L1 never misses twice; L3 exactly 3; L4 honest dice (6
  straight); forced hit consumes no roll_ok call; hit resets run. All
  pass.
- **Simulation** (scratch, 500 rounds each): max consecutive misses
  L1 = 1, L3 = 3, L4 = 4 (natural). Exact match to the goal.
- **Suites.** Plugin: 1375 passed, 8 failed — the same pre-existing 8
  as the phase-1 baseline (test_017 ×2, test_022, test_048_no_classes,
  test_067, test_kill3d ×3). worldd: full suite green (count in
  phase-7 summary).
- **Vendor synced** (economy.py, unlocks.py, engine/combat.py);
  `diff -rq` clean. Deploy deferred to phase-7.
