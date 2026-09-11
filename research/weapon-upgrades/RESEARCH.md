# Weapons, materials, and progression through the tower

The recommended direction is a small collection of lasting weapons: **blade, bow, and staff in Common, Rare, Epic, and Legendary grades, each with upgrade levels 0–20**. Weapons consume gold and their grade's materials at the Forge. Hunting supplies materials now; mining is a separate future project.

The existing exponential economy should provide the reference curve. It should not make every route equally good. Knowing which creature to hunt, bringing its counter, choosing a suitable weapon recipe, preserving a valuable weapon, and coordinating with other players should produce a measurable advantage. Random drops add uncertainty around those decisions; they should not replace the decisions.

This is a research proposal, not an implemented balance change. The accompanying [progression tables](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/weapon-upgrades/PROGRESSION-TABLES.md) contain every proposed upgrade and every floor's material rates. [Validation and limitations](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/weapon-upgrades/VALIDATION.md) separate arithmetic checks from work that still requires engine simulations and real browser play. [Boss systems](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/weapon-upgrades/BOSS-SYSTEMS.md) examines the newly identified pledge mechanic. The [mining plan note](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plans/013-mining-and-gathering/PLAN.md) is outside the weapon implementation scope.

## What exists now

The evidence is the local checkout examined on 11 September 2026: root commit `c52fa21d546171e9e950a1c2c9155ebef6231dcb`, plugin commit `2f9cfff5557cde824091e8e2ce9107171ba80024`, plus existing working-tree changes. These are source findings, not a production-state audit. The plugin and vendored `economy.py` were byte-identical when inspected. The mechanics page's reference attack values matched the imported economy on all 100 playable floors. [S1–S4]

| Area | Current behavior | Consequence for this proposal |
|---|---|---|
| Catalog | `FORGE` contains 285 records: 145 weapons, 87 shields/focuses, 48 armor, 5 shoes. Weapons include 141 paid records and 4 zero-price starter/compatibility records. | Reduce paid weapon templates to 12. Keep starter compatibility; leave defensive catalogs alone. |
| Weapon paths | Blade, bow, staff; training ranks 0–10. Internal catalog lines retain warrior/archer/sorcerer names. | Preserve matchups, training, range, mastery, and carrying several weapons. |
| Shopping | Many named rungs; dense early ladder, whole tiers and midpoints later. Physical weapons at Forge, paid staves at Arcanum. | Lasting cards replace repeated purchases. Arcanum can introduce staves, but all weapon upgrades use Forge. |
| Honing | Weapon honing is stored by weapon slug. Each hone multiplies weapon bonus by 1.3. Shield/armor honing remains per slot. | Weapon level replaces weapon honing. Applying both would double-count growth. |
| Weapon condition | Generally one durability use per swing. Broken weapons provide half strength. Starter weapons also wear. | Show current/max condition and increase maximum durability with upgrades. |
| Styles | Early keen variants: ×1.15 bonus, ×1.40 price, ×0.65 durability. Warded: unchanged bonus, ×1.20 price, ×1.75 durability. | Preserve meaningful tradeoffs, especially for existing owners; do not confuse these with rarity. |
| Item identity | Inventory is slug → quantity; wear and weapon hone use slug-based maps. | Different upgraded copies need instance IDs, or an explicit one-copy-per-template restriction. |
| Pack | Starts with six stacks. A stack is one slug at any quantity; loot may overflow rather than disappear. | Eight new material slugs would overwhelm the first pack without dedicated material storage. |
| Drops | Wilds give gold/XP; alpha and warden loot tables award consumables. “Rare loot” is not a general weapon rarity system. | Add material awards at resolved wilds victories, with their own probabilities and receipts. |
| Death | Beyond beginner protections, paid weapons can be permanently lost with 20% probability each. At player level 6+, ordinary unprotected death takes 90% of carried gold and can lose a whole inventory stack. | Months invested in one weapon make the old destruction rule much more consequential. Define weapon and material death behavior explicitly. |
| Progress | Character level caps at 30; floor and gear progression continue to 100. | Never gate Legendary equipment behind “player level 76.” |

The detailed engine supersedes several old vision and research passages. In particular, the old linear `3 × level + weapon` narrative and a floor-100 quorum of 12 are not a reliable description of the current calculation. [S1, S5–S8]

## The progression law to preserve

Let `F` be tower floor, `L` character level, and `u` weapon upgrade level. These are three different quantities.

