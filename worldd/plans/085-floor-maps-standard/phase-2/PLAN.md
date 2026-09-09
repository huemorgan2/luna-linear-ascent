# Phase 2 — complete the map artwork for floors 1–10

## Goal

Nine new, distinct maps accompany the unchanged floor-1 reference, each visually accepted and with documented landmark coordinates.

## Steps

1. Apply phase-1 findings to every remaining prompt before generation.
2. Generate floors 3–10 with separate built-in image calls, using the reference map and consistent scale/light/dither instructions. Store selected source and prompt per floor.
3. Apply the accepted grid-enforcement pipeline. Inspect every native output and a contact sheet for consistency; inspect cavern and dense-forest maps individually for flattened shadows/noisy texture.
4. Annotate actual gate, camp, return, keep, hunt and deep-hunt anchors. Check that the projected HTML chip rectangles can fit on phone and desktop without covering key structures.
5. Record coverage, file hashes, output paths and visual decisions. Commit; amend phases 3/4 with discovered constraints.

## Verification

- Exactly maps 001–010 available; floor 1 unchanged; all final maps 492×369 and two-color opaque PNGs.
- Every map passes the style contract by visual inspection; there is no repeated generic landscape or oversized doorway/tree.
- Full prompt/source manifest and anchor notes exist for future map batches.

## Rollback

Revert phase-2 additive assets and records. No runtime changes have shipped yet.

## Execution status

Not started.

> retro(phase-1, 2026-09-09): Roy approved the original floor-2 design and requested only lower resolution. Keep map_002_v1 composition, ship 492×369 like floor 1, and use its geography/scale alongside floor 1 as a reference. Do not perform the proposed texture redesign.
