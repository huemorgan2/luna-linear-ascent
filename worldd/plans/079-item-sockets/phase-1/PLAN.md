# Phase 1 — `static/site/lib/sockets.js`, the shared attachment module

## Goal

One importable module that turns "put this item on that character" into a
single call, with all placement knowledge in two tables (sockets, grips) and
zero scene-specific math. Measurable: figure3d and fight3d can both express
their current attachments through it with no behavior code of their own.

## Steps

1. Create `worldd/static/site/lib/sockets.js` (imports `three` — both host
   pages already map that specifier to the shared vendored build):
   - `SOCKETS`: named anchors → ordered bone-alias lists, covering the shared
     humanoid skeleton of human/elf/giant: `hand_r`, `hand_l`, `forearm_l`,
     `hip_r`, `hip_l`, `back`, `chest`, `neck`, `waist`, `foot_l`, `foot_r`.
     Case-insensitive resolution with fallbacks (today's `pickBone`).
   - `normalizeProp(model, grip)`: modes `long` (farthest-vertex-pair axis →
     +Y, the existing Tripo heuristic), `flat` (thinnest bbox axis → +Z, for
     shields), `none`; grip fraction along the axis; centring on ALL three
     axes (the off-centre-GLB bug found this session); returns a group whose
     origin is the grip point — the pivot convention Tripo assets lack.
   - `attachToSocket({ charRoot, charHeight, bones, socket, prop, grip })`:
     resolves the socket bone, wraps the normalized prop, applies the grip's
     `orient` euler and `offset` vector in **character space** — the frame of
     `charRoot` (x = character's screen-right when faced, y up, z = facing) —
     by cancelling the bone's rotation relative to `charRoot`. Offsets and
     lengths accept proportional units (fraction of `charHeight`) so the
     giant's staff scales with the giant. Returns the wrap for later removal
     (fight3d re-equips between kills).
   - `GRIPS`: per item family (blade, bow, staff, shield, focus, armor,
     boots, charm, potion) → default socket + normalization mode + len +
     grip + orient + offset + emissive lift. Per-item overrides shallow-merge
     on top (the exception hatch).
2. `node --check` the module.

## Verification

- `node --check` passes.
- A scratch import from the figure3d harness resolves the module and lists
  `SOCKETS`/`GRIPS` keys in the console (proves the import map reaches it).

## Rollback

Delete `worldd/static/site/lib/` — nothing imports it yet in this phase.
`git revert` of the phase commit.

## Execution status (2026-08-24)

DONE — commit `df01205`. Module verified in-browser through the harness
import map: all 12 sockets, 12 grip families, 4 functions resolve.
`node --check` clean. One deviation from plan: grip-space frame was
defined as the RIG's frame (+x facing, +y up, +z right hand) rather than
screen frame — the rigs animate facing +x and every scene yaws them, so
screen-frame tunings would break per stage.
