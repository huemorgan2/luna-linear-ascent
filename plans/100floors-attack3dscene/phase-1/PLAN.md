# Phase 1 — floors 1–10: promote the Arena out of Labs, ship the backdrops

## Goal

Every player fights in the 3D arena on floors 1–10 with a proper 320×300
animated backdrop for all 69 foe ids (61 encounters + wardens 001–010), with
no Labs toggle involved. Measurable: `labs.FEATURES` has no `"arena"` key;
`arena.enabled(p, f)` is True for floors 1–10 and False for 11+ regardless of
the player doc; `backgrounds300/` covers all 69 ids (55 new files, each
320×7200 1-bit); plugin + worldd test suites green; dojo walkthrough PASS on
floor 1; deployed and verified live.

## Steps

### A. Code — promote the gate (plugin submodule first)

All engine edits happen in
`plugin-linear-ascent/plugin_linear_ascent/engine/`, then are vendored.

1. `arena.py`: add the rollout gate and cut the Labs dependency:
   - `READY_FLOORS = frozenset(range(1, 11))` (module constant, with a
     comment: grows by 10 per phase of plans/100floors-attack3dscene;
     delete after phase 10).
   - `enabled()`: keep the floor-resolution logic, replace the final
     `return labs.enabled(p, FEATURE, fl)` with `return fl in READY_FLOORS`.
   - Drop the `labs` import and the `FEATURE = "arena"` constant; update the
     module docstring (no longer "when the arena is on for this player").
2. `labs.py`: delete the `"arena"` entry from `FEATURES` (figure3d stays).
3. `scene.py` (~line 207): update the `arena` field comment — the payload
   rides on `READY_FLOORS` floors for everyone, not "floors 6–7 with
   labs.arena on".
4. `worldd/static/site/fight3d/arena3d.js` header comment (line 2): same
   correction; bump `ARENA3D_URL` to `?v=5` in `worldd/app/webplay.py`.
5. Tests:
   - `plugin-linear-ascent/tests/test_067_labs.py`: the labs card now lists
     only figure3d (`labs_toggle_arena` gone); the floor-gate unit test
     moves off the arena key (assert `"arena" not in labs.FEATURES`, keep
     the gate semantics covered via a locally-constructed `Feature`).
   - `tests/test_067_arena.py`: `_climber()` drops `labs.set_flag`;
     gating tests become: enabled on floors 1 and 10 with no flag set,
     disabled on floor 11; `test_off_everywhere_else` reworked accordingly.
   - `worldd/tests/test_067_arena3d.py`: unchanged (script-tag level).

### B. Vendor + tests

6. Diff plugin tree vs vendor tree first (`diff -r --brief
   plugin-linear-ascent/plugin_linear_ascent worldd/vendor/plugin_linear_ascent`)
   — confirm nothing vendor-only would be deleted, then run
   `worldd/tools/vendor_game.sh`.
7. `cd plugin-linear-ascent && pytest tests` (targeted `-k "arena or labs"`
   first, then full). `cd worldd && pytest tests` (targeted
   `test_067_arena3d.py`, then full).

### C. Assets — 55 arena backdrops

8. Restore the image pipeline (see main-plan BLOCKER): re-clone
   `luna-plugins` next to the workspace so the `plugin-image-gen` symlink
   resolves, or add a local providers shim. Generate ONE canary still
   (`grey_wolf`), inspect it, only then batch.
9. `research/3d-fight/gen_bg_arena.py`: replace the hardcoded 14-id `IDS`
   with ids derived from the floor YAMLs for a `FLOORS` range (1–10 now) +
   `warden_NNN`; merge floor-1 scene prompts (from
   `demo2/gen_backgrounds.py` SCENES + its floor-1 setting text) into the
   `gf.SCENES` lookup so floor-1 ids resolve. Skip-existing stays (the 14
   shipped floors-6/7 sheets are not regenerated).
10. Run `gen_bg_arena.py stills` (55 Gemini calls, resumable, skips
    existing jpgs), then `gen_bg_arena.py sheets`. Working files in
    `research/3d-fight/backgrounds_arena/`, sheets land directly in
    `worldd/static/site/fight3d/backgrounds300/`.
11. Census: every floor 1–10 id present in `backgrounds300/`; each new PNG
    is 320×7200, mode `1`. Eyeball the `_still.png` contact prints.

### D. Commit, dojo, deploy

