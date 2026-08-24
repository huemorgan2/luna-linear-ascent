# 079 — Item sockets: one attachment system for both 3D scenes

## Problem

Evidence (2026-08-24, figure3d harness screenshots + live-scene bbox dumps):

- The giant's staff floated at the frame edge, detached from his hand; after
  ad-hoc fixes it now lies against his body instead of standing gripped in
  his fist.
- The shield mounted like a cylinder (long-axis normalization picks a random
  diameter of a disc) and now hangs INSIDE the forearm line, clipping the arm.
- The human's sword was invisible for two separate reasons (hidden behind the
  shield-side thigh; rendered below the crushed-black tone cutoff) — each
  found only by pixel-hunting.
- Every fix is a hand-tuned bone-local euler/offset in `figure3d.js` `HOLD`,
  duplicated in spirit by `fight3d.js` `WEAPONS` + `equipTripo()`. The two
  scenes share no code. Tunings broke wholesale when the portrait turned
  from ¾ profile to front-facing, because bone-local axes are unpredictable
  per joint.

More items and wearables are coming; the attack scene needs the same
placement. Per-item-per-scene guessing does not scale.

## Root cause

Our Tripo GLBs violate the pivot convention every engine assumes (item origin
at the grip, agreed axes), and we compensate in scattered per-scene constants
expressed in the wrong space (bone-local). The industry answer is **skeletal
sockets** (Unreal) / mount points (Unity): named anchors on the skeleton,
tuned once, plus per-item grip normalization. We have neither; this plan adds
both as a shared module.

Constraint discovered during tracking: **the rigs have no finger bones**
(verified via live-scene traversal — hands are baked open-palm meshes). So
"the hand grips the sword" is achieved the way low-poly games do it: the
shaft is aligned along the palm line through the fist volume, tuned per
socket, and judged visually at zoom. No finger posing is possible without
re-rigged assets.

## Emergency mitigation already taken

None needed — Labs-only surface (071 portrait) plus the fight finisher;
nothing is data-affecting. Ad-hoc fixes from this session stay in place until
Phase 2 replaces them.

## Fix (phases)

1. **phase-1** — shared module `static/site/lib/sockets.js`: SOCKETS table
   (named anchors → bone aliases, character-space offsets scaled to body
   height), prop normalization (long-axis / flat / none + grip fraction +
   full 3-axis centring), `attachToSocket()` applying orientation and offset
   in **character space** (the figure's facing frame, not world, not bone).
2. **phase-2** — figure3d adopts it: `HOLD`/`attach`/`wrapProp` replaced;
   grip-illusion tuning per socket (staff standing in the giant's fist and
   clear of his silhouette, shield outside the forearm, sword hilt at the
   palm line, bow on the back).
3. **phase-3** — fight3d adopts it: `equipTripo()` delegates normalization
   and socket resolution to the module, keeping its strike-swing quaternion
   mechanics; bow-in-hand and blade-in-hand verified in the finisher.
4. **phase-4** — E2E judgment run (scenarios in `worldd/tests/079-item-sockets/`),
   results folder, learnings appended to `plugin-linear-ascent/vision/1bit-images.md`.

## Verification

- `node --check` on every touched JS file; full `pytest worldd/tests` stays
  green (webplay serves the module; no Python behavior change expected).
- Harness walkthroughs (the scenario files): figure3d test.html at zoom for
  all three races — sword hilt in the palm line / on the correct hip, bow on
  the back, staff standing in the giant's fist in front of the body, shield
  outside the forearm; fight3d test.html — blade and bow strikes still land
  with weapons in hand.
- Screenshot evidence for every verdict.

## Operational notes

- No branches (workspace rule) — commit to `main`, plan committed before
  execution.
- Cache: bump `FIGURE3D_URL`/`FIGHT3D_URL` `?v=` in `app/webplay.py` when
  shipping so /play picks up the new modules.
- figure3d's "isolated folder" note in its header/README must be updated: it
  now imports `../lib/sockets.js` (still never imports fight3d).
- Rollback for every phase is `git revert` of that phase's commit; no data,
  no schema, no state.