```text
P(F) = 1.3^(F−1)                    power and capital-cost curve
I(F) = (1.3 / 1.04)^(F−1) = 1.25^(F−1)   underlying income curve
W(F) = 1.04^(F−1)                   increasing time cost relative to income

player attack = round(3 × P(min(L,30))) + weapon bonus
player HP = round(52 × P(min(L,30))) + 4 × armor bonus
baseline boss-body HP ∝ (1.3 × 1.02)^(F−1)
```

Actual gold has early-floor bonuses and a gold-to-XP floor; `daily_income(F)` is a design estimate based on unbonused income and an estimated healing allowance, not a measured player paycheck. Capital and running costs deliberately use different curves. Repairs must not start charging a fixed percentage of the sum of every historical upgrade payment. [S1]

The research uses the existing **reference weapon bonus** as its neutral attack anchor. It does not normalize damage against different monsters, flatten the class triangle, or promise equal rewards for every hunt. An efficient player should reach the useful part of the ladder sooner, spend less recovering, and outperform someone using the wrong counter.

### Four grades can cover the existing curve

| Grade | Main floor range | Materials | Material IDs proposed |
|---|---:|---|---|
| Common | 1–25 | Wood + Raw Metal | `wood`, `raw_metal` |
| Rare | 26–50 | Hardwood + Steel | `hardwood`, `steel` |
| Epic | 51–75 | Meteorite + **Starforged Steel** | `meteorite`, `starforged_steel` |
| Legendary | 76–100 | Mythic Threads + Shard Matter | `mythic_threads`, `shard_matter` |

Starforged Steel is a working name for “XXX Steel,” not established canon. Shard Matter is the normalized spelling of “Shard mater”; existing shardmind lore should be checked before giving it a final description.

Each grade has 21 states. Most current decades have two floors where reference weapon attack stays unchanged while the body or other equipment progresses. Reusing those plateaus allows the grade/level schedule in the tables to reproduce every current floor's reference weapon bonus exactly. It does not require adding an invisible second progression system.

Two Epic steps, **+17 and +18 at floors 72 and 73**, increase durability without increasing reference attack. The card must say so. This is an intentional conservative candidate, not a requirement that the eventual design fit every old point. If those steps feel unrewarding in play, move some attack growth between adjacent Epic steps and measure the resulting advantage. Do not pad them with unnoticed critical-hit or regeneration multipliers simply to make every preview show a larger attack number.

The theoretical fully upgraded path matches the curve. A player who has not earned the next level remains behind it. Material availability, money, floor access, and training still determine actual progress.

### Keep a small catalog without erasing choice

Use 12 paid templates: four grades each of blade, bow, and staff. Keep three playable starter paths and the existing starter alias for compatibility. This changes 145 weapon catalog records to a target of 16 records including that alias, with 15 visible faces. Legacy names and art can survive as skins or retired collectibles rather than becoming extra numerical rungs.

Rarity belongs to the template; upgrading changes its level, not its rarity. A Common +20 remains Common. Reaching a new grade opens a new recipe without requiring destruction of the old weapon or completion of every old-grade level. That makes deciding when to stop investing in an old weapon part of good play.

All new-grade +0 weapons still require gold and materials. There is no random chance to fail a paid upgrade. Scarcity comes from obtaining inputs, deciding where to spend them, and opening the next part of the tower.

## Make knowledge matter more than a lucky streak

### Recipes should prefer different materials

For a grade, call the first material in the table above **A** and the second **B**. The upgrade tables give a recipe quantity `Q`.

| Weapon | Material A | Material B | Player decision |
|---|---:|---:|---|
| Blade | `Q` | `3Q` | Hunt metal- or shard-bearing creatures. |
| Bow | `3Q` | `Q` | Hunt wood-, meteorite-, or thread-bearing creatures. |
| Staff | `2Q` | `2Q` | Balance sources or target creatures carrying both. |

Those are proposed bill-of-materials proportions. They can be themed per weapon later; they should not be silently forced to produce equal completion times on every floor. A biome can legitimately favor bows, and another can favor blades. Existing elemental counters may make the richest material carrier dangerous for the weapon being upgraded, creating a reason to carry and train a second path.

### Creatures should have different opportunities

The floor table gives **baseline grade-discovery probabilities**, not identical probabilities for every creature. Each eligible creature receives content-authored material affinities. These modify the grade probability and the composition of a successful bundle.

