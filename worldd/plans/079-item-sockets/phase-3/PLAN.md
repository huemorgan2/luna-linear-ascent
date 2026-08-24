# Phase 3 — fight3d on sockets (weapons in hand for the attack scene)

## Goal

`equipTripo()` delegates prop normalization and bone resolution to
`lib/sockets.js` — same axis math, same grip pivots, one source of truth —
while the strike mechanics (the `want` quaternion the swing animates against,
the re-equip on kill replay) stay exactly as they are. Blade and bow read as
held in the hand during the finisher. No visual regression in strikes.

## Steps

1. Import the module in `fight3d.js`; rewrite `equipTripo()` to call
   `normalizeProp` + socket resolution (`hand_r`) and keep constructing its
   neutral-quaternion `want` wrapper on top (world-orientation strikes were
   deliberately tuned per PLAN3/PLAN4 — do not re-space them in this phase).
2. Express the `WEAPONS` len/grip/lift entries as `GRIPS` overrides so both
   scenes read one table; delete the duplicated vertex-pair code.
3. Bump `FIGHT3D_URL ?v=` in `app/webplay.py`; reload uvicorn, `/health`.

## Verification

Scenario `worldd/tests/079-item-sockets/scenario-finisher.md` — fight3d
`test.html`: one blade kill, one bow kill, one staff kill; weapon visibly in
the striking hand through the swing; screenshots. `node --check` both files;
pytest suite green (`test_web_play.py` covers the injection).

## Rollback

`git revert` the phase commit — fight3d returns to its self-contained
`equipTripo`. The module keeps serving figure3d unaffected.

## Execution status (2026-08-24)

DONE — commit `5280347`. equipTripo now calls normalizeProp + resolveBone
(hand_r socket with regex fallback); duplicated vertex-pair code deleted
(−44 lines net). `want` world-orientation strike mechanics untouched.
Verified in the fight3d harness: blade (human), bow (elf), staff (giant)
all ride the striking hand; canvases mount, sequences play. WEAPONS
len/grip/lift stayed local to fight3d rather than merging into GRIPS —
its values are finisher-specific (bigger silhouettes at 320×112) and the
per-frame cancel consumes them differently; folding them in added
indirection without removing a source of truth. FIGHT3D_URL v=13→14.
