# 0063 — Equipment durability bars

Date: 2026-09-11. Parent baseline: `7bb8326`; plugin baseline: `20b0b71`;
plan committed before implementation: `a68f663`; implementation: `2f9cfff`.

The shared durability track is now borderless and aligned exactly with
the equipment frame's outer left, right and bottom edges. Its 3px height,
fill percentage and green/gold/red thresholds are unchanged.

## Environment

Local worldd at `127.0.0.1:8601` loaded the source plugin. QA Luna at
`127.0.0.1:8798` was freshly started with that plugin. Existing isolated
QA databases `ascent_maps_browser` and `luna_maps_qa85` were used for
browser play; the service suite used only `ascent_maps_tests`. Production
was not accessed. Pre-existing dirty files were preserved.

## Browser verdicts

| Scenario | Verdict | Evidence |
| --- | --- | --- |
| Baseline reproduction | PASS | `screenshots/01-before.png`: a 52px track inside a 60px frame, inset 4px on each side and 3px at the bottom. |
| Desktop bar states | PASS | `screenshots/02-bars-desktop.png`: green 75%, gold 25%, broken red, full durability, packed count and read-only player sheet. |
| Mobile 390px | PASS | `screenshots/03-bars-390.png`: readable icons/counts; strips touch the frame without overflow. |
| Mobile 320px | PASS | `screenshots/04-bars-320.png`: same visual result. `geometry.json` records zero left/right/bottom differences, 3px height and 0px bar border. |
| Real game and popup | PASS | `screenshots/05-equipment-popup.png` and `06-game-after.png`: Rusted Sword shows 1,298/1,300 durability; its strip has zero edge offsets. |
| Luna conversation | PASS | `07-luna-equipment.png`, `08-luna-refresh.png`, `09-luna-pane.png`: real `ascent_character` and `ascent_scene` calls, correct equipment, working pane and popup. |
| Refresh preserves equipment | PASS | `luna-state-before.json` and `luna-state-after.json` are identical for stored gear/durability, HP 80, coins 50, energy 24, action sequence 25 and gate location. |

All screenshots were opened and visually inspected. Temporary viewport
overrides were reset. The fixture generator uses the actual shared CSS
and slot renderer; `render_preview.py` can recreate it.

## Coded checks

- Focused renderer/equipment/avatar checks: **53 passed, 1 failed**.
- Full plugin suite: **1,441 passed, 9 failed, 1 skipped, 1 xfailed**
  (`plugin-full.txt`, 592.95 seconds).
- The nine failures all reproduce with the pre-change renderer:
  **9 failed** in `baseline-failures.txt`. The focused quiver failure
  also reproduces independently in `baseline-focused.txt`.
- The supplemental full worldd run was interrupted after **92 passed in
  1,400.16 seconds**; its partial output is in `worldd-full.txt`. This is
  **not a full pass**. Cancellation also produced client-close teardown
  warnings; the run had no failed test before interruption.
- Source and vendor renderer files are byte-identical. `git diff --check`
  passes. There is no asset build or dependency change.

## Regressions and observations

No styling regressions observed. Existing engine/renderer assertions fail
in combat flavor, death relics, XP at cap, class migration scanning,
arena distance, quiver consumption and kill-3D rendering; see the baseline
comparison for exact test names. They were not changed in this CSS task.

Luna answered `show me the scene` by referring to its existing pane; the
explicit follow-up `refresh my current scene` called `ascent_scene`.
The refresh reported a routine daily repair-token gift. The gear and
stored meters stayed the same. Initial Luna startup was slow and logged
optional embedder warm-up timeouts before the successful walkthrough.

Production publication was not performed. Broader service-suite
validation remains incomplete; the requested styling is implemented and
verified locally.
