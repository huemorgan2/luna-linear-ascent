# Dojo 087 — floor-2 contrast preservation

## Preconditions

- Local worldd and QA Luna use this branch's source package and isolated QA databases.
- A disposable player can reach floor 2. The old and candidate assets plus the approved 1448×1086 source are available for side-by-side review.

## Scenario

1. Open floor 2 in a desktop browser and capture the full map plus DOM snapshot.
2. Compare the lower-left and mid-left lakes, central tower shadow, upper ridges, fortress, quarry roads, and tiny Lampfall roofs against the approved source and old output.
3. Hover and keyboard-focus every marker; press the displayed GATE number and return to floor 2.
4. Repeat at 320px and capture the map with all chips visible.
5. In QA Luna, type `show me floor 2`, inspect the rendered pane, then reply with the displayed GATE number.

## Expected behavior

- Lakes and deep valleys read as distinct dark tonal masses; lit ridges and quarry faces remain visibly lighter.
- The source composition and tiny scale references remain intact.
- The image remains crisp one-bit pixel art, with no gray pixels, moiré wash, or new labels baked into the bitmap.
- Existing HTML markers, descriptions, costs, and numbers remain readable and route correctly.

## Fail conditions

- Water and adjacent ground merge into one texture density.
- Roads, small doors, roofs, rails, or the fortress silhouette disappear.
- The image contains non-palette pixels, changes dimensions, or shifts/crops geography.
- Any marker overlaps, clips, misroutes, or appears in the bitmap itself.

## Verify

- Record image dimensions, palette, hashes, territory-block metrics, and unchanged-map hashes.
- Confirm the browser loads the new versioned floor-2 URL and its bytes equal the selected local asset.
- Compare player state before/after the read-only Luna scene request and verify only the intended GATE action mutates location.
