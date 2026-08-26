# 082 · level001 · phase-1 — the map ships first, quests wait

## Goal

Floor 1's camp menu becomes the Fencerows map — v1, **no quests**. A Labs
toggle (`floormap`, shown as **"Floor maps"**, gated to floor 1) replaces the
Lamplit Steading option list with the 1-bit territory map carrying only the
places and actions the game already has: gate, town, camp (Hobb's fire),
Brackjaw's keep, the hunting fields. A marker with a real click-cost wears
that cost on the chip in the cost's own color (HUNT — `1 ⚡` in the energy
teal); Brackjaw's chip carries no cost (his keep screen already prices the
swing). Toggle off = today's list, byte-identical. Measurable: with the flag
off the gate-town scene dict is unchanged; with it on, every option id
reachable today is reachable from the map card; full plugin + worldd suites
at baseline (0 failures); dojo scenario PASS.

## Map art — territory scale (roy, 2026-08-26)

The map is a *district*, not a yard: ~1000 acres seen from altitude.
Forests, not trees; a mountain range, not a slope; massive field systems;
the river a real artery. Landmark buildings (pylon, town, camp, keep) stay
at their current small chip-scale, drawn ON TOP of the terrain the way map
landmarks are — clearly structures standing on the land. Art regenerated at
this scale (mock-map/raw_map.png → map_gen.py → map_001_640x480.png) and
that asset ships in the plugin as `content/art/maps/map_001_640x480.png`.

## Steps

All engine edits land in `plugin-linear-ascent/plugin_linear_ascent/` and
are vendor-synced into `worldd/vendor/plugin_linear_ascent/`. Quest scope
(economy, YAML places, engine/quest.py, combat seams) is **out** — it moves
to phase-2.

1. **engine/labs.py** — register
   `Feature("floormap", "Floor maps", <blurb>, floors=frozenset({1}))`.
2. **engine/tips.py** — `labs_toggle_floormap` tip.
3. **engine/floormap.py** (new, isolation contract: deletable) —
   `KEY = "floormap"`; `LAYOUTS = {1: {...}}` mapping option id → marker
   (x%, y%, label word, tooltip, cost text + cost kind); `payload(p, fl,
   options) -> dict | None`: None unless `labs.enabled(p, KEY, fl.floor)`
   and the floor has a layout; else `{"art": "map_001", "markers": [...]}`
   built ONLY from option ids present in the live scene options (a
   conditional row that is absent today is absent from the map). Options
   with no marker in the layout (stew/heal/use_*/answer_flare) stay
   ordinary rows under the map — nothing becomes unreachable.
4. **engine/scene.py** — top-level `map: dict | None = None`, riding
   `to_dict`/`from_dict` (the R-0053-1 lesson: both directions). Old
   clients drop the unknown top-level key and render rows.
5. **engine/core.py** — in `_gate_town_scene`, `_floor_arrival_scene`,
   `_npc_scene`: `s.map = floormap.payload(p, fl, s.options)`. No other
   seam.
6. **content/art/maps/map_001_640x480.png** — the dithered asset, copied
   from the mock pipeline output.
7. **render.py** — `_map_data_url(slug)` (maps dir through `_art_url`, so
   ART_BASE hosting works); `_map_html(scene)` emits the map block: the
   PNG 1:1 (`image-rendering: pixelated`), absolutely-positioned borderless
   chip `<button data-opt=…>` markers (`[n] NAME`, numbering = the
   option's position in `scene.options` so typed numbers keep working),
   cost span on the chip in the cost color, tooltip above on hover
   (paints over neighbours), hover invert, CSS in the card stylesheet.
   When `scene.map` renders, mapped option ids are skipped from the row
   list; unmapped ids still render as rows beneath.
8. **version.py** — bump.
9. **Vendor sync** — plugin → `worldd/vendor/plugin_linear_ascent/`,
   worldd plugin pointer update.
10. **Tests** — new plugin `tests/test_082_floormap.py` (see Verification).
11. **Dojo** — `luna/dojo/tests/082-floor-maps/` scenario
    *map-replaces-menu* + walkthrough run before reporting complete.

## Verification

- Targeted (`tests/test_082_floormap.py`):
  - flag off ⇒ `scene.map is None` and `to_dict()` equals today's
    (no new keys with values that alter old-client behavior);
  - flag on, floor 1 ⇒ `map["art"] == "map_001"`, every marker's `opt`
    exists in `scene.options` ids, hunt marker cost text `1 ⚡` and kind
    `energy`, keep marker carries **no** cost;
  - flag on, floor ≠ 1 ⇒ None (floors gate);
  - hurt player ⇒ stew/heal ids NOT in markers (they row below);
  - Scene round-trip `from_dict(to_dict())` preserves `map`;
  - render: fragment contains one `data-opt` per option id exactly
    (chip or row, never both), map img present.
- Full suites: plugin pytest and worldd pytest at baseline (0 failures).
- Dojo *map-replaces-menu*: toggle Labs → Floor maps ON, floor 1 camp
  shows the map, click through GATE / TOWN / CAMP-TALK / BRACKJAW / HUNT
  and back, each lands on the same scene the list version lands on;
  toggle OFF restores the list. Evidence: screenshots + scene ids.

## Rollback

- Live mitigation: the Labs toggle itself — off restores the old menu
  per player instantly.
- Full revert: delete `engine/floormap.py` and
  `content/art/maps/map_001_640x480.png`, drop the `floormap` key from
  `labs.py` + the tip, revert the three-line core seam, the `scene.map`
  field and the render block, version bump revert, vendor re-sync. One
  commit revert; no player-doc migration (a stale
  `p["labs"]["floormap"]` key is ignored by design).

## Execution status

Executed 2026-08-26. Shipped in plugin 0.105.0; vendor synced.

- **Code:** labs registry + tip, `engine/floormap.py`, `Scene.map`
  (to_dict AND from_dict), three core seams (`_floor_arrival_scene`,
  `_npc_scene`, `_gate_town_scene`), `content/art/maps/map_001_640x480.png`
  (territory-scale re-render), render map block + chips + tooltips + cost
  inks + row suppression, `button.mk` added to BOTH click-wiring selector
  lists (pane.py `wireOptions()` and the render.py bridge — chips were
  inert without it; found by dojo run 0054, not by coded tests).
- **Tests:** targeted `test_082_floormap.py` 8/8. Plugin suite 1406
  passed / 5 failed — all 5 pre-existing at baseline (kill3d ×3,
  048 no-classes, 013 combat-feel; verified failing on a stash of the
  changes). worldd suite 221 passed / 0 failed.
- **Dojo:** run 0054 (`dojo/results/0054-082-floormap-2026-08-26/`)
  **28/28 PASS** — list-off byte path, toggle + DB flag both ways, map
  card, five chips with correct labels/numbering, `1 ⚡` in AETHER on
  HUNT only, tooltip, all five destinations reachable and returning to
  the map, exactly 1 ⚡ spent on hunt, keep entry free, no console errors.
- **Not done (by design):** quests (phase-2+); deploy not requested.
