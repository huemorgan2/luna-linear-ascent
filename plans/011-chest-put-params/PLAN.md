# 011 — The chest's PUT cards say what the piece is

## Problem

Reported 2026-08-16 (screenshot: THE AGENT LABS · THE CHEST → "What
goes in the chest?"). When a member places a piece from the pack into
the faction chest, the card wall shows only the piece's name and the
tenure line "no coin — the faction keeps it". None of the piece's
parameters are visible — no +ATK/+DEF/+spd, no durability, no style —
so the donor can't tell WHICH piece they are giving away (a fresh
Wolfbite and one worn to 40% read identically), even though the scene's
own support line says "The wear rides with the piece".

The Forge already solved this idiom (031 §14 / 045 / 048 in the plugin
repo): every shop card's hint carries
`pay ◈ price · +N ATK · durability N,NNN`.

The same gap exists in the pawn shop's sister flow: the
"Donate <name> to the armory" rows (`_pawn_scene`, core.py) also say
only "no coin — the faction keeps it".

## Root cause

`_chest_put_scene` (engine/hall.py) and the pawn-shop donate rows
(engine/core.py `_pawn_scene`) build their `Option` hints from the
tenure sentence alone; the stat/durability formatting exists only as
local closures inside the Forge's `_rack` and is not shared.

## Fix (single phase)

1. **economy.py** — add `gear_card_stats(item, left=None) -> str`, one
   shared formatter next to `endurance()`:
   - stat: `+N ATK` (weapon) / `+N DEF` (shield, armor) / `+N spd`
     (shoes) — same wording as the Forge rack;
   - durability: `durability N,NNN`; when the pack's wear stash
     (`durability_pack`) says the piece is worn, `durability left of
     full` — the honest per-slot unit from `endurance()`;
   - style word (`keen` / `warded`) when the piece carries one.
2. **engine/hall.py `_chest_put_scene`** — hint becomes
   `{gear_card_stats} · no coin — the faction keeps it`.
3. **engine/core.py `_pawn_scene` donate rows** — same hint shape.
4. Changes land in **both places**: the `plugin-linear-ascent`
   submodule (source of truth, renders in the marketplace) and the
   vendored copy `worldd/vendor/plugin_linear_ascent/` (builds the
   scenes live in production).

No state, storage, or protocol changes; hints are display-only strings.

## Verification

- New coded tests in `plugin-linear-ascent/tests/test_chest_card_params.py`:
  fresh piece shows stat + full durability; worn piece (stash in
  `durability_pack`) shows `X of Y`; keen piece shows its style word;
  pawn donate row carries the same fragment; the `no coin` law text
  survives (existing `test_chest_put_flow_rides_the_pack` keeps
  asserting it).
- Full plugin suite green before and after.
- Vendor copy: import + direct scene render through
  `worldd/vendor/plugin_linear_ascent` produces the same hints.
- Dojo scenario `luna/dojo/tests/011-chest-put-params/scenario.md`
  (member with a fresh and a worn piece opens THE CHEST → PUT IN;
  cards must show stat and durability; worn piece must show reduced
  durability). Browser walkthrough runs against the next deploy.

## Rollback

Display-only change. Revert the two hint call sites to the literal
`"no coin — the faction keeps it"` and delete `gear_card_stats` — in
both the plugin submodule and `worldd/vendor`. No data migration in
either direction.

## Operational notes

- The plugin submodule and the `luna` submodule both carry unrelated
  in-flight work (plan 010 recolor, luna runtime.py); this plan stages
  only its own hunks and does not commit those.
- No deploy performed as part of this plan; ship rides the next
  explicit deploy per the production workflow.

## Execution status (2026-08-16)

- **Plugin submodule** — `economy.gear_card_stats` + both hint call
  sites committed as `985412c`; tests
  (`tests/test_chest_card_params.py`, 6 tests) committed as `18ca39c`.
  A concurrent session was mid-flight on plan 010 in the same checkout
  and reset the shared index between stage and commit — the code half
  was re-committed through a private `GIT_INDEX_FILE` with a
  compare-and-swap `update-ref`, staging only this plan's hunks; the
  010 worktree changes were left untouched and uncommitted.
- **Vendor copy** — same three edits applied to
  `worldd/vendor/plugin_linear_ascent/` (this commit).
- **Verification** — targeted: 6/6 new tests pass. Full plugin suite:
  1178 passed, 3 failed — the same 3 fail with this plan's edits
  stashed (pre-existing: `test_022_001`, `test_026`, `test_kill3d`),
  0 failures introduced. Vendor: direct scene render through
  `worldd/vendor` shows `+1520 ATK · durability 975 of 1,950 · no coin
  — the faction keeps it` on the chest PUT card (worn piece) and the
  identical fragment on the pawn donate row.
- **Dojo** — scenario committed in `luna` as `22350610`; the browser
  walkthrough has NOT run yet — it needs a deployed build with a
  faction member holding worn gear, so it rides the next deploy's
  acceptance gate.
- **Not done** — no push, no deploy, no plugin version bump, no
  submodule pointer bump (left to the deploy owner; plan 010 is
  in-flight in the same checkout).