| Creature opportunity | Grade-chance multiplier | A:B bundle composition | Tradeoff |
|---|---:|---:|---|
| Ordinary mixed carrier | 1.0 | 2:2 | Broad fallback; no special preparation. |
| Recognizable A carrier | 1.0 | 3:1 | Better for bows; worse for blade bottlenecks. |
| Recognizable B carrier | 1.0 | 1:3 | Better for blades; worse for bow bottlenecks. |
| Rich carrier | 1.25 | Authored 3:1 or 1:3 | Better chance, but content must justify extra combat risk or reduced encounter frequency. |
| Sparse carrier | 0.5 | Authored composition | Easy prey can remain useful for gold or safe survival without being the best material farm. |

Chance is capped at 90% after modifiers; no roll yields a negative quantity. Each successful grade roll awards `4 × Y` total units in the stated proportions. Four grade rolls are independent, so one victory can contain several grades. The four percentages therefore need not sum to 100%. Affinity, specimen, and deep-hunt effects must be disclosed in the creature's loot preview.

`Y = min(5, 1 + floor(max(0, F − grade_start) / 6))`. A grade discovered before its normal band produces one bundle unit. Higher quantities accompany deeper access, with a cap so old materials do not inflate without limit.

For specimens, start with bundle multipliers: runt 0.5, common 1, tough 1.5, alpha 2. Use unbiased stochastic rounding of quantities; award the resulting A/B package atomically. Treat these as candidate reward values and validate them against win chance and energy. Do not boost both chance and quantity for every modifier by habit.

The existing deep hunt costs two energy and offers a risky roster. Its gold/XP premium is already designed around approximately 1.2–1.5 times ordinary returns per energy. Start material quantity with the existing `deep_reward_mult(F)`, then evaluate real survival and specimen mixes. This is a starting hypothesis; copying the gold multiplier is not proof that material economics are balanced. [S1, S6]

### Give players a way to act on the information

Current hunts select an encounter from weighted tables; they do not generally let the player request a named creature. Add a small choice of **hunting trails** in the weapon/material work: for example “wood-bearing tracks” and “metal-bearing tracks.” A trail changes encounter weights, not damage rules, and makes no guarantee of a particular spawn. This is hunting UI, not mining.

A proposed trail might give a 70% chance of its advertised carrier family and 30% of the remaining roster. The ordinary hunt remains available. Costs are charged when the hunt begins; refreshing a preview cannot reroll it for free. Show the likely creatures, favored materials, and danger before spending energy. These are proposed encounter-weight choices, not a claim that all floors already have suitable carrier families.

For example, at floor 35 the candidate Rare probability is 39.29% and `Y=2`. A Rare +10 blade needs 16 Hardwood and 48 Steel. A B carrier awards 2 Hardwood and 6 Steel per successful Rare roll, while an A carrier awards 6 Hardwood and 2 Steel. The B carrier takes eight successful bundles; the A carrier needs 24. At equal encounter chance and win rate that is a threefold difference from knowledge alone. With a 70% B / 30% A trail, expected Steel per successful material roll is 4.8, versus 3.2 on the opposite trail. The route advantage remains even after encounter uncertainty. This example uses floor 35 to gather for a later recipe; equipping +10 still requires its floor gate.

Do not describe a ratio-of-expectations estimate as an exact completion time. Losses, changing inventory bottlenecks, encounter draws, gold, and healing all affect the realized result.

### Fairness does not mean equal outcomes

Allow efficient hunting, scouting, timing upgrades, saving money, and route choice to accelerate progress. There is no target that everyone must take exactly the same number of days. A useful experimental target is a **25–50% reduction in time to a chosen upgrade** from informed play across representative routes, with larger wins in especially favorable local situations. This target remains to be demonstrated.

Keep some fallback access to both materials so a poor route is slower rather than permanently impossible. Early Epic discoveries should be memorable, but a rare drop cannot bypass equipment floor gates. Do not sell an unrestricted upward conversion from Wood to Shard Matter.

An optional dry-streak safeguard can guarantee a normal-grade bundle after a long run of eligible wins. It must apply only to the grade native to the player's current progression band, preserve the creature's material composition, and persist across refreshes. It must not turn every early Epic or Legendary discovery into a predictable farm. The supplied probability and pacing calculations exclude this optional safeguard.

## Upgrade costs and pacing

### Gold

At a grade/upgrade state's gate floor `S`, the candidate gold charge is:

