# Phase 1 — reference, baseline and floor-2 canary

## Goal

Produce one floor-2 map that meets the top-level design contract and can be reproduced from its stored source/prompt. Floor 1's bytes must remain unchanged.

## Steps

1. Record hashes/versions and source/vendor differences. Inspect the final floor-1 map, source and phase-1f/1g shading records.
2. Capture the current map and elevator behavior in the running local browser where available. Confirm transparent full overlay versus opaque GIF rectangle.
3. Store an image prompt manifest with common style plus per-floor briefs, and a parameterized version of the accepted `mock-map/map_gen.py` conversion recipe. Keep source images versioned outside the shipped package; final PNGs go in `plugin_linear_ascent/content/art/maps/`.
4. Generate only floor 2 with floor 1 as style reference. Inspect source and native-grid output, landmark proportions, terrain gradients and prospective marker regions. Iterate a single issue at a time if needed.
5. Record floor-2 marker anchors from the actual output and visual/tonal evidence. Commit the phase and update remaining phase plans with what the canary taught us.

## Verification

- SHA-256 of floor 1 unchanged.
- Floor-2 final: 492×369, two opaque colors, no text/border, legible district-scale geography and tiny entrance/window/tree references.
- Native-size and enlarged visual inspection alongside floor 1; planned marker overlay readable at 736px and phone width.
- Source, prompt, recipe and final paths recorded in execution status.

## Rollback

Revert the phase's additive generator/source/asset commit. Runtime is unchanged, so no player or deployment rollback is needed.

## Execution status

Not started.
