# 088 — preserve contrast on every floor map and mark exact locations

Status: planned 2026-09-11. This plan is committed before implementation under the workspace devprocess.

## Problem

The approved floor-map sources use local one-bit dot density to distinguish water, forest, stone, roads, and lit ground. Floor 2 now preserves those tonal regions at 492×369, but floors 3–10 still use the earlier conversion and look flatter. Map labels also name destinations without showing the exact point on the landscape that each link targets.

Measured against each saved source in 24×24 target-pixel territory blocks, the current and proposed tone ranges are:

| Floor | Current | Preserve-source | Change | Proposed correlation |
| --- | ---: | ---: | ---: | ---: |
| 3 | 0.5012 | 0.6169 | +23.1% | 0.9961 |
| 4 | 0.4459 | 0.5945 | +33.3% | 0.9978 |
| 5 | 0.4942 | 0.5962 | +20.6% | 0.9967 |
| 6 | 0.5616 | 0.6740 | +20.0% | 0.9971 |
| 7 | 0.3577 | 0.4562 | +27.5% | 0.9930 |
| 8 | 0.4752 | 0.5893 | +24.0% | 0.9960 |
| 9 | 0.4407 | 0.5495 | +24.7% | 0.9947 |
| 10 | 0.4614 | 0.5651 | +22.5% | 0.9961 |

Floor 1 is already the approved native 492×369 asset and has no downscale step to correct. Floor 2 already uses the selected preserve-source recipe. Both remain byte-identical during the art rebuild.

## Root cause

Floors 3–10 were reduced with the legacy floor-1 pipeline: LANCZOS, strong unsharp masking, autocontrast, gamma, an 85% highlight ceiling, and a second Bayer pass. Their high-resolution sources already contain designed stipple, so the global curve and ceiling compress broad regional differences before the final one-bit encoding. The renderer creates only a rectangular label button at each coordinate; it has no visible endpoint glyph.

## Emergency mitigation

None. Production 0.111.1 is functional. This is a visual correction with no player-state or schema effect.

## Fix

1. [Phase 1](phase-1/PLAN.md): rebuild floors 3–10 with the measured preserve-source converter and add a reusable pixel location dot to every map marker.
2. [Phase 2](phase-2/PLAN.md): run coded and real-browser verification across all floors, version, deploy, and verify production assets and UI.

## Design contract

- Retain the approved wide, territory-scale compositions: forests read as forests, cities as cities, and major structures as massive landmarks with tiny entrances, buildings, and trees.
- Keep every final map at exactly 492×369, fully opaque, and restricted to black plus `(217,217,211)`.
- Preserve the existing label typography, numbering, instant tooltip behavior, keyboard digits, coordinates, and anchor rules.
- Add one 9×9 stepped pixel circle at every destination coordinate. Its 5×5 center is map gold and its two-pixel octagonal outline is black. The dot is decorative to assist sighted players; the existing button retains the accessible name and focus target.
- Center the dot at the exact configured `(x,y)` point. Center-, left-, and right-anchored labels attach from their center, left edge, and right edge respectively, so clamped labels do not move the indicated place.

## Verification

- Floors 1 and 2 remain byte-identical; floors 3–10 reproduce the hashes recorded by the preimplementation candidate run.
- All 10 files pass dimensions, opacity, and exact-palette checks.
- Floors 3–10 each have tone range at least 20% greater than their current asset and source correlation at least 0.993.
- Every rendered map button has exactly one decorative marker dot, aligned to its configured destination coordinate under all three anchor modes.
- Existing hover tooltips still appear instantly, digits 1–5 still activate destinations, and mobile labels remain inside the map.
- Targeted tests, plugin full suite, worldd full suite, and a real Chrome/Luna dojo walkthrough pass or record unrelated baseline failures exactly.
- Production health reports the released version and production map hashes match the release commit.

## Operational notes

- Work is isolated in parent/plugin branch `codex/088-all-map-contrast-markers`; the active durability, admin, research, and lore worktree is untouched.
- Reuse the saved sources and explicit `--tone-mode preserve-source` converter. Do not regenerate or redesign compositions.
- Commit plugin changes first, then the parent vendor pointer and execution records. Scan for secret patterns before every commit.
- Deployment is explicitly authorized by Roy's request to complete the remaining floors and deploy.

## Rollback

Revert the plugin asset/UI/version commit and the parent vendor/pointer commit. If deployed, push the revert, trigger Render, poll until live, and verify the previous version plus all ten previous asset hashes. No database rollback is required.

## Execution status

Complete and deployed — 2026-09-12. Floors 3–10 now use direct BOX reduction plus one Bayer encoding, every map destination carries the reviewed stepped gold/black point, and production 0.112.0 serves all ten exact release assets. Phase evidence and the Chrome walkthrough are recorded below and in `dojo/results/0064-088-map-contrast-markers-2026-09-11/summary.md`.