```text
G(grade,u) = ceil(C_grade × 1.3^(S−1))
C_common = 125; C_rare = 47.5; C_epic = 53.5; C_legendary = 47.5
Exception: acquiring Common +0 costs 200 gold, preserving the current paid entry weapon price.
```

Within each grade, every upgrade costs more than the previous upgrade. The underlying exponential is the existing capital curve. Gaps between upgrade gates can produce larger steps; they are not a second compounded rarity multiplier. New-grade acquisition is separate from an upgrade and can reset its local material quantity and price schedule.

The coefficients were chosen against an explicit current reference route: buy each early reference rung, buy each new whole-tier weapon, and pay for each increase in reference honing thereafter. No pawn refunds, interest, gifts, deaths, mid-rung shortcuts, or training expenses are included. Comparing gold divided by the same floor's `daily_income` keeps an exponential price from appearing cheap merely because the table uses huge late-floor incomes.

This reference is an accounting benchmark, not optimal current play. Real players can skip purchases or use mid-rungs. Therefore the proposal must also be compared against optimized current routes before release. It is acceptable for a smarter new route to be faster; it is not acceptable to claim unchanged progression solely from the reference route. The candidate's effort index is +0.18% versus this route, but its total nominal gold spend is +39.40% because payments move between floors. Bank balances and interest therefore need a separate whole-account check before the prices are frozen.

The Common coefficient is higher because the old early progression repeatedly buys replacement weapons. Later coefficients distribute those larger shop purchases across persistent upgrades. They are not an intrinsic claim that ordinary wood is more valuable than mythical materials.

### Materials

```text
Q(grade,0) = A_grade
Q(grade,u) = max(Q(grade,u−1) + 1, ceil(A_grade × 1.18^u))
A_common = 1; A_rare = 3; A_epic = 8; A_legendary = 20
```

Multiply `Q` by the weapon's A:B recipe coefficients. This gives an exponentially rising requirement, with a minimum one-unit increase so small rounded costs do not remain unchanged. For example, Common +20 requires `Q=28`; Legendary +20 requires `Q=548`. A Legendary +20 blade therefore spends 548 Mythic Threads and 1,644 Shard Matter for that step. The cumulative column includes acquisition and every preceding level of that grade.

At floor 1 the ambient Common roll is 2%, Rare 0.05%, Epic 0.001%, Legendary zero. A successful Epic roll is about one in 100,000 eligible ordinary victories before creature modifiers. The probability table increases access to better grades as the tower rises. Legendary ambient drops begin only at floor 50 in this candidate and become practical in the 70s; Legendary mining still requires the future high-floor sites.

Give the first tutorial wilds victory a clearly labeled, one-time bundle sufficient for the starting path's Common +0 recipe. Gold still gates the purchase. This teaches the material loop without making a new player wait for a 2% roll. It is an exception to ambient rarity, not an extra repeatable material source. All further mandatory progression must work with animal/creature drops alone while mining is absent.

### Model money and materials together

Inputs accumulate during the same hunts. Time is approximately the maximum of the remaining gold time, the remaining material time, and the progression gate—not the sum of two independent grinds. Conversely, a player hunting a low-paying route for one missing component may delay their gold goal. Model the player's actual chosen route rather than treating the two balances as independent.

The table's illustrative gold time allocates 60% of the current design `daily_income` estimate to the main weapon. That estimate already subtracts a generic healing allowance, so 40% is an additional reserve for other commitments, not another claim about the actual healing tax. Pacing examples assume 30 successful ordinary hunts per day. Failures, deep-hunt energy, sleep, and warden participation require different counts.

For a recipe-matched carrier, enough successful bundles means `K = ceil(Q/Y)`. With grade probability `p`, the expected eligible kills are `K/p`. The 90th percentile is the smallest `n` for which `Pr[Binomial(n,p) ≥ K] ≥ 0.90`. The validation document also examines an unfavorable carrier; a deliberately bad route should be slower.

Do not turn these estimates into a promise of a four-to-six-month season. Even the current reference capital route represents hundreds of design-income days before account interest and other faucets. Actual population progress and optimized play must establish elapsed-time expectations.

## Attack, durability, and meaningful secondary choices

For the neutral template, store the attack bonus of the old reference weapon at the state's gate floor. Remove the old weapon-hone multiplier from its stat calculation. Preserve the existing character attack contribution, training, class counters, range, and mastery.

