# 3d-fight — side-view fight scenes: animated 1-bit backgrounds + live 3D combatants

Research question: can a fight screen be staged like the content event
photos — a 1-bit scene image — but **alive**? A softly animated 1-bit
background GIF per encounter, with the player and the monster as real
3D models (three.js) rendered down to 1-bit and standing on the scene's
floor, breathing.

Scope: floor 1 only (The Fencerows, 7 fights from
`plugin-linear-ascent/plans/049-monster-image-remake/MONSTERS.md`).
Everything lives in this folder; nothing ships.

## Two layers, one pixel grid

Master grid **480x270** (16:9), displayed at 2x with
`image-rendering: pixelated`. Both layers use the same 8x8 Bayer
matrix as `tools/generate_banners.py`, so they dither as one image.

### Layer 1 — background GIF (`demo1/gen_backgrounds.py`)

Per fight, following `plugin-linear-ascent/vision/1bit-images.md`
(headline lesson — the model designs the dither, we only enforce the
grid):

1. nano-banana-pro renders the fight's scene as designed 1-bit dither
   art — **empty stage**: no creatures, no people, a flat clear ground
   band across the full width of the lower quarter (the fighting
   floor), side-on theater-stage view, glow gradients from every light
   source.
2. Grid enforcement: crop 16:9 → LANCZOS 480x270 → autocontrast →
   the greyscale *density master*.
3. Procedural loop animation (24 frames, 100 ms, perfect loop) on the
   density master, then fixed-grid Bayer per frame:
   - **wind** — sinusoidal horizontal displacement above the floor
     line, amplitude growing with height (hedges/grass sway ~1–2 px)
   - **glow pulse** — bright regions (floodlights, windows) breathe
     ±8% on a slow sine
   - **fire flicker** — scenes with fire get band-limited noise added
     in the glow mask, cyclically blended so the loop closes
   The Bayer grid stays fixed, so untouched pixels do not boil; only
   what moves shimmers. (Veo image-to-video + per-frame re-dither is
   the alternative from 1bit-images.md — richer motion, but does not
   loop, costs a model call per take, and boils everywhere. Procedural
   wins for an idle fight loop.)

### Layer 2 — 3D combatants (`demo1/fight.js`)

Same approach as `base-mock/threejs` (which proved 3D + shader filter
carries the 1-bit look): render into a 480x270 buffer, post pass does
sobel ink outlines over depth+normal buffers + Bayer dither. New here:
the buffer is **transparent** — only character (and dithered contact
shadow) pixels are opaque, so the canvas overlays the GIF exactly.

- Side view: orthographic camera on +Z; player left facing right,
  monster right facing left, feet on the background's floor line.
- One strong key light models the volume (the closeup lesson: lit side
  dense white dither, shadow side black, dark contour from the sobel
  edge) + dithered contact shadow via a ShadowMaterial catcher.
- Player: KayKit Knight rig (CC0, vendored from base-mock) with the
  1-handed sword on `handslot.r`, playing its `Idle` clip.
- Monsters: goblin = KayKit Rogue_Hooded scaled down; the animals
  (wolf, boar, rat, pack dogs) are procedural quadrupeds grown from
  the base-mock beast builder with breathing/head-bob/tail idle;
  hedge-wight and Warden Brackjaw are procedural builds (blackthorn
  man-shape sway; armored wolf frame with servo tick).
- Free animated sources for later passes: KayKit adventurers pack
  (done), Quaternius Ultimate Animated Animals (CC0 — proper wolf/
  boar/rat rigs), poly.pizza mirrors. demo1 stays procedural to prove
  the pipeline without new downloads.

## Demo

`demo1/index.html` — fight picker, background GIF `<img>` with the
character canvas layered on top, per-fight floor-line/scale config.

```bash
cd research/3d-fight/demo1 && python3 -m http.server 8998
# open http://localhost:8998/
```

Regenerate backgrounds (key: LUNA_GEMINI_API_KEY, falls back to
luna/.env):

```bash
worldd/.venv/bin/python research/3d-fight/demo1/gen_backgrounds.py stills   # model calls
worldd/.venv/bin/python research/3d-fight/demo1/gen_backgrounds.py gifs     # local only
```

## Open questions

- ~40 px combatants on the game's native 320x112 banner grid — does
  the 3D layer still read at that size, or is the fight screen its own
  taller grid (this demo's 480x270)?
- Quaternius animal rigs vs procedural: worth the asset weight?
- Sync: should background glow pulse and character breathing share a
  clock so hits can flash the floodlights?
