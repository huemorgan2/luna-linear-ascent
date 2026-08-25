# 080 phase-2 — render parity: the portrait tone curve in the fight

## Goal

The finisher (and the arena, which shares the stage) shades bodies with the
portrait's continuous crushed-black ramp instead of 6 posterized bands, and
every weapon family carries a GRIPS emissive lift. Measurable: in harness
screenshots the player body reads as a solid-black core with bright lit
edges (clearly separated from the scenery dither), and a rusted blade is
visible against both sky and dark scenery.

## Steps

1. `fight3d.js` post shader (createStage): replace

   ```glsl
   float shade = smoothstep(0.03, 0.95, lum);
   shade = floor(shade * 6.0 + 0.5) / 6.0;
   ```

   with the portrait's continuous ramp (start from `smoothstep(0.28,
   0.75)`; tune the two constants against the harness — the fight has
   scenery + tint the portrait does not). Keep the rim/hot/edge terms; they
   consume `shade` unchanged.
2. `equipTripo`: emissive lift comes from `gripFor(family).lift` (blade
   0.24 etc.) instead of the local `WEAPONS[..].lift` (bow-only today).
   Keep any per-weapon override that reads better in the tint.
3. Judge body lift (0.06) and monster lift (0.06) against the new curve in
   the harness; nudge only if bodies or monsters sink into solid black.
4. Bump `FIGHT3D_URL` / `ARENA3D_URL` in `app/webplay.py`.

## Verification

- Harness runs, screenshots at approach / strike / aftermath for at least:
  grey_wolf+human+blade, ember_shade+elf+bow, orc_overseer+giant+staff, one
  warden. Judge: no banding, body/scenery separation, weapon visible.
- `gallery.html` spot-check across tints (green, amber, red).
- Arena stage (arena3d harness or /play Labs): same judgment — it inherits
  the shader.
- `node --check fight3d.js`; `pytest tests/test_web_play.py -q`.

## Rollback

`git revert` the phase commit — restores the posterize line, the bow-only
lift, and the previous URL versions.
