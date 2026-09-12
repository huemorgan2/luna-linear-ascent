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

## Loot and acquisition extension

9. Open Creature Loot, confirm all425 rows. Filter Floor80 and compare normal/deep common specimens. The master's remount must have about0.05618571% versus0.22474286% Legendary weapon odds. Feeble creatures show unavailable in Deep. Switch to Alpha; its chance rises to0.50567143%. Select runt in Deep: none are eligible. Switch Normal to restore runt outcomes.
10. Switch the visible table view between Drop chances and Creature parameters. Creature images/names persist. Search remount; inspect the dossier's16 weapon-family probabilities and the staff's3× weight. Clear search and restore all floors.
11. Open Weapon Sources, confirm64 rows. Legendary Ramguard shows shop+6,4798/4798 END,Floor84; drop+0,449/4486 END (10%),first find50/equip76. Open it and choose Upgrade in the Forge: both rarity controls stay synchronized. Inspect other grades' starting levels and condition.
12. On phone width, repeat the dossier and loot controls. Tables may scroll internally. Keep all text16px and avoid page overflow. Inspect console errors and loaded asset dimensions.
