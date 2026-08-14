# 3d models — Tripo3D-generated player characters + weapons

Generates the game's player matrix (`giant | elf | human` ×
`blade | bow | staff`, from ../PLAN2.md) with the Tripo3D API instead of
stock CC0 rigs, then shows them breathing in live 1-bit dither.

Pipeline per character (roy's website recipe, automated):
text→model at 2000 faces → texture (prompted for the 1-bit look per
`plugin-linear-ascent/vision/1bit-images.md`: flat regions, strong tonal
separation, no micro-texture) → auto-rig (biped, mixamo names) →
retarget `preset:biped:idle` (the breathing stance). Weapons stop after
texture; the viewer attaches them to the right-hand bone.

## Run

```bash
# generate (resumable — task ids in models/manifest.json)
python3 "research/3d-fight/3d models/gen_models.py"
python3 "research/3d-fight/3d models/gen_models.py" status
python3 "research/3d-fight/3d models/gen_models.py" giant blade   # subset

# view (serve from 3d-fight so ../demo2/vendor/three.module.js resolves)
cd research/3d-fight && python3 -m http.server 8997
# open http://localhost:8997/3d%20models/
```

Key: `.env` here (`TRIPO_API_KEY=…`, gitignored) or env var.

All 6 assets are generated (2026-08-13, ~185 credits, balance ~4300).
Note: Tripo bills API credits separately from tripo3d.ai web credits —
an empty API wallet gives error 2010 on every task. Failed/cancelled
tasks are refunded.

## Viewer notes

- Falls back gracefully: idle → rigged → textured → base glb; if no rig
  yet, procedural breathing (gentle y-scale sine) stands in.
- Same look as demo2: 8×8 Bayer, 4-step luminance quantize, near-side
  depth ink, dithered contact shadow. Buffer 200×240 @2x.
- Normalize bbox is measured on the ANIMATED pose (mixer settled one
  frame) — the rest pose of Tripo retarget glbs differs from the idle.
- Weapon `rot`/`pos` in WEAPONS are WORLD-space; the frame loop cancels
  the live hand-bone rotation every tick (equip-time compensation isn't
  enough — each rig's idle twists the wrist differently) so one setting
  fits all three characters. `lift` adds flat emissive for props Tripo
  textures too dark for the dither (the bow's near-black limbs).
  Tune live in the console:
  `fx.grip(null, "blade", {rot: [0,0,-0.9], grip: 0.2})`,
  `fx.bones("elf")` lists bone names.
- `fat` thickens a prop transversely (long axis untouched). Needed for
  the blade and bow: the post shader inks every pixel whose neighbour is
  much deeper, so geometry only 1–2 buffer pixels wide is ALL edge and
  renders pure black — invisible. Fat, chunky props survive (and suit
  the pixel-art look anyway).
- Click a canvas to attack: plays `40_slash` / `41_shoot` / `42_cast`
  (matched to the equipped weapon) once at 1.5× speed, crossfades back
  to idle. The clips bind to the 30_idle skeleton by bone name; the
  per-frame weapon lock is released during the swing so the weapon rides
  the hand. Weapon scale is `len / nlen / handBoneWorldScale` — the bone
  scale already contains the model's normalize factor, so don't multiply
  by it again (that was the 2×-oversized-staff bug).
