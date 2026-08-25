# fight3d — the kill finisher + arena stage

Two stages over one canvas law (320-wide 1-bit band, inked in the card's
banner tint):

- `fight3d.js` — the kill finisher (PLAN4): strike choreography mounted
  into the victory card's banner slot from `data-kill3d`
- `arena3d.js` — the live fight stage (067): 320×300 band driven by
  `data-arena`, phase by phase
- `monsters/`, `backgrounds/`, `backgrounds300/` — creature GLBs and
  painted plates (scene-specific, not shared)
- `test.html` — finisher harness; `gallery.html` — creature gallery
  (serve `worldd/static/site`, open `/static/site/fight3d/test.html`)

The climber is NOT built here. Since plan 080 both stages build the
player through `../lib/character.js` — the same GLBs out of
`../lib/models/`, the same normalization, and the same dressing loop
through the `../lib/sockets.js` grip table that the figure3d portrait
uses. The scenes keep only stagecraft: cameras, the shared crushed-black
tone curve (`smoothstep(0.28, 0.75)`, from the portrait — plan 080
phase 2), strike timing, HUD.

Gear on the wire: `data-rig3d="family:class:slug+slug+..."` pre-warms
the item GLBs; `kill3d`/`arena` payloads carry `worn`/`paths`/`lead` so
the climber fights in their real wardrobe (plan 080 phase 3). Generic
family weapons under `../lib/models/items/` are fallbacks only.
