# 080 phase-3 — gear parity: the climber fights in their own gear

## Goal

The kill finisher shows the climber wearing what they actually wear: real
lead-weapon GLB (not the generic placeholder), shield, armor, boots, and a
second blade, dressed through the same GRIPS placements as the portrait.
Measurable: a climber with `iron_sword` + `gate_buckler` shows exactly
those models in the finisher; the three generic weapon GLBs are deleted.

## Steps

1. Server payload (plugin submodule `plugin-linear-ascent`, then rsync to
   `worldd/vendor/plugin_linear_ascent`, commits in both, submodule pointer
   bump):
   - `engine/combat.py`: the kill3d dict gains `worn` and `paths` from
     `engine.figure3d.sheet(p)` (already computes them; reuse, do not
     duplicate). Keep the payload small: drop empty slots.
   - `render.py`: `data-rig3d` grows a third field with the worn slugs the
     climber carries (`race:line:slug1+slug2+…`) so `warmFor` can prefetch
     the item GLBs during the fight, before the kill card lands.
   - Plugin tests: extend `test_kill3d.py` for the new fields (and record
     the pre-existing baseline failures before touching anything).
2. `fight3d.js`:
   - `ensureFor`/`warmFor`: parse gear slugs, load item GLBs from
     `lib/models/items/` with the family-GLB fallback chain.
   - Lead weapon: `equipTripo` keeps its want-quaternion strike mechanics
     but loads the REAL item GLB for the climber's weapon slug (fallback:
     family GLB). `WEAPONS.len/grip` stay as the normalization inputs.
   - Other slots: dress via `character.dressFigure` with
     `skip: ["charm", "potion"]` (too small to read at 320×112) and the
     lead-weapon slot excluded (equipTripo owns it).
   - DELETE `static/site/fight3d/players/{blade,bow,staff}.glb`; the
     family fallbacks now come from `lib/models/items/{blade,bow,staff}.glb`.
3. Strike pass: run all four STRIKES against real swords in the harness;
   re-tune keyframe `d`/`lg` values only if a real blade misreads (clipping
   the body, invisible at impact).
4. Bump `FIGHT3D_URL` / `ARENA3D_URL`; version.py bump in the plugin per
   its release convention if one applies.

## Verification

- Plugin: `pytest tests/test_kill3d.py -q` (new fields), then full plugin
  suite — no NEW failures vs the recorded baseline.
- worldd: `pytest tests/test_web_play.py -q`; `node --check fight3d.js`.
- Harness with a spec carrying worn gear: climber visibly wears shield +
  armor + real sword through approach, strike, and aftermath; nothing
  detaches or lags a bone. All three races.
- Degrade: a spec with a bogus slug still plays (family fallback), and a
  missing monster GLB still falls back to the GIF reel.

## Rollback

`git revert` the worldd commit AND the plugin commit (both repos), restore
the three placeholder GLBs (the revert brings them back), rsync vendor from
the reverted submodule, bump the submodule pointer back.