The proposed maximum weapon durability is `round(1300 × (1 + 0.025 × (S−1)))`, using the table's gate floor. This interpolates the current tier-based durability shape, rises on every level, and reaches roughly 4,518 uses at floor 100. That is a maintenance change: honing previously raised attack without raising maximum weapon durability. Measure the resulting repair frequency.

On an upgrade, preserve **absolute missing durability**: `new_current = max(0, new_max − (old_max − old_current))`. The new capacity arrives intact, but old wear does not vanish. Require repair of a broken weapon before an upgrade so the upgrade cannot become a cheap bypass of the repair bill. Show the combined quote if the player chooses both operations; it must still settle atomically.

For new weapons, begin with the existing tactical distinction among blade, bow, and staff. A later temper choice can reuse the current keen/warded tradeoff as a separate Forge option, with costs and condition consequences shown explicitly. Do not multiply a rarity bonus, hone bonus, level bonus, temper bonus, mastery bonus, and new proc bonus without measuring their product. An optional strong temper should have an opportunity cost, not a hidden universal penalty that makes every build identical.

Potential secondary benefits to prototype include longer-lasting oil, reduced repair frequency, or a stronger narrow matchup at the expense of another. Avoid adding passive player healing, energy regeneration, armor penetration, stacking damage-over-time, or boss-heal suppression in the first material release: these change the social combat math, not merely the weapon card. Their value can be explored later as bounded specialization.

Repair quotes should use a documented running-cost basis tied to the item's effective progression floor. Pawn value must have a separately defined recoverable basis; cumulative displayed spend is informational, not automatically a sell price. Otherwise an upgrade/repair/reforge loop can mint currency.

## Protect cooperation without flattening mastery

There are two current boss paths. Ordinary non-milestone floors use persistent world HP. Floors 10, 20, …, 100 use a pledge quorum and aggregate-power resolution. A floor-100 shared-pool number calculated by `world_warden_hp(100)` is not the actual finale encounter. **The desired model is one continuously healing warden fought directly by players, including floor 100. Pledges, aggregate-stat auto-resolution, and timezone accommodation are not part of the desired design.** The [boss-system analysis](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/research/weapon-upgrades/BOSS-SYSTEMS.md) documents the existing mismatch and the transition required. [S9–S11]

For ordinary wardens, `required_strikers` is 1 through floor 30, then rises exponentially toward a population-dependent target. At the fallback census of 200, that target is 50 at floor 100. Pools are sized in reference fight units, with 2.7778% of maximum HP regenerated per hour above floor 30. Early ordinary floors 1–9 never heal or time out; ordinary floors 11–29 have a 30-hour silence reset and zero continuous regen. Every tenth floor takes the separate milestone route.

There is a pre-existing calibration concern: the sizing formula budgets one complete exchange for three energy, while the current player flow makes entry free and charges three energy **per damaging swing**. Some existing exchange tests refill energy every round. Maintaining their algebra therefore does not demonstrate that the live roster can beat a deep warden. A release must measure real energy-limited damage, recovery, and report timing before presenting “50 strikers” as a measured need. This proposal records the issue without retuning it.

For the weapon change, retain server-authoritative damage, energy costs, and the existing limits until the combat redesign explicitly replaces them. Do not resize wardens from whoever happens to equip the best current weapon: that would erase the benefit of good decisions. Freeze the reference basis and keep already-active pools and earned damage stable. The current pledge quorum is recorded as legacy behavior, not retained as a desired long-term rule. Its eventual removal needs a boss-specific implementation phase with current pledge refunds and safe world-state conversion; it must not happen as an incidental catalog migration.

The intended fight checks damage over real time: `net damage per second = sum(active player DPS) − warden healing per second`. A group must also have enough energy and survivability to finish the remaining HP before their burst ends. Crossing a minimum pledge count or waiting days for pooled player stats is not combat. Healing should close abandoned wounds naturally; no separate timezone window is needed for that purpose. Higher floors should demand more concurrent output, while good preparation can reduce the number of players or the time required. The boss document distinguishes this requirement from the source baseline, which does not yet implement it for every floor.

Allow better preparation to improve speed and efficiency. Require measured upper bounds that prevent one account's permitted loadout from clearing late cooperative gates alone. Test native-floor equipment and the strongest legally available legacy equipment, all paths, styles, races, mastery, consumables, and sleep schedules. Do not assume a 15% weapon bonus means only 15% more useful damage after defense subtraction.

