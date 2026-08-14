# PLAN3 — putting the 3D kill scene into the game

2026-08-14. Scope: the demo2 fight stage (320x112 three.js, 1-bit post shader,
keyframed strikes, banishFx) becomes the game's **kill finisher** for wild
creatures — starting with floor 1 only. Wardens keep their GIF reels.

Ground laws (from the shipped game, mapped by the code survey):

- The engine is pure Python emitting `Scene` objects; the browser swaps HTML
  fragments (`pane.py showScene()`, `game.innerHTML = fragment`). No client
  game logic exists today.
- The Luna chat card is **no-network by law** (`render.py:8`) — every asset is
  inlined. The 3D layer is therefore **website-only** (`/play`), injected the
  same way `funnel.js` already is (`worldd/app/webplay.py:114`). The chat card
  keeps the GIF path untouched.
- Aesthetic law: 1-bit white ink as a CSS mask over a tint color,
  `image-rendering: pixelated`. The 3D canvas must obey it: same post shader,
  ink colored by the same tint the banner uses.
- Missing-art convention: slugs with no file degrade silently. The 3D layer
  degrades the same way — no GLB / no WebGL / chat surface → the existing
  GIF (`_kill_fx`) plays exactly as today.

---

## Part A — generate monsters that LOOK like monsters

The demo2 animals are stock GLBs (Wolf, Rat, Bull, Husky, Rogue_Hooded) —
placeholders, and they read as pets. Every shipped creature gets a Tripo-
generated model with a **breed style bible**, matching the game's fiction
(native / pressed / wrongmade):

| breed | silhouette rules |
|---|---|
| native | wild and wrong: gaunt, matted, bone spurs, scarred hide, too many teeth. Predator posture, never "cute". |
| pressed | war-gear: scrap-iron armor plates, chains, cage muzzles, banner scraps, crude rivets. A beast someone armed. |
| wrongmade | wrong geometry: metallic or chitinous shells, asymmetric growths, glowing seams, spikes that pierce their own hide. |

### Floor-1 prompt sheet (replaces the fluffy five)

- `grey_wolf` — "gaunt dire wolf, ribs showing through matted black fur, bone
  spikes along the spine, scarred iron-grey muzzle, bared oversized fangs"
- `feral_boar` — "massive feral boar, cracked tusks capped with rusted iron,
  bony armor plates grown over the shoulders, small furious eyes"
- `hedge_rat` — "dog-sized plague rat, scabrous hairless patches, needle
  teeth, spiked vertebrae, naked segmented tail"
- `lane_wolf` — grey_wolf variant: leaner, torn ear, old brand scar (the
  pack leader reads as a veteran)
- `goblin_straggler` (biped) — "hunched goblin deserter, scrap-metal pauldron
  and stolen helm, jagged cleaver, wiry and mean"
- `ember_shade` (biped) — "hedge-wight: hulking wrongmade revenant of woven
  briars and charred fenceposts, ember light in the seams, iron nails
  studding the limbs"

Texture prompt suffix (all of them, per `vision/1bit-images.md`): *flat color
regions, strong tonal separation, no micro-texture, matte, high-contrast
silhouette* — this is what survives the 1-bit threshold shader.

### Pipeline (existing tools, `research/3d-fight/"3d models"/`)

`gen_models.py`: text→model (2000 faces) → texture → rig → retarget idle;
`gen_clips.py`: attack/hit clips. Manifest-resumable; TRIPO_API_KEY in the
gitignored `.env`. ~30 credits per creature; floor 1 = 6 creatures ≈ 180
credits (balance ~4300, fine).

### Risk + validation spike (do this FIRST)

Tripo auto-rig/retarget presets are **biped** (mixamo names). Four of the six
floor-1 creatures are quadrupeds. Spike, one creature (`grey_wolf`):

1. Generate model + texture. 2. Try Tripo quadruped rig (if the API exposes
   one) — else auto-rig and inspect. 3. If no usable quadruped clips: demo2
   already drives locomotion procedurally for the player; extend the same
   trick to monsters — root-bone bob + lunge + head-pitch driven from code,
   using only the model's bind pose. The kill scene needs exactly: walk-in,
   one attack lunge, flinch — all achievable procedurally.
4. Accept/reject before batch-generating the rest.

Bipeds (`goblin_straggler`, `ember_shade`) go through the proven biped path
(same as the 6 player assets generated 2026-08-13).

---

## Part B — floor-1 integration first, then the tower

### B1. Wire data (engine, tiny and additive)

At `_victory()` the killing blow is fully knowable **at that instant**:
`p["race"]` + `_damage_type(p)` (side-arm attacks promote to the lead hand
*before* resolving, so the lead weapon IS the killing weapon). `_kill_fx()`
already computes `{id}_{verb}_{race}_{line}`. Add to the victory Scene one
attribute (rendered as data-attrs on the card, next to the existing
`data-fight` / `data-dtype`):

```
data-kill3d="{enc_id}:{race}:{line}:{breed}:{tint}"   # e.g. grey_wolf:human:blade:native:#9ae6b4
```

Emitted only when `content/art/models3d/{enc_id}.glb` exists (same probe
convention as `_creature_art()`), so it self-gates per creature and per floor.
`Scene.fx` keeps the GIF slug — the GIF remains the fallback body of the card.

### B2. Client bundle (website only)

