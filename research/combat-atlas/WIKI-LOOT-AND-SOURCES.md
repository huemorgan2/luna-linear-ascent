# Wiki, creature loot and weapon starting settings

12 September 2026. Proposed settings, not a live combat or economy migration.

The game website's `/wiki` replaces the eight illustrative creatures with all **425 authored creatures and 425 distinct images on 100 floors**. The floor slider changes the actual roster and environment. Species keep fixed proposed profiles; future same-animal recolors are limited to three nearby variants. Current HP, attack, defense, speed, body/bite traits and specimen rules come directly from the deployed engine. Draft Power/Magic/Air badges use its pixel icons. Typography is the website's IBM VGA at 16px throughout. Rare uses game Aether teal; Epic uses Violet; Legendary uses gold. Rarity frames differ in both color and pixel outline.

## Weapon drawings by grade

Revision089.3 assigns **64 distinct drawings**: four for every one of the16 families. Grade identity changes the weapon's silhouette, blade or limb construction, handle and focal details. Common is rough and practical; Rare is forged and reinforced; Epic is elaborate or charged; Legendary uses exceptional shapes, suspended cores or radiant structures. Frame color remains an additional cue.

Each weapon has an explicit `artByGrade` record with its asset source and visual description. There is no single-image fallback. Arsenal cards, Forge portraits, acquisition rows and details all resolve that same family-and-grade record. Opening any weapon shows four selectable designs side by side, with a two-column layout on phones. Choosing one updates its source settings and the shared grade controls.

61 portraits are distinct existing game assets. Three new Thunder Maul portraits fill missing Common/Rare/Legendary shapes: wooden mallet, steel hammer-and-beak, and floating split-shard hammer. Epic uses the existing Ironstorm Maul drawing. Original generated PNGs and the exact prompts are preserved under `worldd/static/site/wiki/weapons/` and `worldd/plans/089-game-wiki/phase-3-grade-art/PROMPTS.md`. These are the wiki's proposed item identities for later adoption by game inventory UI. Upgrade level and remaining endurance do not select a different rarity drawing.

## Source settings

Every family has its own editable acquisition record in `worldd/static/site/wiki/model.json`. Defaults are below; there are 16 families × four grades, all displayed in the wiki.

| Grade | Bought level | Bought condition | Shop floor | Dropped level | Dropped condition | First possible drop | Equip dropped weapon |
|---|---:|---:|---:|---:|---:|---:|---:|
| Common | 0 | 100% | 1 | 0 | 40% | 1 | 1 |
| Rare | 2 | 100% | 28 | 0 | 30% | 1 | 26 |
| Epic | 4 | 100% | 57 | 0 | 20% | 1 | 51 |
| Legendary | 6 | 100% | 84 | 0 | 10% | 50 | 76 |

Every family also has an explicit **Forge crafting source: +0 and 100% endurance at Floors1/26/51/76**. It costs the base gold charge and that family’s paired material recipe. The wiki shows the exact quantities for all64 variants. This prevents a grade-transition gap before the +2/+4/+6 shop stock opens: a player can gather materials and craft, rather than depend on a very rare weapon drop.

Condition means remaining endurance / maximum endurance, rounded to an integer. The wiki gives both numbers for each weapon. Its attack column is full-condition weapon contribution; repair is needed to recover a damaged drop's performance. Shop price includes base acquisition and upgrade charges through the delivered level. The player does not pay these upgrade costs twice. Crafting at a higher configured starting rank would sum the gold and recipe quantities through that rank; the present craft settings are all+0. Materials are included in the bought item; subsequent upgrades consume gold and materials in the Forge.

Starting a bought Legendary at +6 shifts its shop availability to Floor84. Giving Floor84 damage at Floor76 would violate the existing exponential curve. A lucky early discovery can be saved or traded, but its equipment gate remains. The neutral upgrade reference matches the existing honed weapon contribution at **every floor1–100**, including hold floors. Honing and the new upgrade multiplier must never apply together. This protects the existing reference, but the proposed abilities, loot economy and damaged-item repair loop still need simulation before implementation.