Keep the existing 1–10 gear-band quantity for energy and other dependent systems, derived from effective progression floor. Replacing a ten-tier field with rarity values 1–4 would accidentally lower late energy caps and change other prices. Grade, upgrade level, and progression band need separate fields.

## Card and Forge experience

| Grade | Suggested frame color | Pixel geometry | Material icon language |
|---|---|---|---|
| Common | Slate `#A5ADB8` | Single stepped outline; square corner rivets | Rough log ends and unrefined metal pieces |
| Rare | Blue `#4E9CFF` | Double outline; two-pixel corner brackets | Clean billets and dense-grained hardwood |
| Epic | Violet `#B77AFF` | Three-step corners; small diamond notches | Faceted meteorite and patterned Starforged Steel |
| Legendary | Gold `#F3BE4A` | Crown-like corner teeth and interrupted inner rule | Angular shard matter and woven luminous threads |

Colors are a Linear Ascent proposal, not copied Kingdom Rush values. Use the same grade color and corner motif on weapons and both associated materials. Retain the game's crisp 1-bit item art, using frame color as an additional layer. Grade words and distinct shapes must remain readable without color. Keep grade color separate from faction colors, danger states, and the durability bar.

The resting weapon card shows name, path, grade, `+u / 20`, attack, current/max durability, and an upgrade-ready marker. Hover, keyboard focus, or tap reveals the same details: the next level, before/after stats, both material names with `owned / required`, exact gold `owned / required`, floor/character gates, and the reason an action is unavailable.

Use **“Upgrade in the Forge”** on a ready card outside the Forge. Clicking it opens the normal travel/navigation flow and selects that item on the Forge bench. It does not mutate the item remotely or teleport out of an encounter. A player may inspect requirements in combat, but upgrading waits until combat is finished and the Forge is reached.

At the Forge, the action names the actual spend, for example “Upgrade to +7 · 640 gold.” The final quote shows both materials, their quantities, current and resulting attack/durability, and any repair requirement. Upgrading rechecks location, ownership, gates, recipe version, gold, and materials on the server. Two open cards or a retried request cannot spend twice.

Material cards live in a dedicated **Materials compartment within the pack**, showing all eight types as they are discovered. Proposed storage: unlimited quantities per material, independent of the six consumable/equipment stacks. This preserves limited equipment capacity while avoiding a mandatory bag purchase merely to receive the new resources. Material progress shown on weapon cards is shared inventory availability, not a separate balance reserved for every weapon. Upgrading one card immediately refreshes all other cards drawing on that material.

Compact numbers may appear on closed cards; expanded quotes and accessible labels must show exact integer amounts. World HP can exceed JavaScript's safe-integer range. Backend integer arithmetic and a deliberate wire representation are essential; never round authoritative amounts through floating-point display values.

## Persistence, migration, and economy edge cases

**Use item instances.** A proposed item record includes `instance_id`, `template_id`, `grade`, `upgrade_level`, `durability_current`, `recipe_version`, optional temper/skin, and migration provenance. Equipment and pack references point to instance IDs. Materials remain stack counts in a separate material map. Do not add upgrade fields to a catalog object shared by every player.

**Do not change an existing player's paid stats by surprise.** Inventory, held slots, equipped weapons, faction storage, gifts, pending rewards, and pawn stock need a conversion inventory. Hone, wear, oil, styles, and legacy IDs all need representation. Several old slugs may map to one new template; never merge them into one item or overwrite the best copy accidentally.

**Grandfather difficult cases.** When an old item's effective bonus or style has no fair legal new-state mapping, retain a functional retired instance until an explicit Forge conversion can preserve its value. Do not silently round down its power or promote it past a closed gate. Avoid paying uncapped compensation gold based on the new cumulative table. Preserve remaining wear proportion or absolute wear under one documented migration rule and test it separately from the normal upgrade rule.

**Separate death policy from migration.** Recommended new-weapon policy: death damages the weapon and increases the repair obligation but does not erase purchased upgrade levels. Start with a missing-condition penalty comparable to the old economic loss and simulate it; this is a proposed change to the current 20% deletion rule, not existing behavior. Legacy items can retain their current policy until conversion. Existing death protections and beginner rules must keep explicit precedence.

