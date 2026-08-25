# 080 — one player pipeline: shared rig, shared items, shared look

## Problem

The 3D climber is rendered by two scenes that have drifted apart:

- **figure3d** (profile portrait, 071/079): continuous 1-bit tone curve with
  crushed blacks (`smoothstep(0.28, 0.75)`), greyscaled textures, GRIPS
  emissive lifts (props 0.24), and the player's REAL worn gear from the
  76-item catalog (`figure3d/models/items/`, ~56 MB).
- **fight3d** (kill finisher + arena stage): 6-step posterized shading
  (`floor(shade * 6.0 + 0.5) / 6.0`, fight3d.js ≈ line 395), emissive lift
  on the bow only (blade/staff get none), and THREE generic placeholder
  weapons (`fight3d/players/{blade,bow,staff}.glb`) regardless of what the
  climber actually carries.

Evidence (2026-08-25 harness run, screenshots in the 080 dojo results):

- Player body at 320×112 dithers at nearly the same density as the scenery
  behind it — the figure does not separate (zoom crop of
  `test.html?id=grey_wolf&race=human&line=blade`).
- The rusted blade renders as a solid black stick (no emissive lift).
- md5 proves the player bodies are ALREADY the same rig duplicated on disk:
  human/elf/giant GLBs in `figure3d/models/players/` and `fight3d/players/`
  are byte-identical (9a9099…, 4340da…, 281dc2…). `vendor/GLTFLoader.js` is
  also byte-identical in both scenes (726811…).
- The body pipeline (settle idle → normalize height → boneMap) exists twice:
  `figure3d.buildFigure` and `fight3d.buildPlayer`.

Timeline: fight3d shipped first (PLAN3/PLAN4). figure3d (071) then learned
the portrait look; 079 shared only the socket/normalization module. The
tone curve, lifts, real items, and body pipeline never crossed back.

## Root cause

Assets and pipeline were **copied**, not **shared**, when figure3d was
built. Every later learning landed on the copy, not the source.

## Emergency mitigation

None needed — this is drift, not an outage.

## Fix — four phases

1. **phase-1 — one rig pipeline, canonical models.** New
   `static/site/lib/character.js` (loader cache, shadowify, buildRig,
   prop prep + dressing loop) and `static/site/lib/models/`
   (players + items + vendor GLTFLoader). Both scenes port. ZERO visual
   change — pure refactor + dedupe.
2. **phase-2 — render parity.** fight3d adopts the portrait tone curve
   (continuous ramp, crushed blacks) and takes prop emissive lifts from
   GRIPS. Tuned against the harness + gallery until bodies separate and
   every weapon family reads.
3. **phase-3 — gear parity.** The kill3d payload (engine/combat.py) carries
   `worn`/`paths` via the existing `engine/figure3d.sheet()`; render.py
   ships it; fight3d dresses the climber (shield, armor, boots, second
   blade) and swaps the generic lead weapon for the real item GLB. Strike
   keys re-tuned if the real blades misread. Plugin submodule + vendor stay
   in sync.
4. **phase-4 — judgment.** Dojo walkthrough of portrait + finisher + arena,
   results folder, 1bit-images.md learnings, execution statuses.

## Verification

- Per-phase: targeted pytest (`test_071_figure3d.py`, `test_web_play.py`,
  plugin `test_kill3d.py`), `node --check` on touched JS, harness
  screenshots judged by eye (the portrait harness must look UNCHANGED after
  phase 1; the finisher must visibly improve after phase 2/3).
- Final: full worldd + plugin suites, dojo scenarios in
  `worldd/tests/080-shared-player-rig/`, results folder under
  `dojo/results/`.

## Operational notes

- **No branches** (workspace rule) — commit straight to `main`, push
  `origin main`. Plugin changes: submodule first, then vendor copy +
  parent pointer.
- The repo carries other agents' uncommitted WIP — stage ONLY files this
  plan touches, by explicit path.
- `webplay.py` version params bumped every phase that touches fight3d.js /
  figure3d.js / arena3d.js. `lib/*.js` needs no param: static .js ships
  `max-age=60, must-revalidate`. Moved GLBs get new URLs — natural bust.
- Model move = URL change for prod clients mid-deploy; GLBs 404 → both
  scenes already degrade (portrait unhides the PNG, finisher plays the fx
  reel). Acceptable for the 60 s cache window.
- Rollback for every phase: `git revert` of that phase's commit(s); the
  model move in phase 1 is a pure `git mv` and reverts cleanly.
