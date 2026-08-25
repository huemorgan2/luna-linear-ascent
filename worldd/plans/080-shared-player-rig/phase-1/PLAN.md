# 080 phase-1 — one rig pipeline, canonical models

## Goal

Both 3D scenes load the SAME player GLBs from one folder and build bodies
through ONE shared module, with zero visual change. Measurable: md5-equal
duplicate GLBs are gone from the repo; `figure3d.js` and `fight3d.js` no
longer contain their own settle/normalize/boneMap body code; portrait and
finisher harnesses render as before (eye judgment on screenshots).

## Steps

1. Canonical assets (git mv, parent repo):
   - `static/site/figure3d/models/players/*.glb` → `static/site/lib/models/players/`
   - `static/site/figure3d/models/items/*.glb`  → `static/site/lib/models/items/`
   - `static/site/fight3d/players/{human,elf,giant}_{cast,shoot,slash}.glb`
     → `static/site/lib/models/players/` (strike-clip GLBs are player rig
     assets)
   - DELETE `static/site/fight3d/players/{human,elf,giant}.glb`
     (byte-identical duplicates of the figure3d bodies).
   - `static/site/fight3d/players/{blade,bow,staff}.glb` STAY until phase 3
     retires them.
   - `figure3d/vendor/GLTFLoader.js` + `fight3d/vendor/GLTFLoader.js`
     (byte-identical) → one `static/site/lib/vendor/GLTFLoader.js`;
     `three.module.js` stays in fight3d/vendor (the import map's target).
2. New `static/site/lib/character.js`, importing only `three` and
   `./sockets.js`:
   - `load(rel)` — cached GLTF loader resolving against `lib/models/`.
   - `shadowify(o)`.
   - `buildRig({ gltf, height })` → `{ model, mixer, B, k }`: play
     clip 0 / settle 0.033 s, idempotent normalize against cached
     `src.userData.dims` (fight3d's stricter discipline — never clone a
     skinned scene), boneMap.
   - `prepProp(src, { lift, liftFn })` — clone(true), shadowify, emissive
     lift; `liftFn` hook lets figure3d keep its greyscale + hover
     bookkeeping.
   - `dressFigure({ fig, worn, paths, skip, equipFn })` — the slot loop
     from figure3d.buildFigure (blade/blade_l, staff/staff_back,
     shield/focus, armor, boots_l/r, charm/potion) with a skip list, prop
     GLB fallback chain (own slug → family GLB → placeholder).
3. Port `figure3d.js`: body code in `buildFigure` → `buildRig`; the worn
   loop → `dressFigure` (equipFn keeps liftMesh/tagSlot); model URLs →
   lib. Keep stage, shader, hover, mount lifecycle untouched.
4. Port `fight3d.js`: `buildPlayer` body code → `buildRig`; player + clip
   GLB paths → lib loader. `equipTripo`, gait, strikes, monsters
   untouched. `warmFor` warms the lib URLs.
5. Bump `FIGURE3D_URL` / `FIGHT3D_URL` / `ARENA3D_URL` versions in
   `app/webplay.py`. Update the two scene READMEs' isolation notes and the
   figure3d/fight3d test harnesses if they reference moved paths.

## Verification

- `node --check` on figure3d.js, fight3d.js, lib/character.js.
- `pytest tests/test_071_figure3d.py tests/test_web_play.py -q` green (fix
  any moved-path assertions).
- Portrait harness `figure3d/test.html`: all three races + gear render
  exactly as before (screenshot vs pre-change screenshot, eye judgment).
- Finisher harness `fight3d/test.html?id=grey_wolf&race=human&line=blade`:
  sequence plays, weapon in hand, no console errors.
- `rg "models/players|models/items" static/site` shows only lib paths (plus
  the three placeholder weapons in fight3d).

## Rollback

`git revert` the phase commit — the asset move is `git mv` and reverts to
the original paths; webplay version params revert with it.
