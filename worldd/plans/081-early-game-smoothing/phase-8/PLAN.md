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
4. Vendor sync (`diff -rq --exclude=__pycache__` clean) + parent
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