## Loot rules

The wiki has a searchable, image-bearing 425-row table with two visible views: **Drop chances** and **Creature parameters**. Choose all floors or an individual floor, normal/deep hunting, and runt/common/tough/alpha. A creature dossier lists every weapon family's individual drop chance as well as all four rarity chances.

Material rarity is four independent rolls: more than one grade can succeed. Each successful grade grants that grade's paired materials. Weapon rarity is one categorical roll, with at most one item; `no weapon` completes the probability to100%. Other consumable/armor drop categories are not assigned new rarity settings in this proposal. Wardens use shared encounter rewards and are outside hunt-creature rolls.

Floor baseline percentages are piecewise interpolated from the tables in `model.json` and printed in the wiki. Multiply by body × bite × specimen × hunting-ground bonus. Unlisted traits use1. Species are deliberately unequal:

| Factor | Values |
|---|---|
| Body | frail0.65, lean0.9, sturdy1.15, hulking1.45 |
| Bite | feeble0.65, fierce1.2, savage1.5 |
| Specimen | runt0.5, common1, tough1.35, alpha2.25 |
| Deep material multiplier, Common/Rare/Epic/Legendary | 1.15 / 1.5 / 2 / 3 |
| Deep weapon multiplier, Common/Rare/Epic/Legendary | 1.25 / 1.75 / 2.5 / 4 |
| Caps | each material grade95%; all weapon grades combined50%, proportionally scaled |

Example: Floor1 Grey wolf has 2% Common materials, 0.001% Epic materials, 0.3% Common weapons and 0.00002% Epic weapons. The stronger Feral boar pays 1.38× those chances. Legendary discovery stays zero below Floor50. At Floor80, the master's remount in common specimen form gives a Legendary weapon at0.05618571% in normal hunting and0.22474286% in deep hunting; an alpha deep specimen gives0.50567143%.

Air favors bow families, Ground Magic favors staves, and Ground Power favors blades at3× family weight. Common ground uses1 per family. Individual family probability = creature's grade chance × family weight / sum of all16 weights. This makes target selection useful without promising equal farming speed.

Material carriers preserve different recipe routes: Air carries A-heavy bundles (3Y:1Y), Power ground B-heavy (1Y:3Y), others mixed (2Y:2Y). Y=min(5,1+floor(max(0,floor−grade-start)/6)); grade starts1/26/51/76. Materials remain Wood/Raw Metal, Hardwood/Steel, Meteorite/Starforged Steel, Mythic Threads/Shard Matter. These are draft quantities; caps can saturate at high levels and should be evaluated against upgrade material sinks, time and survival cost.

## Existing deep-hunt rules retained

Deep hunting unlocks on Floor4, costs2 entry energy, excludes frail/feeble creatures, and has no runts. It adds20% attack and1 speed. Its current specimen mix is common45%, tough35%, alpha20%. Its current XP/gold multiplier rises with floor and reaches3.4 at Floor10. These are current rules; the rarity multipliers above are new proposals. Displayed authored encounter share is not the player's final encounter chance (mercy/prey fade and filtering can change selection).

## Implementation boundary

This change serves public reference HTML/CSS/JS, a generated data bundle and a homepage link. No game action, player inventory, drop algorithm, shield behavior, raid or database state is changed. Shared wardens remain a proposal for **continuous healing against concurrent real attacks**, including Floor100; no stored pledge pool is introduced. Mining remains a separate project.

Canonical inputs: `worldd/static/site/wiki/model.json` and the vendored game content/economy. Rebuild with `python worldd/tools/gen_wiki.py`; verify with `--check`. `worldd/plans/089-game-wiki/PLAN.md` records execution and rollback. The former independent Combat Atlas is superseded by the game wiki for this reference.

Editable settings and the implementation are committed on `codex/089-game-wiki` and `main`: [weapon/source model](https://github.com/huemorgan2/luna-linear-ascent/blob/main/worldd/static/site/wiki/model.json). The original research checkout is retained separately so unrelated ongoing changes remain untouched.
