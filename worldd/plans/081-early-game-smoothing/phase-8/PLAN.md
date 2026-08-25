# 081 phase-8 — R-0053-1: the foe sheet survives the pane's serialization

## Goal

The phase-6 foe sheet (type grid + dismissable swap hint) actually
renders on the web pane — the surface every real player uses.
Measurable: a fresh wilds opener fetched through worldd's
`/play/api/act` contains `class="foesheet"` (and `class="foehint"`
while undismissed); dojo scenario 06 re-walked end to end and judged.

## Problem (from dojo run 0053, scenario 06)

`Scene.to_dict()` / `Scene.from_dict()` (engine/scene.py:381/440) do
not carry the `foe_sheet` field phase-6 added to Scene. worldd's
`/play/api/act` and `/play/api/pane/scene` round-trip every scene
through that serialization (app/webplay.py `_card` →
`Scene.from_dict`), so the pane renders with `foe_sheet=None` and the
sheet + hint never appear. Plugin tests passed because they render the
Scene object directly — the dict round-trip had no test.

## Root cause

Phase-6 added the Scene field and the renderer but not the
serialization pair. `foe_sheet` is a plain dict of str/int/bool —
JSON-safe, additive, safe for old stored scenes (`d.get` → None).

## Steps (engine — submodule first, then vendor + pointer)

1. `engine/scene.py to_dict()`: add `"foe_sheet": self.foe_sheet`.
2. `engine/scene.py from_dict()`: add
   `foe_sheet=(dict(d["foe_sheet"]) if d.get("foe_sheet") else None)`.
3. Test (`tests/test_081_foe_sheet.py`): round-trip test — an opener's
   `Scene.from_dict(s.to_dict())` keeps `foe_sheet` intact and its
   fragment still draws `.foesheet` + `.foehint`; a round card's
   round-trip keeps it None.
4. **Second root cause (found re-walking 06 after 1–3):** the
   idempotent scene rebuild loses the opener. `core._build_scene`
   rebuilds any live encounter as `combat.fight_scene(p, fl)` —
   `opener` defaults False — so `/play/api/pane/scene` (reload, tab
   restore, any refusal-recovery read) answers with a bare round card:
   no sheet, no prose, no pack row, even though the player is still
   sizing up. Fix: rebuild with `opener=combat.swap_window(p)` — the
   sizing-up predicate (at range, not attacked, treeline unbroken) is
   exactly "the opener is still the truthful card". Once the fight has
   begun the rebuild stays a round card, as today.
5. Test: after starting an encounter at range, `core.current_scene(p)`
   carries `foe_sheet`; after an attack it does not.
6. Vendor sync (`diff -rq --exclude=__pycache__` clean) + parent
   pointer bump.

## Verification

- Targeted: `pytest tests/test_081_foe_sheet.py` (new round-trip test
  included), then full plugin + worldd suites at baseline.
- Live: fresh floor-1 opener via `/play/api/act` contains
  `class="foesheet"`.
- Dojo scenario 06 re-walked (desktop + mobile), results appended to
  run 0053's summary.md.

## Rollback

Revert the commit(s). The two serialization lines are additive; old
stored scenes lack the key and load unchanged.

## Execution status

Executed 2026-08-25. Two engine commits:
- d8dfae5 — `to_dict`/`from_dict` carry `foe_sheet`; round-trip test
  (opener keeps the sheet through the dict pair and still draws
  `.foesheet` + `.foehint`; a round card round-trips to None).
- ca4b5a4 — `_build_scene` rebuilds a live encounter with
  `opener=combat.swap_window(p)`; test: `current_scene` carries the
  sheet before the first attack, not after.

Vendor synced (`diff -rq --exclude=__pycache__` clean). Tests:
`test_081_foe_sheet.py` 12 passed; full plugin suite 1395 passed /
1 skipped / 1 xfailed (same 8 pre-existing failures as baseline);
worldd suite 221 passed.

Live verification: fresh floor-1 opener via `/play/api/act` contains
`class="foesheet"` and `class="foehint"`; `/play/api/pane/scene`
mid sizing-up returns the full opener (fix #2); fresh browser load
renders the sheet ({"sheet":true,"cells":["DEF 5","SPEED 3"]}).

Dojo scenario 06 re-walked end to end (desktop + mobile): PASS —
addendum in `dojo/results/0053-081-early-game-smoothing-2026-08-25/
summary.md` (all four type pairings, hint dismissal persistence,
reload-keeps-opener, swap window, mobile 2×2 grid, clean round cards).