12. Secret scan on every diff. Commits, in order:
    1. workspace: this plan (already committed before execution).
    2. `plugin-linear-ascent`: engine + tests change ("100floors phase 1:
       promote arena out of Labs; READY_FLOORS 1–10").
    3. workspace: vendored copy + webplay/arena3d bump + submodule pointer.
    4. workspace: `backgrounds300/` assets + gen_bg_arena.py changes.
13. Dojo: run `phase-1/dojo/01-arena-floors-1-10.md` against the local
    stack (same recipe as dojo 0046: worldd on :8600); write
    `dojo/results/00NN-arena3d-phase1-<date>/` with summary.md +
    screenshots. Regressions are filed, not quietly fixed.
14. Deploy: push main, `worldd/tools/deploy.sh`, poll `/health`, then fight
    on floor 1 in production and confirm the 3D arena with backdrop.
15. Append Execution status to this file; commit.

## Verification

- `python3 - <<'EOF'` census (floors 1–10): 0 ids missing from
  `monsters/`, `backgrounds/`, `backgrounds300/`. Each new sheet:
  `PIL.Image.open(...).size == (320, 7200)`, `.mode == "1"`.
- `pytest tests -k "arena or labs"` (plugin) — the new gate tests pass;
  full plugin suite green; full worldd suite green.
- Grep proof the old branch is gone: `grep -rn '"arena"' engine/labs.py`
  returns nothing; `grep -n READY_FLOORS engine/arena.py` shows the gate.
- Dojo: floor-1 fight renders the 3D stage (canvas `.a3d` present), the
  backdrop is not black, turn beats play in order, numbers match the log;
  floor-11 (via an account on floor 11) still gets the classic 2D card.
- Production: same floor-1 check on the live site after deploy.

## Rollback

- Code: `git revert` of the plugin commit + workspace vendor/pointer commit
  (restores the Labs gate exactly — the deleted FEATURES entry and
  `labs.enabled` call come back; stale `p["labs"]["arena"]` player flags
  resume working). Redeploy with `worldd/tools/deploy.sh`.
- Assets: none needed — `backgrounds300/` files are additive and unread
  while the gate excludes their floors; delete the 55 new PNGs only if a
  sheet is actually bad (`git rm` the file, redeploy).

## Execution status (2026-08-24)

**Complete. Live in production at 0.100.0.**

- **Code:** plugin `f4d7dca` — `READY_FLOORS = frozenset(range(1, 11))`
  gate in `engine/arena.py`, labs "arena" Feature deleted, `_foe`
  hardened against key-less fight docs; workspace `8de20cf` (vendor +
  plugin pointer + arena3d.js header), `5e263ec` (assets). Vendored by
  surgical file copy — the plugin tree held in-flight 075 edits, so
  `vendor_game.sh` was not used. Shipped inside the 0.99.1→0.100.0
  vendor rolls (`588b712`, `87e6a9f`).
- **Assets:** 55 new arena sheets generated (Gemini nano-banana-pro
  stills → density master → 24-frame 1-bit sheets). Census after:
  **69/69** floor-1–10 ids present in `backgrounds300/`, every sheet
  320×7200 mode-1, 1939 KB total. Generator reworked to derive its id
  list from the floor YAMLs (`research/3d-fight/gen_bg_arena.py`,
  `FLOORS = range(1, 11)` — widen per phase).
- **Suites:** plugin 1343 passed, 5 failed — 4 pre-existing
  (test_048_no_classes, 3× test_kill3d), test_059 a concurrent-edit
  artifact that passes standalone. worldd 201 passed, 1 failed —
  test_leaderboard_marks_only_you: local dev DB holds 512 'playing'
  docs and the score endpoint windows to top 200, so the fresh level-1
  account falls outside; environment artifact, not a regression.
- **Dojo:** local run 0047 **24/24 PASS** (floors 1 and 8 on the stage
  with backdrops, Labs card arena-free, floor 11 classic, DB labs docs
  clean; steady-state round 570 ms). Production re-check after deploy
  **6/6 PASS** at 0.100.0 (fresh signup, floor-1 hunt → stage +
  backdrop 200). `dojo/results/0047-100floors-phase1-2026-08-24/`.
- **Deploy:** `worldd/tools/deploy.sh` → deploy
  `dep-da686161egvs739o2dsg` live, `/health` reports 0.100.0. The build
  also carried the concurrently released 075 pursuit model and 076 lift
  transitions (released in parallel this session by the other driver).
- **Operational note:** the luna submodule's git object store depended
  on a deleted Google Drive clone via `objects/info/alternates`; removed
  the dead alternate (backup: `alternates.bak-dead-drive`), dropped two
  stale remote refs, `git fetch --refetch` — fsck clean.
