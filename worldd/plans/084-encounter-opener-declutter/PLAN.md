# 084 — encounter opener declutter: the sheet IS the card

## Problem

Reported by the user 2026-08-26 with a floor-7 opener screenshot. After
081's foe sheet, the opener card says everything twice and the eye has
nowhere to land:

1. The headline name + ◇ status lines ("at range", "it CANNOT reach
   you…", "your speed edge slips N%") repeat what the [i] dossier and
   the sheet already carry.
2. The prose block — support line ("It is between you and the way
   forward."), the sidekick whisper ("That thing hits harder than you
   do…"), the encounter description, and the You-line ("You — ATK …
   DEF …") — buries the sheet and the option rows.
3. The foe-sheet cells wear 1px outline boxes ("ugly boxes") in a 2×2
   grid — the user wants solid dark-grey cells, white text, all in ONE
   row.
4. The [i] dossier control loses its anchor when the headline goes —
   it must move onto the stat slab over the creature art, right of
   SPEED.
5. The grey floor bar under the image ("FLOOR 7 · MEN · THE ORCHARD
   ROWS") should also carry the monster's name — the only place the
   name then appears on an opener.

Scope: opener encounter cards only (foe_sheet present). Round cards,
arena HUD, victory/death cards unchanged.

## Root cause

Design accretion, not a bug: 081 added the sheet on top of the existing
opener prose instead of replacing it.

## Emergency mitigation

None needed.

## Fix — one phase (engine), then the standard ship steps

Engine (submodule first, vendor after, both copies in sync):

1. `engine/combat.py fight_scene`, opener only: stop emitting the
   description prose and the You-line (body starts empty; functional
   notes — swap note, fx, flare, presence — stay); `support` empty on
   openers; `shard_note` (the whisper) empty on openers. Round cards
   keep all three as today.
2. `render.py render_scene_fragment`: on opener cards (`foe_sheet` set
   and not arena-live) skip the headline and `_enemy_head_html`; append
   the foe's name to the eyebrow ("FLOOR 7 · MEN · THE ORCHARD ROWS ·
   ORCHARD WOLF"); pass the [i] info span into `_estat_html`, which
   prints it after SPEED on the black slab over the art.
3. `render.py` CSS: `.foesheet` becomes one flex row (cells share the
   line, `flex:1 1 0`, `min-width:0`); `.fscell` loses the border,
   gains a solid dark-grey background (#26241f), text white (BRIGHT)
   for label and hint; icons keep their type inks. `.estat .info`
   styled dim like the headline [i].
4. Tests: adjust existing assertions that expect opener prose/headline;
   add targeted tests — opener fragment has no headline/ehead/support/
   whisper, eyebrow carries the name, estat carries the [i], foesheet
   row layout class present; round card unchanged (support + shard
   feedback still render).
5. Version 0.106.0 both `version.py` files; vendor sync of ONLY the
   files this plan touches (082 floor-maps is mid-flight in the
   submodule at 392b530 — its unshipped floormap work must NOT ride
   into the vendor copy with this plan; `diff -rq` will show the 082
   files as expected pending diffs).

## Verification

- Targeted pytest (new/adjusted tests), then full plugin + worldd
  suites at baseline (8 pre-existing plugin failures, worldd 221).
- Dojo scenario `worldd/tests/084-encounter-opener-declutter/
  01-opener-declutter.md` walked in a real browser (desktop + mobile):
  opener shows image + [i]-on-slab + floor bar with name + one-row
  sheet + hint + options and NOTHING else; [i] popup still opens the
  dossier; round card still carries its prose. Results folder under
  `dojo/results/`.
- Deploy (explicit trigger + poll), post-deploy: live /health 0.106.0
  and a prod opener fragment spot-check.

## Rollback

Revert the engine commit(s) and redeploy the previous version. All
changes are presentational; no doc/schema migration.

## Operational notes

- Concurrent 082 (floor maps) executes in the same submodule — this
  plan lands on top of 392b530 and syncs only its own files to vendor.
- Never `git add -A` in the parent repo (unrelated user-dirty files).
- Secret-pattern scan before every commit.

## Execution status (2026-08-26)

**DONE — deployed 0.106.0.**

- Engine (submodule 9f414b9, on top of 082's 392b530): opener body/
  support/whisper stripped in `engine/combat.py`; `render.py` drops
  headline + ◇ plate on opener cards, moves the [i] onto the stat slab
  after SPEED (`display:inline-flex` — the base `.info` is a block;
  ≤480px the slab folds instead of clipping), appends the monster name
  (+ alpha/runt/tough specimen tag) to the eyebrow, and flattens the
  foe sheet to one flex row of solid #26241f cells with white text.
- **R-0055-1** (found by the dojo walk, fixed in-plan): the foehint ✕
  was a dead button in a real browser — `wireOptions` in pane.py never
  wired `button.x[data-opt]`. Run 0053 had verified the dismissal via
  API only. Wired + coded guard test.
- Tests: plugin 1408 passed / 7 pre-existing failures (same list as
  baseline; the old 8th, test_067_arena, was updated by this plan and
  passes); worldd 221 passed. RNG-stream shift from the retired
  `_shard_advice` draw pinned with blade rank 10 in affected tests.
- Dojo run 0055: PASS 33/33 checks, desktop + mobile, screenshots +
  summary in `dojo/results/0055-084-encounter-opener-declutter-2026-08-26/`.
  `foehint_done` flips server-side and holds across sessions.
- Vendor sync limited to combat.py / render.py / pane.py / version.py —
  082's unshipped floormap did not ride along (`git diff --stat` on the
  vendor tree confirms only these four).
- Commits: plugin 9f414b9, parent fbcd502, luna 836fdd1 (driver).
- Deploy: trigger=api via tools/deploy.sh, live /health game=0.106.0;
  post-deploy prod opener fragment spot-check recorded below.
- Post-deploy verification (2026-08-26 ~07:10 UTC): live /health
  `game=0.106.0, db=true`; prod opener fragment via fresh player
  Dojo084Prod — eyebrow `FLOOR 1 · MEN · THE FENCEROWS · Grey wolf —
  runt`, no headline/ehead/support/way-forward line, foesheet present,
  exactly one [i] on the slab. 7/7 checks PASS.