**Protect earned materials from accidental whole-stack deletion.** Recommended ordinary-death policy for the new Materials compartment: banked/stored materials are safe, while any proposed carried-material loss must be percentage-based and priced in the same economy study. For the first release, keep the compartment safe on ordinary death and account for the reduced loss sink; do not accidentally inherit the generic “lose one entire inventory stack” operation. The future mining expedition has its own unbanked haul and loss-on-death rule.

**Do not introduce unrestricted material trading by accident.** Default new materials and weapons to owner-bound for the first release; existing gold transfers remain as they are. Strategic co-play comes from efficient assistance and coordinated goals. Guild material sharing is a valuable later option, but requires explicit transfer ownership, fees/limits, and economic evaluation. Existing item-transfer paths must reject unknown instance/material payloads until they implement the new schema. This avoids silently making the old slug-based transfers corrupt new items.

**Remove weapon XP honing cost once.** The new weapon upgrade bill is gold plus materials. Shield/armor honing and other aether sinks remain. Removing weapon honing also removes an XP sink, potentially accelerating character leveling. Quantify this alongside gold/material pacing rather than assuming gold-equivalent effort preserves the first 30 levels.

**Persist progress honestly.** A personal equipment progression record must be separate from world `unlocked_floor`, which worldd synchronizes forward for everyone. Proposed gates require character level `min(S,30)` and access to floor `S`; a personal floor-visit requirement, if used, must not make a lucky material discovery unusable without explanation. Materials can be owned before their recipes open.

## Kingdom Rush Battles comparison

The relevant comparison is **Kingdom Rush: Battles**, rather than only the original Kingdom Rush tower-upgrade trees. Its official beginner guide describes four card rarities and a loop of earning cards and gold to upgrade persistent collection entries. This supports a smaller recognizable weapon collection with visible upgrade progress. Materials take the role of upgrade copies here. It does not establish an MMO drop curve or a forge/mining system. [E1]

Ironhide's developers specifically highlighted affordability glows and upgrade-ready indicators, and explained rarity partly through mechanical complexity and lore. Those are useful references for the Forge link and distinct item identities. Their portrait-layout constraints also support readable, compact card treatment. [E2]

The requested community wiki describes rarity frames, persistent card levels, and a separate within-match tower progression. Its reported card cap of 12 conflicts with official October 2025 patch notes raising the cap to 15. Therefore its exact progression numbers should not be copied as current fact. This research uses the wiki as a comparative reference and official sources for the supported design mechanisms. [E3, E4]

| Battles mechanism | Useful adaptation | What needs a different answer here |
|---|---|---|
| Persistent cards and four rarities | Lasting weapon identity, grade frame, visible level | Twenty upgrades must fit the tower's existing power law. |
| Cards/resources plus gold | Show each required input and its progress | Materials come from chosen hunts; no duplicate-weapon lottery. |
| Upgrade-ready glow | “Upgrade in the Forge” marker and clear quote | Readiness also requires both materials and valid progression gates. |
| Distinct deck roles and counters | Blade/bow/staff choice and useful secondary weapons | Do not equalize every matchup or erase the current triangle. |
| Summon pity | Optional protection against a native-grade dry streak | Keep rare discoveries rare; no limited-time monetized gate. |
| Competitive card balance changes | Measure whole builds and interactions | Shared-world wardens and other players' contributions must survive a catalog migration. |

The official Summon Rift guide documents a visible guaranteed-reward mechanism after enough summons. That supports the idea of reducing extreme dry streaks, not copying its paid summons, event schedules, or banner resets. Official patch notes also reduced Legendary power and fixed duplicated buffs; they illustrate why multiplying every new stat source deserves a separate check. [E4, E5]

## Implementation sequence to turn this research into a plan

The following phases are a blueprint, **not executed phases**. Before runtime work, create and commit the actual numbered plan and phase files under the appropriate plugin/worldd plan directories, including exact rollback operations and matching dojo scenarios.

