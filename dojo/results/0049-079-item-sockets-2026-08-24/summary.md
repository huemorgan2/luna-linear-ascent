# Dojo run 0049 — plan 079 item sockets (2026-08-24)

- **Environment**: local worldd `uvicorn app.main:app --port 8600`
  (`/health` ok, game 0.102.0, db true), Cursor IDE browser.
- **Commits under test**: `df01205` (phase-1 lib/sockets.js), `af70fcc`
  (phase-2 figure3d port), `5280347` (phase-3 fight3d port + URL bumps).
- **Scenarios**: `worldd/tests/079-item-sockets/scenario-portrait.md`,
  `scenario-finisher.md`.

## scenario-portrait — PASS

| Check | Verdict | Evidence |
|---|---|---|
| Human: buckler outside left forearm, face-on, off the torso | PASS | portrait-human-elf-native.png, portrait-human-elf-zoom.png |
| Human: sword on opposite hip, near-vertical, hilt at palm height | PASS | portrait-human-elf-native.png, portrait-hover-weapon.png (hover tint outlines the full sword: crossguard at palm, blade down the outer thigh) |
| Elf: bow slung on the back, limb above the shoulder | PASS | portrait-human-elf-native.png |
| Elf: sword + shield as human | PASS | portrait-human-elf-native.png |
| Giant: staff STANDING through right fist, in front of body, in frame | PASS | portrait-giant-staff-zoom.png (world bbox x −0.55…−0.30 vs frame edge −0.59 after tuck) |
| Gear visible at a glance (survives tone curve) | PASS | prop emissive lift 0.24 vs body 0.07; all items readable in native-scale shot |
| Hover tints the right piece, restores on unhover | PASS | portrait-hover-weapon.png / portrait-unhover-restore.png |
| Console/WebGL errors | PASS | none; all three stages mounted (`fig3dLives` = 3) |

## scenario-finisher — PASS

| Check | Verdict | Evidence |
|---|---|---|
| Blade rides the striking hand (human) | PASS | finisher-blade-idle.png, finisher-blade-approach.png |
| Bow held at grip (elf), hand-keyed draw path untouched | PASS | finisher-bow-elf.png |
| Staff gripped upright (giant) | PASS | finisher-staff-giant.png |
| Strike arc/tempo unchanged | PASS | `want` world-orientation mechanics untouched by the port; poses match pre-refactor captures from this session |
| Re-equip contract | PASS (code-level) | wrap handle contract unchanged (`userData.weaponWrap` removal path intact); harness has no replay control for a live double-equip probe |

## Regressions filed (pre-existing, NOT from 079)

- `tests/test_web_play.py::test_leaderboard_marks_only_you` FAILS at
  committed HEAD with a clean tree (verified via stash) — leaderboard/social
  area, unrelated to item placement. Needs its own track-and-fix.

## Notes

- The rigs have **no finger bones** (verified by live traversal), so "the
  hand grips the weapon" is an alignment illusion: the shaft is laid through
  the fist volume along the palm line. At 100×200 1-bit it reads as a grip.
- Placement is now data: `GRIPS`/`SOCKETS` in `worldd/static/site/lib/sockets.js`.
  New item = one table row; per-item overrides shallow-merge.
