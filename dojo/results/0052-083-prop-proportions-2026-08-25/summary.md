# dojo run 0052 — 083 prop proportions (portrait gear fixes)

- **Date:** 2026-08-25
- **Commit:** 4ea13bd (plan committed at 14e0418, then renumbered 081→083
  over the early-game-smoothing collision)
- **Environment:** local worldd at 127.0.0.1:8600, figure3d harness
  (`/static/site/figure3d/test.html?fig3ddebug`), repro loadouts injected
  into `#game` from the console (same mount path as /play)

Trigger: Roy's live profile (huemorgan, elf blade) — Notched Cleaver as
a floating slab, shield-slot buckler as a floating ball (user read the
purple hover ink as "armour"; purple is the shield slot).

## Scenarios

| scenario | verdict | notes |
|---|---|---|
| repro: elf + notched_cleaver / wolfsteel_broadsword + gate_buckler | REPRODUCED | broadsword slab past the frame edge (scene bbox x −0.86 vs camera ±0.42), buckler ball at the forearm — screenshots 01, 02 |
| repro side-effect: three same-race figures on one page | REPRODUCED | all elf stages black except the last mounted — shared gltf.scene re-parented by Group.add() |
| fix: originals human/elf/giant (sword, bow+sword, staff) | PASS | zero regression — rusted_sword back at full length under the RMS girth cap (bbox-width cap had shrunk it to a dagger; caught and replaced) — screenshot 03 |
| fix: elf + cleaver, elf + ratcatchers_dirk | PASS | both hand-scale at the hip, grips at palm height — screenshot 04 |
| fix: shield through idle animation phases (0.01s / 0.8s / 1.9s / 3.0s) | PASS | squashed disc stays pressed on the forearm at every phase; the ball/sliver flip-flop with the forearm twist is gone — screenshot 05 |
| fix: same-race multi-mount | PASS | six stages, every body present (SkeletonUtils clone per stage) |

## Measured root causes

- `notched_cleaver` blade is 45% as wide as long; family `len: 0.55`
  scaled its long axis to sword length. RMS cross-section separation:
  slender swords 0.035–0.061 rms/len, cleaver 0.113, dirk 0.143 —
  `girth: 0.035` (blades) caps the squat ones only.
- bucklers are domed (depth 64% of diameter): `squashd: 0.30` crushes
  the dome; new orient/offset strap it flush on the forearm.
- shared `gltf.scene` across stages: last mount steals the body.

## Tests

`tests/test_web_play.py` + `tests/test_071_figure3d.py`: 16 passed.