| Phase | Deliverable and inheritance | Verification required before proceeding |
|---|---|---|
| 1. Baseline and design decisions | Freeze reference data; record current economy, optimal routes, warden energy reality, legacy milestone behavior, and inventory shapes. Carry the direct-combat boss requirement into its own implementation phase; decide initial death/temper policy. | Targeted existing tests, whole-floor calculations, representative existing-player browser play; failures filed separately. |
| 2. Data and compatibility | Instance-aware weapon state, eight material definitions, versioned recipes, compatibility readers. Existing players and new-player provisioning inherit the same engine behavior. | Migration fixtures including duplicate slugs, held/packed/stored items, oil, worn and broken weapons; idempotent reruns and rollback. |
| 3. Earn and upgrade | Creature affinities, hunting trails, loot receipts, Forge-only atomic upgrade, death behavior. | Whole-route economy simulation, adversarial retries, wrong-location refusals, insufficient inputs, no mining dependency, honest previews. |
| 4. Present and simplify | Grade frames, material compartment, hover/focus/tap preview, selected-item Forge navigation, retire excess sale rungs. | Real browser and Luna play on desktop and narrow mobile widths, all three paths, good and poor routes, no lost materials at full pack. |
| 5. World compatibility and rollout | Vendor engine into worldd, update mechanics data and projections, canary existing and fresh accounts, then explicit deployment. | Targeted then full suites; whole-tower engine tests; multi-user dojo; production verification during a separately authorized deployment. |

Keep a feature flag and old readers through migration. Snapshot before account/fleet operations. Rollback must restore each migrated instance and material balance from recorded pre-change state; it cannot simply delete new fields after players have spent resources. Define how post-migration transactions are reversed or replayed before enabling writes. Never roll back a world frontier or erase another party's boss damage as part of an item migration.

The release gate is evidence that the new choices are legible and useful: a player deliberately picks a better material route, earns the expected advantage, sees accurate progress, travels to the Forge, spends the quoted inputs once, and still needs other players where the world is designed to require them. A dojo walkthrough is mandatory before reporting implementation complete.

## Sources

Local source citations refer to the checkout identified above, not a claim about the currently deployed server. Line positions may move with parallel working-tree changes.

- **S1.** Linear Ascent, [economy.py](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/economy.py): pillar, income, character cap, reference gear, catalog, honing, durability, grade-independent training, death constants, pack, deep hunts.
- **S2.** Linear Ascent, [mechanics generator](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/tools/gen_mechanics.py:245): floor tables, reference bars, and nominal warden stat output.
- **S3.** Linear Ascent, [generated mechanics data](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/static/site/mechanics-data.js): 101 reference bars including the extra calibration bar; this study checks playable floors 1–100.
- **S4.** Linear Ascent, [game import selection](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/gamepath.py) and [vendor script](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/tools/vendor_game.sh): source/vendored engine relationship.
- **S5.** Linear Ascent, [player state](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/state.py:38): new-player data, migrations, hone keys, gear bonus, energy band.
- **S6.** Linear Ascent, [combat](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/combat.py): hunt weighting, drops, death, shared damage, per-swing energy.
- **S7.** Linear Ascent, [Forge and inventory](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/core.py:1794): current shop, hone, repair, inventory, and boss routing.
- **S8.** Linear Ascent, [item rendering](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/render.py:1727): item preview and existing pixel presentation.
- **S9.** Linear Ascent, [world social engine](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/social.py:447): shared HP, regeneration, census, pledge and aggregate resolution.
- **S10.** Linear Ascent, [world game transactions](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/game.py): row locks, idempotency, frontier synchronization.
- **S11.** Linear Ascent, [gate tests](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tests/test_026_the_gate_bites_back.py) and [coordination tests](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tests/test_022_002_retune.py): exchange assumptions and test coverage boundaries.
- **E1.** Ironhide Game Studio, [Kingdom Rush Battles Beginner's Guide](https://support.ironhidegames.com/support/solutions/articles/4000223620-kingdom-rush-battles-beginners-guide), modified 3 November 2025; accessed 11 September 2026.
- **E2.** Patricia Mazzei / Ironhide Game Studio, [Q&A with Kingdom Rush Battles Devs](https://www.ironhidegames.com/News/Details/420), 13 August 2025; accessed 11 September 2026.
- **E3.** Kingdom Rush Wiki contributors, [Kingdom Rush: Battles](https://kingdomrushtd.fandom.com/wiki/Kingdom_Rush:_Battles), community-maintained, accessed 11 September 2026. Exact level-cap claim conflicts with E4.
- **E4.** Ironhide Game Studio, [Battles October Patch Notes](https://www.ironhidegames.com/News/Details/432), October 2025 patch entries; accessed 11 September 2026. Historical change log, not proof of today's maximum level.
- **E5.** Ironhide Game Studio, [Summon Rift Event Guide](https://support.ironhidegames.com/support/solutions/articles/4000223685-summon-rift-event-guide-kingdom-rush-battles-summon-scrolls), modified 3 November 2025; accessed 11 September 2026.
