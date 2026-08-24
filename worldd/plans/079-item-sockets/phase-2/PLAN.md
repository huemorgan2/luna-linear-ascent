# Phase 2 — figure3d on sockets + grip-illusion tuning

## Goal

The portrait scene expresses every attachment through the module, and the
four reported defects are gone: (a) the giant's staff stands in his fist,
clearly in front of / beside his silhouette — not laid on the body; (b) the
shield hangs OUTSIDE the left forearm; (c) swords hang hilt-at-palm-line on
the hip opposite the shield; (d) the bow sits diagonally on the back.
Measurable at 4× zoom per race.

## Steps

1. Replace `figure3d.js`'s `HOLD`, `wrapProp`, `attach`, `pickBone` with
   imports from `../lib/sockets.js`; keep the slot→family mapping and the
   hover-tint tagging where they are.
2. Move this session's tunings into `GRIPS` as character-space values, then
   fix the four defects by adjusting table values only (that's the point):
   - staff: socket `hand_r`, planted vertical, offset outward+forward in
     character space so the shaft crosses the fist volume, not the torso;
     length proportional to body height (the giant's staff towers with him).
   - shield: socket `forearm_l`, flat mode, offset outward (character +x)
     past the arm silhouette.
   - blade: socket `hip_r` (opposite the shield), near-vertical hang, hilt
     at palm height.
   - bow: socket `back`, the existing diagonal.
3. Update the header comment + README (imports lib/, still fight3d-free).
4. Keep `?fig3ddebug` introspection working (it reads the lives map only).
5. Restart/reload local uvicorn, hit `/health`, bump `FIGURE3D_URL ?v=`.

## Verification

Scenario `worldd/tests/079-item-sockets/scenario-portrait.md` — all three
races at zoom, judged on the four defects, screenshots saved. `node --check`
+ full pytest suite green.

## Rollback

`git revert` the phase commit — figure3d returns to the pre-socket ad-hoc
`HOLD` table (which renders, with the known defects).

## Execution status (2026-08-24)

DONE — commit `af70fcc`. HOLD/wrapProp/attach/pickBone deleted (−179
lines), placement is GRIPS table rows. All four defects verified fixed at
4× zoom (dojo run 0049): staff vertical through the giant's fist inside
the frame, buckler face-on outside the forearm, swords hilt-at-palm on
the right hip, bow diagonal on the back. Hover tint + restore intact.
FIGURE3D_URL bumped v=8→9 (landed with phase-3 commit). Iterations
during tuning: flat-mode shields need +π/2 yaw in grip space; blade
lean sign flipped to hang outward; staff tucked z −0.045→−0.120.
Pre-existing failure filed: test_leaderboard_marks_only_you (fails at
clean HEAD, unrelated).
