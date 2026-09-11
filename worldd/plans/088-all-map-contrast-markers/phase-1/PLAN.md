# Phase 1 — tone-preserving assets and exact location dots

## Goal

Ship reviewable plugin code in which floors 3–10 retain their source-defined regional shading and all floor-map links visibly terminate at their exact configured map coordinate, while floors 1–2 and all navigation behavior remain stable.

## Steps

1. Record all ten input/output hashes and the preimplementation territory metrics.
2. Run `prepare_map.py --tone-mode preserve-source` on saved sources 003–010 into the plugin's canonical map paths.
3. Add one decorative marker-dot child to `_map_html` and CSS for a 9×9 stepped black ring with a 5×5 gold center. Align it to center, left, or right according to the existing label anchor.
4. Add focused renderer and asset tests, including all ten palettes, marker count, accessibility decoration, and anchor CSS.
5. Inspect all eight changed PNGs at native scale and render representative left, center, and right anchored markers at desktop and phone widths.
6. Commit the plugin implementation after targeted and full plugin tests.

## Verification

- Floors 1 and 2 SHA-256 remain `2b47403f91a4e74bfb476f8ef9e0f9835dbe8e5422e45abea8edc1f55c2be5b5` and `d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e`.
- Floors 3–10 match the candidate hashes in `evidence/metrics.json`.
- Every PNG is 492×369 RGBA, alpha 255 everywhere, with exactly black and `(217,217,211)`.
- Renderer tests prove one `aria-hidden` dot per destination and all three anchor offsets.
- Visual inspection shows distinct dark water/forest/shadow and bright road/stone/snow regions without changing composition.

## Rollback

Revert the plugin implementation commit. This restores all image bytes and removes the dot markup/styles; there is no data migration.

## Execution status

Complete — 2026-09-11.

- Rebuilt floors 3–10 from the saved 1448×1086 sources with `--tone-mode preserve-source`; their output hashes match `evidence/metrics.json`. Floors 1 and 2 remained byte-identical at `2b47403f…be5b5` and `d5d46a03…8f9e`.
- Added one decorative `mkdot` inside each existing marker button: a 5×5 gold center with a stepped two-pixel black outline, centered at the configured coordinate for center/left/right anchors.
- Preserved the established first-child `mknum` markup after the first vendored full run exposed that contract in `test_085_floor_maps.py`.
- Focused renderer/asset suite: 61 passed. All ten assets proved 492×369 RGBA, fully opaque, and limited to black plus `(217,217,211)`.
- Plugin implementation commits: `32ceff18` and compatibility fix `92c86b6f`; release version commit: `3ce3448c`.
