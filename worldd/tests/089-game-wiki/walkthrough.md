# 089 — wiki browser walkthrough

## Preconditions

Local worldd serves this branch. No player login is required for the wiki; no production character is modified. Current floor content has 425 unique encounter IDs. Capture screenshot evidence and a numbered report.

## Scenario

1. First user action: open `/wiki` from the website's Wiki link.
2. Read the opening cards and compare their game font/icons with the homepage.
3. Move the bestiary slider to floors1,3,25,50,80,100. Read names and inspect images. On floor3 find Marsh adder in The Drowned Pasture; each floor must replace the roster, not rescale eight placeholders.
4. Select each enemy profile, arrow payload, distance and rarity through visible options. Only a selector with more than six entries (weapon family) may use a dropdown.
5. Open a weapon, inspect its effect, recipe and stats. Change grades and upgrade0/20. Compare AirPower with ordinary and arcane arrows. Verify blades cannot hit Air or distant Ground.
6. Raise shield defense and turn on Shield wall. Some HP loss remains; wear equals the shield's absorbed damage. Inspect movement/raid examples.
7. At390px width, navigate sections, use the floor slider and open weapon details. No clipped controls or horizontal page overflow; tables may scroll internally.
8. Reload a deep link and repeat a selection. Confirm no game action/session is required.

## Expected behavior

Every text node uses the game VGA font at16px; hierarchy comes from color, spacing and borders. Pixel icons come from the game module. Current creatures and stats are distinct from draft combat rules. Selected rarity has the future frame style and color. Different floors show their actual creatures and distinct art. Each visual creature identity has at most three defensive-profile variants; this release uses one per species.

## Fail conditions

Eight fixed examples on every floor; shared silhouette across unrelated species; randomized profile changes; short dropdowns; mixed fonts/sizes; missing icons/art; a shield reducing a landed hit to zero; unpublished proposed rules presented as live; any player state mutation.

## Verify

Read the browser DOM and screenshots. Check every encounter image against the generated content data, all425 IDs and100 floors. Verify successful HTTP responses and correct deployed revision after publication. Report failures separately and retest fixes.
