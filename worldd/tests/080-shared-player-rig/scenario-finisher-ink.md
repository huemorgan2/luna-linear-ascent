# 080 scenario — finisher ink (phase 2: bodies separate, weapons read)

## Preconditions

- Local worldd on :8600, phase 2 deployed locally.

## Scenario

For each of: `grey_wolf&race=human&line=blade`,
`ember_shade&race=elf&line=bow`, `orc_overseer&race=giant&line=staff`,
`warden_002&race=human&line=blade&breed=wrongmade`:

1. Open `/static/site/fight3d/test.html?id=…&tint=%239ae6b4`.
2. Screenshot at approach (~3 s), strike (when the lunge lands), and
   aftermath.
3. Zoom-crop the player and the weapon at each moment.

## Expected behavior

- The player body shows the portrait look: solid-black shadow core, bright
  lit side, continuous dither rolloff — NO visible banding steps.
- The figure separates from the scenery at a glance (different dither
  density / solid regions, plus the black contour line).
- The weapon is identifiable in every frame — against sky AND against the
  dark scenery strip.
- Monsters remain readable; the tint stays the ONLY color.

## Fail conditions

- Concentric band edges on body or monster (posterize look).
- Body reads as a flat noise patch that merges with the background.
- Weapon vanishes at any of the three moments.
- Bodies or monsters crushed to featureless solid black.

## Verify

- Repeat one case with a red tint (`%23f26541`) and one amber — the curve
  must hold across tints.
- Arena stage spot-check (same shader): open the Labs arena harness or a
  /play arena fight; same judgment.
