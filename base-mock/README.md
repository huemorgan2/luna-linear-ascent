# base-mock — the hub as a walkable 1-bit scene

Feasibility tests for the "base gathering" vision: the bottom-of-tower hub
(lodge / vault / forge / medlab / gate) as a live top-down scene you
navigate by clicking, rendered in the exact 1-bit banner style. Multiplayer
players visible in real time: walkers you can talk to, sleepers you can
loot or leave messages on.

**Not game code.** Nothing here ships; it exists to answer "can we get the
look and the interactions in a browser at card-embed cost?"

## Verdict so far: yes — 3D + shader filter is the right approach

`threejs/` renders a real 3D scene (orthographic, top-down 3/4, Pokémon
framing) into a 640×400 buffer, then a full-screen post pass does two
things: a **black ink outline** (sobel over the depth + normal buffers —
dark contour lines on bright fills, like a woodcut) and 8×8 Bayer ordered
dithering against the card palette (`#e6e9f2` ink on `#0b0e14`) — the same
discipline as `tools/generate_banners.py`. The scene is sunlit with real
shadow maps, so buildings and characters cast readable shadows; brightness
uses max-channel (the KayKit palette is blue-heavy and plain luminance
crushed it). The canvas is integer-upscaled with `image-rendering:
pixelated`.

Layout is a walled western-style town: one avenue with the buildings on
both sides (lodge + forge on the west row; vault, medlab, market on the
east row, with clear gaps between buildings and between the rows and the
wall), leading north to a square with a fountain, and behind it the tower
gate to floor 1 — with stairs visible beyond the gate descending into the
dark. A stone wall rings everything; braziers burn on the wall corners and
flank the gate with a flickering glow. Outside the wall, wild boars and a
wolf prowl (procedural quadrupeds with animated legs, kept outside by
local-hop wandering). You can slip behind the building rows but never
leave except through the gate. Buildings have collision boxes with a
tangential slide so click-to-walk flows around corners instead of pinning.

The chrome matches the chat cards: the HP/⚡/✦/◈ meter rail (with █░
blocks) sits above the canvas, and contextual options render below it as
[1] / [2] / [⏎] buttons — clickable or keyboard-driven.

Assets are real rigged models (KayKit, CC0, vendored in `threejs/assets/`):
five animated character rigs (75 clips each — Idle/Walk/Run/Lie), a weapon
set attached to the rigs' `handslot` bones, and ten medieval buildings
(tavern→lodge, castle→vault, blacksmith→forge, church→medlab, market,
well, homes, windmill, gate tower). `fetch_assets.py` re-downloads them.

Why 3D beats pre-baked gif/sprite frames for this:

- **Designed gradients come free.** The styleguide's core rule — every scene
  carries big dither gradients — falls out of real lighting: lamp pools,
  door glow, plaza falloff all ramp continuously and dither beautifully.
  With 2D sprites every gradient must be hand-baked per tile and breaks the
  moment anything moves.
- **Characters stay flat-forward** (styleguide: sprites are billboards that
  always face the camera) while the world has depth — exactly the
  Pokémon/Zelda-1 read the vision asks for.
- One scene graph serves mouse + mobile taps, smooth camera follow, and
  any future camera move without re-authoring art.
- Cost: three.js is ~150KB gzipped; the whole demo renders 640×400 — runs
  on anything, including inside a chat-card iframe.

GIF sprites remain right for *authored* art (banners, creature portraits).
For a **live, moving, multiplayer** space they can't carry the gradients.

## What the demo shows

- **all 8 race/sex variants** (human/elf/dwarf/halfling × ♂/♀), built from
  the five rigs via silhouette scaling (dwarves short+wide, elves tall+slim,
  halflings small) — each carrying a weapon: sword+shield, crossbow, staff,
  axes, dagger, wand
- real walk/run/idle animation crossfades; characters turn to face where
  they're going; sleepers use the `Lie_Idle` clip with animated Zzz
- **WASD / arrow keys** or click / tap to walk (keyboard cancels the click
  target; raycast to ground; eased camera leash-follow)
- proximity prompts, keyboard or click: `[1] enter the vault` anywhere
  near a building (box proximity, all buildings enterable),
  `1 loot / 2 leave message` near a sleeper, `t talk` near a walker
- mock multiplayer: six wanderers with `name · race` tags + canned talk
  bubbles, two sleepers you can loot or message
- loot consequence flavor ("their shardmind logged your face")
- lamp flicker, plaza light pool, HUD meters + prompt bar as crisp overlay
  text — same split as the chat cards: scene is dithered, UI is typography
- mobile: portrait layout scales the render to screen width (fractional
  downscale), touch tap-to-walk, and a destination list under the options —
  tap a building chip to fast-travel and auto-enter on arrival

## Run

```bash
cd base-mock && python3 -m http.server 8999
# open http://localhost:8999/threejs/
```

`shoot.py` (screenshots) and `record_gif.py` (walking GIF) drive it
headlessly via Playwright; output in `shots/`.

## Open questions for the real thing

- interiors: same renderer, one room per building, door = scene swap
- real multiplayer: worldd already owns players/floors; hub presence needs
  a cheap position channel (poll or SSE) — positions are the only new state
- sleeping-player messages/loot land naturally on existing letter + ledger
  systems
- art pass: buildings want hand-tuned emissive window textures + signage
  sprites; ground wants authored path/tile variation
- perf on mobile: fine (640×400); input already tap-native
