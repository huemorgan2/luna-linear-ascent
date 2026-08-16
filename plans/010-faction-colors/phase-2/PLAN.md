# Phase 2 — plugin: pick it at founding, change it at the desk

## Goal

A founder picks a named color as its own step of the creation flow
(name → banner → **color** → fee → dues); a steward changes it from the
same admin-desk area as rename (web pane AND the in-scene hall desk);
the chosen slug rides the meters to the renderer. Measurable: plugin
tests pass; the founding flow shows exactly 9 named swatches.

## Steps

All in `plugin-linear-ascent/` (submodule), then inherited by worldd in
phase 4 via the vendor sync.

1. **`plugin_linear_ascent/colors.py`** (new) — the single source of
   truth:
   ```python
   FACTION_COLORS = {  # ordered: slug -> (display name, ink)
       "mouse-grey": ("Mouse Grey", "#5b5952"),
       "rag-silver": ("Rag Silver", "#adaba0"),
       "bone-white": ("Bone White", "#fbfbf7"),
       "coin-gold": ("Coin Gold", "#f5b825"),
       "aether-teal": ("Aether Teal", "#45d0c0"),
       "warden-violet": ("Warden Violet", "#d967c8"),
       "ember-red": ("Ember Red", "#f26541"),
       "orchard-green": ("Orchard Green", "#8ed24a"),
       "root-brown": ("Root Brown", "#b5722f"),
   }
   DEFAULT_COLOR = "warden-violet"
   def faction_ink(slug) -> str  # hex, falling back to DEFAULT_COLOR
   ```
2. **Founding flow** — `engine/social.py`:
   - `_founding_scene`: insert step `color` after `banner`; headline
     "The color it flies"; swatch options `col_<slug>` labelled with the
     display names (gallery of solid-ink tiles if the gallery path
     supports untextured tiles, plain options otherwise).
   - `guildhall_action`: handle `col_` prefix when
     `st["step"] == "color"` → `st["color"] = slug`, advance to `fee`.
   - The final founding effect carries `color=st.get("color", "")`.
3. **Meters plumbing**:
   - `engine/scene.py`: `Meters.faction_color: str = ""` (~L64, beside
     `faction_banner`).
   - `engine/combat.py meters()`:
     `faction_color=str(_wfac(p).get("color") or "")` (~L151).
4. **Admin desk, web pane** — `pane.py`:
   - In the "admin desk — the banner" panel (beside the rename savebar,
     ~L903): a swatch row — 9 buttons, each a solid square of its ink
     with its name in the tip, current one ringed;
     `data-desk="recolor" data-color="<slug>"`.
   - Handler (beside the rename handler ~L987):
     `call('/pane/faction/recolor', {color})`; on success re-render the
     panel and the card strip state.
5. **Admin desk, in-scene** — `engine/hall.py`:
   - Beside `rename_banner` (~L771): option `recolor_banner`
     ("Change the colors"); picker scene listing the 9 names; chosen →
     `_effect(p, "faction_recolor", color=slug)` + confirmation note,
     mirroring the rename flow (~L964–1012).
6. **Plumbing to the server** — `routes.py`: `FactionColorIn` +
   `POST /pane/faction/recolor` proxy (beside rename ~L406);
   `backend/remote.py`: `faction_recolor` → `POST /v1/faction/recolor`
   (beside `faction_rename` ~L163).

## Verification

- New/extended plugin tests (`tests/`):
  - founding walks name → banner → color → fee → dues; `col_ember-red`
    lands in the effect payload;
  - `meters()` carries `faction_color` from `w["faction"]["color"]`;
  - hall desk `recolor_banner` emits the `faction_recolor` effect;
  - roster invariants: 9 entries, every ink one of the existing palette
    constants, `DEFAULT_COLOR` present.
- `cd plugin-linear-ascent && pytest` — full suite green.

## Rollback

`git revert` the phase commit in the submodule. No data or schema
involved; the server from phase 1 tolerates clients that never send a
color.

## Execution status

**Done — 2026-08-16, plugin commit `e88ce2f`.**

- All planned edits landed: `colors.py` (9-ink roster, single source of
  truth), founding color step in `engine/social.py` (gated on
  `w["faction_colors"]` — old servers skip it), `Meters.faction_color`
  plumbing (`scene.py` + `combat.py`), hall desk recolor flow
  (`engine/hall.py`), pane swatch rows for found form + admin desk
  (`pane.py`), `/pane/faction/recolor` proxy (`routes.py`,
  `backend/remote.py`). worldd `faction_detail` now also carries
  `color` so the desk swatches can mark the current ink (rides the
  parent-repo phase-2 commit).
- Verification: 10 new tests in `tests/test_010_faction_colors.py`,
  all pass. Full plugin suite: 1188 passed, 1 skipped, 1 xfailed,
  3 failed — all 3 failures reproduce at submodule HEAD with every
  phase-2 change stashed (`test_022_001` pool payout, `test_026` gate
  wound, `test_kill3d` first-sighting line), i.e. pre-existing from the
  parallel chest-card work (`18ca39c`/`985412c`), not phase 2. Filed in
  the plan's operational notes, not fixed mid-run.
- Note: `guild_found` effect key for the name is `guild`, not `name`
  (test adjusted).
