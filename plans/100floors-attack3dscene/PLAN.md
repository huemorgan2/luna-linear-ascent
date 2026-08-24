# 100floors-attack3dscene — promote the 3D attack scene (Arena) from Labs to the whole game

## Problem

The turn-based 3D fight scene ("Arena — turn-based 3D fights", 067) is a Labs
experiment, double-gated:

- per-player opt-in flag `p["labs"]["arena"]` (absent = off), and
- hard floor gate `frozenset({6, 7})` — both in
  `plugin_linear_ascent/engine/labs.py` (FEATURES, lines 27–34), checked at
  every seam by `engine/arena.py::enabled()`.

We want it ON for every player on all 100 floors. The gate is one module; the
real work is asset coverage. Measured 2026-08-24 (all 100 floor YAMLs diffed
against `worldd/static/site/fight3d/`):

| Asset | Have | Missing for 100 floors |
|---|---|---|
| Monster GLBs (`monsters/`) | 122 — floors 1–20 complete (102 encounters + wardens 001–020) | 403 (323 encounters + 80 wardens, floors 21–100) |
| Kill backgrounds (`backgrounds/`, 320×112 sheets) | 123 — floors 1–20 | 403 (same ids) |
| Arena backdrops (`backgrounds300/`, 320×300 sheets) | 14 — floors 6–7 only | 511 (55 for floors 1–10, 53 for 11–20, 403 for 21–100) |
| Player rigs, weapon models, strike clips (`players/`) | complete (3 races × blade/bow/staff × idle/slash/shoot/cast) | 0 — every forged weapon maps to one of the three paths |

Degradation is already graceful and stays as the safety net throughout the
rollout: missing monster GLB → the fight falls back to the 2D GIF flow
(`fight3d.js::ensureFor` returns null); missing arena backdrop → the arena
runs on a plain black stage (`arena3d.js` sets `uBGOn=0`); dead WebGL → 2D.

### Timeline
- 067 shipped the Arena as a Labs experiment piloted on floors 6–7, with
  arena backdrops generated for those two floors only.
- Floors 1–20 already have full monster GLBs + kill backgrounds (shipped for
  the kill finisher via `research/3d-fight/3d models/` + `gen_bg_floors.py`).
- 2026-08-24: decision to promote game-wide, 10 floors per phase.

## Root cause

Not a bug — deliberate Labs isolation (see the contract in
`engine/labs.py` docstring) plus assets produced only for the pilot floors.
Promotion is the designed exit: "flip the default, delete the old branch,
delete the key."

## Emergency mitigation already taken

None needed; nothing is broken.

## Fix — 10 phases, one per 10 floors

Phase N covers floors 10·(N−1)+1 … 10·N. Each phase ends with the gate
widened to include its floors, tests green, a dojo walkthrough, and a deploy.
The rollout gate is `READY_FLOORS` in `engine/arena.py` (introduced in
phase 1, replacing the Labs gate); it grows by 10 floors per phase and is
deleted after phase 10 (arena unconditionally on).

| Phase | Floors | Code | Monster GLBs | Kill bgs | Arena backdrops |
|---|---|---|---|---|---|
| 1 | 1–10 | Promote out of Labs; `READY_FLOORS = 1..10` | 0 | 0 | 55 |
| 2 | 11–20 | gate → 1..20 | 0 | 0 | 53 |
| 3 | 21–30 | gate → 1..30 | 50 | 50 | 50 |
| 4 | 31–40 | gate → 1..40 | 51 | 51 | 51 |
| 5 | 41–50 | gate → 1..50 | 50 | 50 | 50 |
| 6 | 51–60 | gate → 1..60 | 50 | 50 | 50 |
| 7 | 61–70 | gate → 1..70 | 50 | 50 | 50 |
| 8 | 71–80 | gate → 1..80 | 50 | 50 | 50 |
| 9 | 81–90 | gate → 1..90 | 52 | 52 | 52 |
| 10 | 91–100 | gate deleted (always on) | 50 | 50 | 50 |

Per-phase details, exact steps, verification, and rollback live in
`phase-N/PLAN.md`. Phases 3–10 share one shape (assets + gate bump); their
plans differ only in floor range, id counts, and the hand-authored prompt
work.

