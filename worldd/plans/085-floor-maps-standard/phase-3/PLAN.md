# Phase 3 — standard maps and black elevator

## Goal

All eligible players see maps on floors 1–10 without a Labs toggle. Labels, instant explanations, number keys and the opaque elevator behave correctly in both renderer consumers.

## Steps

1. `engine/floormap.py`: add per-floor layouts/descriptions, remove the Labs dependency, keep safe fallback for unmapped floors and absent live options. Resolve multiword/milestone warden names correctly (floor 10: GNARL).
2. `engine/labs.py` and `engine/tips.py`: remove `floormap` registry entry and toggle tip. Existing persisted flags are ignored, not rewritten. Update stale comments at core map seams.
3. `render.py`: retain chip styling and costs; make tooltip descriptions accessible and immediate on hover/focus; correct clipping/overlap if browser review finds it. Preserve residual option rows and mobile action usability.
4. `pane.py`: full overlay starts opaque black with no fade-in. Destination loads beneath it. Existing GIF direction/nonce/timing remains; reveal occurs only after the ride. Block hidden destination clicks/number shortcuts until reveal and remove blockers reliably on completion/cancellation.
5. Update relevant existing tests to express standard maps, and add meaningful regressions for all floor coverage, flag independence, floor-11 fallback, floor-10 marker, and opaque transition/input behavior. Use a separate worldd test file to avoid unrelated dirty test hunks.
6. Bump the plugin version; compare vendor/source then sync via `worldd/tools/vendor_game.sh`. Run targeted tests and inspect local rendered maps/rides.
7. Record execution status and commit plugin then parent. Re-read/amend phase 4 with actual runtime findings.

## Verification

- Targeted plugin map/Labs/render/keyboard/lift tests; vendor files byte-identical for changed package paths.
- Every map marker maps to one current option with matching displayed number. Conditional deep hunt absent when not offered; existing heal/stew/assistance options remain reachable.
- Browser: first frame and mid-ride reveal no destination pixels; ride end restores input; up/down/return correct; reload/peek/refusal quiet.
- Existing floor-1 artwork and ordinary non-map cards preserved.

## Rollback

Revert the plugin integration commit and parent vendor/pointer commit; restart the local services or redeploy if released. This restores the Labs gate and original elevator presentation without changing stored player documents.

## Execution status

Not started.

> retro(phase-1, 2026-09-09): Roy approved the original floor-2 design and requested only lower resolution. Keep map_002_v1 composition, ship 492×369 like floor 1, and use its geography/scale alongside floor 1 as a reference. Do not perform the proposed texture redesign.