- `worldd/static/site/fight3d.js` — demo2's fight2.js refactored into a
  library: `mount(el, spec)` where spec = `{enc, race, line, breed, tint}`.
  Injected from `webplay.py` next to `funnel.js`. three.js bundled locally
  (vendored, no CDN).
- Models served from `/static/site/models3d/` (player 3 races × 3 weapon rigs
  already generated; monsters from Part A). Preload the current floor's set
  after first paint; lazy is fine — the fallback GIF covers a slow load.
- Hook: `showScene()` already calls `window.__laScene(d, game)` (the sfx
  layer precedent). `fight3d.js` registers alongside: on every swap, if the
  new fragment has `data-kill3d` and WebGL is available, mount a canvas
  absolutely over `.banner` inside `.bwrap` (already `position:relative`),
  hide the GIF mask div, run the liberate sequence once (player walks, strike
  library picks by weapon line, banishFx in the monster's tint), then leave
  the last frame held. `innerHTML` replacement destroys the canvas on the
  next act — renderer + GL context live in a singleton outside `#game` and
  re-attach, never re-created per scene.
- Degrade: no WebGL, GLB 404, chat iframe → do nothing; the GIF plays.

### B3. Floor-1 milestone (uses monsters we already have + Part A spike)

1. Ship B2 with the **stock demo2 GLBs** behind a dev flag to prove the
   mount/lifecycle/fallback plumbing on the real site.
2. Swap in the Part A floor-1 monsters as they clear the spike.
3. Only `floor_001.yaml`'s six ids get `models3d/` files → the feature is
   floor-1-only by the probe rule, no code switch needed.

### B4. The rest of the tower (roadmap, not now)

- Floors 2–10: batch-generate per floor with the breed bible (4–6 creatures
  × ~30 credits ≈ 150–180/floor). Reuse rigs across variants (lane_wolf ←
  grey_wolf) to cut cost.
- Floors 11+: generate on demand as the world frontier approaches; the probe
  rule means partially-covered floors just mix 3D and GIF kills.
- Milestone bosses (10, 20, … 100) are wardens — excluded (Part E).

---

## Part C — closeup on FIRST encounter

The 320x112 banner already IS the solo closeup (plan 049 law), but there is
no first-encounter *beat* — the flag `p["matchup_seen"]` exists and only
fires a sidekick line. Change:

- In `start_encounter()`, first time an `id` enters `matchup_seen`: emit one
  interstitial Scene before the fight card — creature banner full-bleed
  (320x200 closeup art from `plans/049`/`plans/054` where it exists, else the
  112 banner), name, breed, one lore line from `_enemy_payload`'s `story`,
  single option **"Fight"**. Subsequent encounters skip straight to the fight
  card as today.
- This is engine-side (works in chat AND web), pure Scene — no 3D involved.

## Part D — 3D is the DEATH scene only

- The 3D canvas mounts **only** on the `_victory()` card (`data-kill3d`),
  never on fight rounds, never on flee/death. Fight rounds keep the masked
  banner + estat exactly as shipped.
- Correct actor guaranteed: race from `p["race"]`, weapon line from
  `_damage_type(p)` at the killing instant (B1). Strike selection: blade →
  strike library (overhead/back/rising/thrust, wild-rolled), bow → draw+shot,
  staff → cast. Player GLB per race, weapon prop per line — all 9 combos
  covered by the generated player assets.

## Part E — wardens keep the GIF reels

- No 3D for wardens (shared world body, milestone identities, personalized
  `warden_001_evicted_{race}_{line}` movies already exist). `data-kill3d` is
  never emitted for `kind == "warden"`.
- **Bug found and FIXED this session**: the fall reel's slain beat used
  `fx="warden_slain"` — art that was never generated (specified in
  `generate_event_gifs.py`, never rendered), silently degrading to the still
  banner. Repointed to the shipped `warden_fall` reel in both engine copies;
  test updated with a regression guard (fx slug must resolve to shipped art).
  11/11 pass.
- Follow-up (optional, restores the intended beat): run
  `tools/generate_event_gifs.py warden_slain --backend grok` (GOLD tint, 8 s,
  split 5.0), vendor the intro/loop pair, add `"warden_slain": GOLD` to
  `render._FX_TINT`, flip the fx back.

## Part F — color the animation per monster

The game already tints: `_banner_tint()` per creature/breed +
`_VARIANT_TINT` for runt/tough/alpha specimens. The 3D layer inherits it:

- The post shader's white ink becomes a `uInk` color uniform; the tint from
  `data-kill3d` (the SAME hex the banner div uses) is passed to `mount()`.
  Result: the kill scene is ink-colored identically to the creature's card —
  green natives, rust pressed, violet wrongmade, specimen retints for free.
- banishFx layers: beam + sparks in `uInk`, fog discs stay black (they read
  as dither haze in any tint). Wild mode may pulse the ink ±10% lightness on
  impact frames.

---

## Order of work

1. **A-spike**: grey_wolf through Tripo, quadruped rig verdict. (blocks A)
2. **B1**: `data-kill3d` on the victory Scene + probe gate + tests.
3. **B2**: fight3d.js mount/lifecycle/fallback with stock GLBs, dev flag.
4. **F**: ink uniform + tint plumb-through (small, do with B2).
5. **A-batch**: remaining 5 floor-1 monsters, vendor GLBs, flag off → live.
6. **C**: first-encounter interstitial (independent, any time).
7. **E follow-up**: warden_slain asset generation (optional).
8. **B4**: floors 2–10 batches, one floor at a time.
