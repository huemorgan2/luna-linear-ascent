# 3d-fight demo2 — game-exact frame, real rigs, player + weapon selection

demo1 proved the pipeline (animated 1-bit background GIF + live three.js
combatants dithered on top). demo2 makes it match the game:

1. **Exact event resolution: 320x112** — the size of every event GIF in
   `content/art/events/` (1196 art files use it). Displayed @3x (960x336),
   `image-rendering: pixelated`, same shared 8x8 Bayer grid.
2. **Real rigged characters, not toons** — Quaternius *Universal Base
   Characters* + *Modular Character Outfits – Fantasy* (CC0, realistic
   proportions, low-poly), animated by the *Universal Animation Library*
   (43 clips; same UE-style skeleton, 66/66 bone names match — clips
   drive the dressed characters directly).
3. **Floor 1 fidelity + loadout choice** — backgrounds prompted from
   `content/floors/floor_001.yaml` (The Fencerows), and the exact
   species/weapon matrix the game already uses in event art:
   species `elf | giant | human`, weapon `blade | bow | staff`.

## Casting (free tier, executed)

| Game species | Recipe |
|---|---|
| giant (dwarf-look) | Superhero_Male base + Peasant outfit + Hair_Beard, scaled wide+tall (stocky mass) |
| elf (male) | Superhero_Male base + Ranger outfit (hood down) + Hair_Long + pointed ears on the head bone, slim scale |
| human (woman fighter) | Superhero_Female base + Ranger outfit + pauldrons + Hair_Buns |

Weapon loadouts (attach to `hand_r` / `hand_l` bones):

| Weapon | Prop | Idle clip |
|---|---|---|
| blade | KayKit sword_1handed (CC0, vendored) | `Sword_Idle` (+`Sword_Attack` available) |
| staff | KayKit staff (CC0, vendored) | `Spell_Simple_Idle_Loop` (+cast clips) |
| bow | Quaternius Bow_Wooden (CC0) | `Idle_Loop` (archery clips are in UAL **Pro** — see vendors) |

