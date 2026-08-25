# 083 — props wear their own proportions (portrait gear fixes)

## Problem

Roy's live profile (huemorgan, elf blade, 2026-08-25 screenshots): the
Notched Cleaver renders as a huge slab floating at the hip — wrong size,
not reading as held — and the shield-slot item (purple hover ink) renders
as a ball floating beside the forearm instead of a shield on the arm.

Reproduced locally in the figure3d harness (elf + notched_cleaver /
wolfsteel_broadsword + gate_buckler, injected specs, screenshots in the
083 dojo results). Reproduction also surfaced a third bug: mounting two
same-race figures on one page leaves all but the last BLACK — the shared
`gltf.scene` is re-parented by `Group.add()`, so the last mount steals the
body.

Measured evidence (bbox of every item GLB, `lib/models/items/`):

- `notched_cleaver` 0.13×1.00×0.45 — its blade is 45% as wide as it is
  long. `GRIPS.blade.len: 0.55` scales the LONG axis to 55% of body height
  with no width constraint → the width blows up to ~25% of body height.
  Same class of misfit: `rusted_shiv` (0.53×1.0×0.91), `wolfsteel_broadsword`
  (0.44×1.0×0.54), `scrap_dagger`, `ratcatchers_dirk`, `gatewatch_gladius`.
- bucklers are DOMED: `gate_buckler` 0.64×1.0×0.99 (depth 64% of diameter).
  Flat-mode mounts the thin axis out, but the orient yaw (1.12) turns the
  dome at the camera and the depth pokes past the arm → floating ball.
- the body-theft bug: plan 080 unified both scenes' loader caches; the
  pre-080 figure3d had its own cache, so two same-race stages never shared
  a scene object before. Now `buildRig` hands every same-race stage the
  same `gltf.scene`.

## Root cause

1. Prop sizing is one-dimensional: `attachToSocket` scales by normalized
   LENGTH only (`grip.len · charHeight / nlen`). Squat items keep their
   aspect and balloon.
2. Domed shields: orientation tuned on flat discs; no depth handling.
3. Player bodies are shared scene objects across stages since 080 —
   `THREE.Object3D.add()` re-parents, silently unmounting the previous
   stage's body.

## Emergency mitigation

None — live but cosmetic (bug 3 does not trigger on /play today: one
portrait per page).

## Fix — one phase

1. **Width-aware sizing** (`lib/sockets.js`): normalizeProp returns the
   normalized bbox; attachToSocket scales by
   `min(len·H/nlen, maxw·H/nwid)`. New per-family `maxw` in GRIPS
   (fractions of char height): blade/blade_l 0.13, staff/staff_back 0.11,
   focus 0.10, charm 0.07, potion 0.09; shields cap DEPTH instead
   (`maxd` ≈ 0.10) since their width IS the design size.
2. **Shield reads as a shield**: retune `GRIPS.shield` orient/offset in
   the harness with the domed bucklers until the piece hugs the forearm
   and shows a rim-lit quarter profile, not a ball.
3. **Stop sharing bodies** (`lib/character.js`): vendor three's
   `SkeletonUtils.clone` into `lib/vendor/`; `buildRig` clones the cached
   `gltf.scene` per stage (skinned-safe clone; plain `.clone()` severs
   skeletons, which is why 080 shared). Prop GLBs stay cloned as before.
4. Bump `FIGURE3D_URL` / `FIGHT3D_URL` / `ARENA3D_URL` in webplay.py.

## Verification

- Harness: elf with notched_cleaver + gate_buckler + studded_jack, plus
  rusted_shiv / wolfsteel_broadsword variants, plus THREE same-race
  figures side by side (body-theft regression). Screenshots judged by eye:
  cleaver hand-scale and gripped, shield on the arm, all bodies present.
- The three dojo-0051 loadouts re-render unchanged (sword/bow/staff are
  slender — width cap must not touch them).
- `node --check` on touched JS; `pytest tests/test_web_play.py
  tests/test_071_figure3d.py -q`.
- Live after deploy: huemorgan's profile shows a hand-sized cleaver and a
  shield that reads as one.

## Rollback

`git revert` the phase commit; URL params revert with it.

## Operational notes

- No branches; commit to `main`, push, deploy via `worldd/tools/deploy.sh`.
- Client-only (JS + webplay version params) — no plugin/vendor sync.
- Repo carries other agents' WIP — stage only this plan's files.

## Execution status

Executed 2026-08-25, commit 4ea13bd (plan committed first at 14e0418 as
081, renumbered — another agent's 081-early-game-smoothing landed
between).

- **Width cap evolved during execution.** The planned bbox-width `maxw`
  shrank `rusted_sword` to a dagger: its bbox is squat only because of a
  wide crossguard + diagonal authoring. Replaced with `girth` — an RMS
  cross-section radius cap, mass-weighted so thin crossguards don't
  register. Measured separation: slender swords/staves 0.035–0.061
  rms/len, notched_cleaver 0.113, ratcatchers_dirk 0.143. `girth: 0.035`
  on blades, `0.040` on staves; charm/potion/focus caps dropped as
  unneeded.
- **Shield `maxd` evolved into `squashd`.** A depth CAP shrank the whole
  buckler; and single-frame tuning was misleading — the idle twists the
  forearm, so a domed buckler flip-flops between ball (face-on) and
  sliver (edge-on). `squashd: 0.30` non-uniformly crushes the dome to a
  disc; retuned `len 0.16, orient [0, 0.90, −0.15], offset
  [0.030, −0.055, −0.030]` straps it flush. Verified across four
  animation phases.
- **Body clones (as planned):** `lib/vendor/SkeletonUtils.js` vendored;
  `buildRig` clones per stage; fight3d `buildPlayer` consumes the
  returned clone (dead `weaponWrap` bookkeeping removed). The fight's
  lead-weapon path `equipTripo` got the same girth cap (charH passed in).
- **Verification:** dojo run 0052 (all PASS, screenshots);
  `test_web_play.py` + `test_071_figure3d.py` 16 passed; `node --check`
  on all touched JS. URLs bumped: fight3d v18, arena3d v8, figure3d v11.
