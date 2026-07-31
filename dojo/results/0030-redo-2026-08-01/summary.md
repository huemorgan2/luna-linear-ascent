# 0030 redo — the design pass on the user's punch list · 2026-08-01

Stack: local render harness (`plugin-linear-ascent/tools/qa_030_shots.py`)
— the real engine (`core.apply_choice`) + the real card
(`render.render_scene`) + Playwright 720×1200 @2x, reduced motion.
Same 14 scenes as the 0030 pass; this run verifies the redo (0.36.0).

## Findings — PASS

- **Portraits reshaded** (01, 11): all six buckets regenerated as
  dithered charcoal studies — forms from tonal gradients, no hard
  cartoon outlines. Rags and chain confirmed on card; suit-up intact.
- **Pack beside the portrait** (01, 04, 11): the pack strip now lives
  inside the profile block's right column — portrait left, meters top,
  ATK/DEF rows, PACK row under them. No strip under the image anywhere
  a profile renders.
- **Enemy plate is one line** (10, 13): `HP n/m · ⚔ ATK · 🛡 DEF` on a
  single black chip at the top of the art, [i] badge keeping the
  corner. Pips, range chip and modifier chip are gone from the art;
  range + modifiers moved into the [i] dossier (unit-tested).
- **Morning Crier is newsprint** (02): light sheet, dark ink, grain a
  shade under the paper; headline + 4 short mid-dot items
  ("Warden Applewrath — 43% · floor 3 · 2 blades · closes in 3h 12m"),
  ✕ still closes for the day.
- **News shortened**: Crier census/warden lines are headline-short;
  worldd's war lines condensed at the source ("X — cut to 50% ·
  floor 3", "X slain by A, B · floor 4 open").
- **Keeper tells glory stories** (04): four rotating tellings of named
  climbers (Okko, Brand, Asha, Vell) earning fortunes over time —
  night shifts, rested kills, vault interest, pawn timing — real
  numbers painted in colour inside the prose.
- **Reel skippable** (06, 07, 14): every beat is [1] Next [2] Skip;
  skip cuts to the arrival card and still stamps `floor_seen_{n}` —
  once per floor holds, for old and new names alike (the flag is new,
  so every existing player gets the movie once too).
- **Colour sweep**: headlines, option labels and fold summaries now
  paint amounts (the ◈ 3,500 in the town NEXT line, lodge ◈ hints);
  body/hints/support/notices/shard already painted.

## Notes

- Screenshots 01–14 in `screenshots/`; harness unchanged and reusable.
- Full plugin suite after the redo: 758 passed, 1 skipped, ~5.4s.
- worldd DB-backed tests still not runnable on this machine (no
  Postgres); the two worldd news lines are copy-only changes inside
  tested insert paths.