### Pipelines (all exist, all resumable)
- Monster GLBs: `research/3d-fight/3d models/gen_floors.py` — Tripo3D
  text→model→texture→rig→walk per creature, prompts hand-written from the
  floor YAML prose, body plan picks the rigger preset. Ship with
  `ship_floors.sh` (copies best GLB into `worldd/static/.../monsters/` and
  runs `optimize_glb.sh`).
- Kill backgrounds: `research/3d-fight/gen_bg_floors.py` — Gemini still →
  density master → 24-frame 320×112 loop sheet. Needs a hand-written
  `FLOOR` setting per floor and a `SCENES` entry per creature (currently
  covers floors 2–20; floor 1 lives in `demo2/gen_backgrounds.py`).
- Arena backdrops: `research/3d-fight/gen_bg_arena.py` — same stills
  pipeline re-parametrized to 320×300 (24-frame sheet into
  `backgrounds300/`). Currently hardcodes the 14 floor-6/7 ids; phase 1
  makes it read the floor YAMLs for a floor range.

## Verification (every phase)

1. Asset census: the phase's floor range has zero missing ids in
   `monsters/`, `backgrounds/`, `backgrounds300/` (script in each phase
   plan); every new `backgrounds300/*.png` is 320×7200 1-bit.
2. Targeted tests, then full suites: `pytest tests` in `plugin-linear-ascent`
   and in `worldd`.
3. Dojo walkthrough (mandatory before the phase is reported complete):
   scenario in `phase-N/dojo/`, results folder under `dojo/results/`.
4. Deploy is explicit: push, `worldd/tools/deploy.sh` (Render never
   auto-deploys this repo), poll to live, then verify the arena on a
   just-promoted floor in production.

## Operational notes

- **Both places rule.** Engine changes land in the `plugin-linear-ascent`
  submodule AND the vendored copy `worldd/vendor/plugin_linear_ascent`
  (sync with `worldd/tools/vendor_game.sh`), plus a workspace commit bumping
  the submodule pointer. Before any `vendor_game.sh` run, diff the plugin
  tree against the vendor tree — the rsync uses `--delete` and will
  clobber vendor-side WIP that never landed in the plugin.
- **BLOCKER (phase 1 step): image pipeline is dead on this machine.**
  `plugin-image-gen` at the workspace root is a broken symlink to
  `../luna-plugins/plugins/plugin-image-gen` (no `luna-plugins` checkout
  exists anywhere under `~/Documents`). Every image tool imports
  `providers.py` through it. Fix: re-clone `luna-plugins` as a sibling of
  this workspace, or ship a minimal local `providers` shim (Gemini
  `generateContent`, model `nano-banana-pro` / `gemini-3-pro-image-preview`,
  key `LUNA_GEMINI_API_KEY` from `luna/.env` — the key is present). Either
  way: generate ONE canary still and eyeball it before any batch.
- **Tripo credits (phases 3–10).** 067's 6 rigged player assets cost ~185
  credits; balance was ~4300 on 2026-08-13. 403 creatures at that rate is
  ~12,000+ credits — a top-up is likely. Run a 5-creature batch first in
  phase 3, measure actual credits/creature, and report the projected total
  before running the fleet. API key: `research/3d-fight/3d models/.env`
  (`TRIPO_API_KEY`, gitignored).
- **Prompt authoring is the human-scale work in phases 3–10**: per phase,
  ~10 `FLOOR` settings + ~50 `SCENES` entries + ~50 creature model prompts
  with body plans, written from the floor YAMLs' arrival/prose text (the
  same recipe floors 2–20 used). Budget it per phase; do not batch-generate
  from bare id strings.
- Secrets never enter the repo; secret-pattern scan before every commit.
- Old `p["labs"]["arena"]` keys on player docs become inert after phase 1
  (`labs.set_flag` guards on FEATURES membership; nothing reads the stale
  key). No migration needed.
- `arena3d.js` edits must bump `ARENA3D_URL ?v=` in `worldd/app/webplay.py`
  (and `FIGHT3D_URL` if `fight3d.js` changes — the importmap shares the URL).