Monsters stay demo1's procedural builds (wolf, boar, rat, pack,
hedge-wight, warden) + KayKit hooded goblin; no free non-toon animal
rigs found (Quaternius' free animal packs have no wolf/boar/rat).

## Vendor survey (paid options roy can buy)

**Best fit — Quaternius Pro/Source via [Patreon](https://www.patreon.com/quaternius)
($10 Silver / $20 Gold per month, each month = 1–2 Source keys):**
- [Universal Base Characters](https://quaternius.com/packs/universalbasecharacters.html)
  Pro: adds Regular + Teen body types (male/female).
- [Modular Character Outfits – Fantasy](https://quaternius.com/packs/modularcharacteroutfitsfantasy.html)
  Pro: all 12 outfits / 62 parts (armor sets for the woman fighter,
  mage robes) — free tier ships only Peasant + Ranger.
- [Universal Animation Library](https://quaternius.com/packs/universalanimationlibrary.html)
  Pro: 120+ clips incl. **bow/archery** — drops straight into demo2
  (same skeleton, zero code change beyond a clip name).
- [Ultimate Animated Animal Pack](https://quaternius.com/packs/ultimateanimatedanimals.html):
  rigged animated wolf/boar-class animals to replace procedural monsters.

**Sketchfab Store** (GLB, works in three.js as-is):
- [Female Warrior — fantasy game character](https://sketchfab.com/3d-models/female-warrior-fantasy-3d-game-character-6a99947157974611991716447f8d308a)
  (Aloya Studio) — facial rig + 50-animation sword pack.
- [Stylized RPG character, rigged & animated](https://sketchfab.com/3d-models/character-stylized-rpg-fantasy-rigged-animated-1e4409c5ff544d6a8c35b0a98b06fb0c)
  (LuxorGrey) — 50+ animations.
- Search [rigged-character](https://sketchfab.com/tags/rigged-character) /
  [elf](https://sketchfab.com/tags/elf); typical $15–60 per character.

**One-off marketplaces:** [CGTrader rigged dwarfs](https://www.cgtrader.com/rigged-3d-models/dwarf),
[elves](https://www.cgtrader.com/3d-models/elf), TurboSquid, Fab (Epic) —
$20–150/model; check "animated" + FBX/GLB before buying.

**Mixamo (free, Adobe login):** upload any humanoid (including a bought
dwarf/elf) → auto-rig + hundreds of clips (has archery). Manual browser
flow only; good for one-time animation baking.

At 320x112 a character is ~55 px tall — silhouette and proportion are
everything, surface detail is invisible. Quaternius-grade low-poly with
real proportions is exactly enough; high-poly marketplace models buy
nothing at this res except heavier files.

## Pipeline changes vs demo1

- Backgrounds: same designed-dither → density-master → procedural loop
  (wind / glow pulse / fire flicker, fixed Bayer), but generated at
  **21:9** (closest supported aspect to 320:112) and center-cropped to
  the 320x112 master grid. Prompts now cite the floor_001.yaml arrival
  + encounter prose. `demo2/gen_backgrounds.py stills|gifs`.
- Stage: same transparent post pass (depth+normal ink, halo ring,
  Bayer), buffer 320x112, camera framed so a human is ~55 px.
- Character build: load base gltf, graft outfit/hair skinned meshes onto
  the base skeleton by bone name (`mesh.bind(new Skeleton(...))`),
  play UAL clips on the base mixer. Species = base+outfit+hair+scale;
  weapon = prop on hand bone + idle clip. UI: fight tabs × species ×
  weapon.

## Run

```bash
cd research/3d-fight/demo2 && python3 -m http.server 8999
# open http://localhost:8999/
```

Regenerate backgrounds:

```bash
worldd/.venv/bin/python research/3d-fight/demo2/gen_backgrounds.py stills
worldd/.venv/bin/python research/3d-fight/demo2/gen_backgrounds.py gifs
```

## Open questions

- Buy Quaternius Pro (UAL Pro archery + 12 fantasy outfits + animal
  rigs)? Cheapest complete upgrade (~$10–20 once).
- Hit/attack choreography: `Sword_Attack`, `Spell_Simple_Shoot`,
  `Hit_Chest`, `Death01` are already in the free library — wire a
  "resolve round" button next?
- Do event GIFs and this live stage share enough look to swap in-game?

## Update 2026-08-13 — demo2 rebuilt at 640x224

320x112 was too coarse for live-rendered combatants (~55 px tall,
detail unreadable). demo2 now runs **640x224** — exactly 2x the event
grid, same 20:7 aspect, displayed @2x (1280x448, pixelated). Camera
zoomed (ortho view height 2.8): human ~138 px, giant ~164 px.
Backgrounds regenerated with the shipped banner prompt discipline
(tools/generate_banners.py STYLE verbatim): the model paints designed
gradients, the local Bayer pass owns the dither. Asking the model for
"chunky dither pixels" was the mush source — painted dither downscales
to mid-density noise. Bow moved to hand_r rot [0, pi/2, 0] (hand_l is
the occluded far-side hand). Goblin is now a rigged fighter (base_m +
peasant outfit, cone ears, sword, Sword_Idle) instead of the KayKit
hooded blob.

## Update 2026-08-13 — back at 320x112; infected/liberated monsters
- 640x224 abandoned; stage is 320x112 @4x again, per 1bit-images.md.
- Ink is now 1px near-side depth edge only (no halo contour pass).
- Every monster has two forms: INFECTED (large, dark dither 0x565d6e,
  black aether-thorns over the back) and LIBERATED (small, near-white
  natural animal). Thorns sit in wrap space against the scaled bbox —
  the animal armature bone scales are broken (same trap as
  SkeletonUtils.clone), and bind-pose dims are cached per asset because
  re-measuring after the mixer has run collapses Box3 to centimeters.
- LIBERATE button runs the fight: blade = dash + Sword_Attack,
  bow = Pistol_Shoot aim + white arrow (UAL has no bow clip),
  staff = Spell_Simple_Shoot + thick white beam w/ ink border; impact =
  white spark burst + expanding ring, infected form shrinks away, the
  small natural animal pops in. `window.fx.liberate()` headless.

## Update 2026-08-13 — Tripo3D players wired into demo2
- Players are now the "3d models" Tripo characters (giant/elf/human
  30_idle.glb) + Tripo weapon props (blade/bow/staff 10_textured.glb),
  copied into demo2/assets/tripo/ (the :8999 root can't reach the
  sibling folder). Quaternius base+outfit players removed; base_m /
  peasant / UAL / KayKit sword stay only for the goblin & wight rigs.
- Equip logic ported from the 3d-models viewer: long axis from the
  farthest vertex pair -> +Y, grip-fraction origin, world-metre length,
  bone-scale cancel, and a per-frame live hand-bone rotation cancel so
  one WORLD-space rot/pos fits all three rigs. Bow keeps lift 0.30.
- Normalize measures the ANIMATED pose (mixer settled one frame),
  cached in src.userData.dims — same trap as the animals.
- Post shader: player-friendly quantize from the viewer (perceptual
  luminance, gamma 0.4545, smoothstep 0.03–0.95, 6 steps). INK dropped
  0x565d6e -> 0x33384a to keep infected monsters dense under the lift;
  players additionally get flat emissive 0.18 (Tripo bakes dark tones).
- Strike clips: gen_clips.py fetches Tripo retarget presets onto each
  character's rig task (rig v1.0-20240301, 10 credits/clip):
  slash = preset:biped:slash, shoot = preset:biped:shoot,
  cast = preset:biped:cast_a_spell -> models/<c>/40_<k>.glb, copied to
  demo2/assets/tripo/<c>_<k>.glb. demo2 extracts just the
  AnimationClip (same mixamo skeleton) and plays it in liberate();
  impact fires at clip midpoint. During a strike the per-frame wrist
  cancel PAUSES so the weapon swings with the hand instead of staying
  world-locked. Missing clip files fall back to the procedural dash.

Update 2026-08-13 — low-key rim look (the reference-image shading)
- Players now sit in dark atmospheric dither with a near-white sliver
  on the monster-facing outline (classic low-key: kicker brighter than
  key). Ambient 0.24, key 1.6 at (-6,9,12), kicker 10.0 at (9,5,-3).
  Player flat emissive lift dropped 0.18 -> 0.06.
- PLAYER_YAW = 1.05 — players turned to a 3/4 view facing the monster
  (was full profile PI/2).
- The sliver itself is shader work, not just lighting: the 1px depth
  ink was overwriting every silhouette pixel, so no rim could survive.
  Fix in the post shader: a MeshNormalMaterial pass now fills rtNormal
  each frame (it was allocated but never rendered), and contour pixels
  whose view-space normal faces the monster (n.x > 0.30) render solid
  white instead of ink; fully saturated pixels (shade >= 0.99) also
  punch through. Everything else on the contour stays dark ink.

Update 2026-08-14 — scale fix, split light, charge choreo, real fx
- Weapon scale bug: equipTripo multiplied wp.len by the character
  normalize k, but the hand bone's world scale already contains k —
  weapons rendered ~1.8x spec (staff 2.49 m vs 1.45). Dropped the k;
  wp.len is now true world metres (verified via fx.probePlayer()).
- Split shading: key moved to the MONSTER side (6.0 at (10,6,3)),
  ambient 0.18 — the facing half of the body is lit, the camera half
  falls to sparse dark dither, kicker sliver unchanged.
- Bow: the Tripo shoot preset crouched and twisted, dropped. Hand-keyed
  draw instead — world-space aimBone() (setFromUnitVectors on the live
  bone chain, weight-slerped) extends the right arm at the monster and
  pulls the left elbow straight back to the cheek; release() lets go
  at the arrow. No local bone axes guessed, works on all three rigs.
- Charge choreography: LIBERATE now sends the infected animal at the
  player (animalRig gained setClip() crossfade — Gallop/Rat_Run; pack
  forwards to its dogs). Blade: both run to a contact point, strike
  lands as they meet. Bow/staff: the monster charges the shooter down
  and the shot meets it mid-run (arrow leads the target). Burst fires
  at the monster's live position; the freed animal appears where the
  infected form fell, not back at its start mark.
- Magic: beamFx replaced by magicFx — 90 white sparks snake to the
  target (sine wander, moving-target aware) while semi-transparent
  circles spawn along the stream; the post shader's partial-alpha
  branch renders them as black dither, so the smoke reads as dark
  rolling haze. Impact at 55% of flight.

Update 2026-08-14b — half outline, hand-keyed swing, shading picker
- 0.5 px outline: contour ink now gates on the Bayer cell (edge *
  step(t, 0.5)) — half the contour pixels ink, half show body.
- Sword: Tripo slash clip dropped. Hand-keyed swing via the same
  world-space aimBone technique — windup vector until 55% of the
  swing, then lerp to the strike vector; driven by the sequencer so
  the blade lands at impactAt (0.6 s), exactly when the animal reaches
  the contact point (closeT 0.5 s). Wrist grip-cancel pauses while the
  swing weight is up so the blade sweeps with the arm.
- Animal attack: at 97% of its charge the monster crossfades to its
  Attack clip (Attack / Attack_Headbutt / Rat_Attack).
- Arrow impact: burst() gained a solid white flash disc (0.55 r,
  shrinks over 0.16 s) and a slower, thinner ring — the bow release
  now has a readable pop at 320x112.
- Shading picker: the post shader takes uStyle; 8 selectable 1-bit
  techniques in a SHADING row (fx.setShade in headless): bayer6
  (posterized 6-step, the original), bayer∞ (continuous — smoothest
  gradients), bayer4 (arithmetic 4x4), noise (interleaved gradient
  noise, organic grain), dots (halftone screen), scanline (row
  thickness), hatch (crossed diagonals by darkness), ink (hard
  2-tone). Graphic styles (dots on) use a lifted tone curve
  (smoothstep(0, 0.72, lum)) so the low-key light doesn't starve them.

Update 2026-08-14c — walk gait, effects-list fix, sinister infected
- Distance-driven gait: the player's legs now stride when the group
  moves — the phase advances with actual x travel, so the stance foot
  never slides; standing still freezes the gait and the idle blends
  back. Works in reverse for the post-strike fall-back.
- Effects-list bug: arrow onHit pushed the burst DURING
  effects.filter(), which dropped it — its meshes froze in the scene
  (the lingering white circle). Pushes during update are now collected
  and merged. Staff had the same latent bug.
- Sinister infected forms (thorns > 0): a solid-white aether-eye
  sphere parented to the head bone (hot path renders it as a burning
  glow), and black semi-transparent miasma circles that spawn along
  the spine, rise, expand, and fade — dithered dark smoke off the back.

Update 2026-08-14d — selectable motion systems (MOTION row)
- Four motion modes, picked live in the UI (fx.setAnim headless):
  keyed, lively, physics, wild — each a different route to organic
  movement, built on the classic animation principles.
- keyed: the plain keyframed overlays as before — the baseline.
- lively: anticipation (the arm pulls back before the windup), follow-
  through (the blade overshoots past the strike vector and settles),
  secondary action (torso leans into the run scaled by speed, head
  counter-rotates to stay level, free arms counter-swing the legs,
  body bobs on each footfall), idle breathing (layered sine sway on
  spine + head), and squash & stretch (the monster compresses 22% as
  it launches its attack).
- physics: spring-damper joints — the swing weight and phase both
  spring-track their targets underdamped (k 170/140), so the arm lags,
  whips and overshoots like a mass on a joint, nothing hand-timed.
  Impact adds size-scaled impulse knockback (light animals fly, heavy
  ones rock: v = 2.6·knock·min(2, 2.2/height)) and the animal rears
  up off its forelegs under the hit (world-z pitch via ZYX order).
- wild: lively plus per-liberation randomness — the strike arc is
  rolled from three keyed arcs (overhead / thrust / diagonal, each
  with its own ANT/WIND/HIT/OVER vectors), the tempo is rolled
  (closeT 0.42–0.64 s), and the monster shuffles its attack-clip
  choice. No two liberations play the same.
- Size/distance-aware choreography: the blade meet point now derives
  from the animal's live bounding box — the nose-to-origin offset
  plus a lunge margin sets the separation (clamped 0.9–2.1), so a rat
  is met close and a stag at arm's length. The swing phase clock is
  s.impactAt/0.75, so the blow lands at impact whatever the tempo.
- Squash snapshots pre-squash scale (mAtkScale) so a mid-squash
  impact can't freeze a flattened monster.

Update 2026-08-14e — selectable sword attacks (STRIKE row)
- The single arm-arc swing became four full-body attack animations,
  keyframed over the swing phase (impact at p 0.75) and picked in a
  STRIKE row (fx.setStrike headless). Each key drives the blade aim,
  body lift (+leap / -crouch, with knee-bend so a crouch never sinks
  through the floor), torso lean, and a forward lunge along the facing:
  overhead (gather low, leap, pierce down from the top), backswing
  (arm far behind the back, torso twisted away, whipped through
  level), rising (slide down into a deep crouch, rip the blade up
  from below, then get back up), thrust (coil straight back, long
  lunging pierce). wild mode rolls one of the four per liberation;
  physics mode's spring-lagged phase plays the same tables with whip
  and overshoot.

Update 2026-08-14f — strike timing fix, banish effect
- Strike timing: the player now arrives at the meet point EARLY
  (closeT = impactAt - 0.18) and plants his stance mid-windup; the
  monster's arrival is timed to impactAt + 0.02, so the strike's own
  forward extension (lunge + blade arc, phase 0.56 → 0.75) actively
  meets the animal's nose as it closes. The sword goes out to the
  monster; the monster never walks onto a parked blade, and its own
  attack clip fires only at the moment it is cut.
- banishFx: one magic-dissolve for every liberation, all weapons
  (fired from impact(), same as the burst): a solid-white beam shoots
  up out of the body (0.25 s rise, holds, narrows away by 0.8 s),
  ~40 sparks rise along it, and 9 half-alpha dark fog discs roll out
  low (the post shader dithers them into black haze). The group rides
  seq.mLastX so knockback carries the beam with the body. The beam
  sits at z -0.1 so the freed animal pops in front of it.
