# Player experience — from opening to the next hunt

Companion to [plan 015](PLAN.md). Everything below describes the proposed experience for review, not an implemented screen.

## The opening teaches a useful loop

Keep character creation, the tower's story and existing identity choices. Replace instructions that teach buying extra weapon slots or repeatedly banking each individual kill. Do not introduce a new class restriction to force blade/bow/staff use.

1. Arrive with three available weapon slots and an authored starter weapon. The profile points to **Weapon collection** and **Bring to battle — 3 slots**. Empty slots are understandable, not locked School purchases.
2. Show a two-creature Ground Common opening group. One sentence explains: **“XP after each kill. Bring home the gold and items by defeating both.”** Teach an attack before presenting the full effect catalog.
3. The first kill awards XP in place, crosses out its portrait and exposes the next enemy. HP and weapon condition remain changed. The next normal combat action engages it; no mandatory Continue or loot screen.
4. Full victory secures the haul. Its receipt links to the next useful action: fill a weapon slot, visit the Forge, recover, or hunt again.
5. Provide basic bow and staff access through authored opening rewards/quests before a required Air or Power counter appears. No rare drop and no expensive equal upgrade of all three weapons is necessary. These grants and their costs belong in the real engine and simulation.
6. Teach selecting an appropriate weapon against a visible profile, then a first +1 upgrade and one positional/status decision. Offer the full help/wiki on demand; avoid a lecture before the first attack.

The first-session gate is ordinary play through this loop with normal earned resources, in both web and Luna. A fixture with free gold or healing cannot establish that it works.

## Collection and profile

**Weapon collection** is the owned inventory view. **Bring to battle** is its three-slot selection. The design may call that selection a deck, but there is no random draw, hand, shuffle or requirement to own every family.

| Screen element | Information and behavior |
|---|---|
| Three large battle cells | Selected instance's image, name, role, grade, +level, condition, technique and arrows. Click/tap a cell to replace it from the collection. Always three cells from account creation. |
| Collection cards | Actual grade-specific drawing and shaped frame; path/reach/damage channel; special ability; current/max endurance; source and level; available or stored status. Two copies of the same family remain distinguishable. |
| Compare / replace | Compare the selected slot with one candidate: damage against the inspected monster, reach, ability, endurance, ammo cost. Show gains and losses; avoid a universal power score that hides a lost counter. |
| Coverage strip | “Ground: blade/bow/magic; Air: bow/magic; no poison answer,” with concrete counter limitations. It is advice, not a mandatory balanced-deck recipe. |
| Arrow choice | Show the six payloads as visible controls, remaining quantities and effective channel. Arrow selection changes the shot, not the bow's permanent type. |
| Stored and pending items | Show location and the action needed to retrieve them. Ownership does not waive travel/storage/access rules. Pending group drops cannot enter the deck. Faction items require the actual withdrawal/ownership transaction. |
| Forge readiness | Owned/needed gold and both materials on hover, focus or tap; next-level effect; **Upgrade in the Forge** navigates there. A +20 item says **Max level**. |
| Profile | Avatar, health, energy, character progress, three selected weapons, defense gear and current condition. Show the active weapon on the avatar; choosing three does not mean wielding three simultaneously. |
| Another player's profile | Preserve existing visibility boundaries and show selected weapons read-only. Strip editing actions; never expose bank/private state by reusing the owner's collection payload. |

Collection browsing is a view over existing ownership/storage, not unlimited free pack space. Keep armor, shield, shoes, charm and consumables separate from the three weapon slots. A bow does not lose a battle slot merely because arrows take consumable storage. Duplicate families are allowed if the player owns separate instances; one item ID cannot occupy two cells.

Deck presets can follow after the core flow works; they are convenience references, never copies of weapons or a way to replace a locked deck. A broken selected weapon stays in its cell and explains why it cannot attack; it does not summon an owned replacement automatically. Out of combat, the collection offers repair or an available replacement. With no usable weapon, direct the player to the recovery route before starting another hunt.

## Encounter opening

The preview belongs in the actual battle scene and shares its layout. Show the offer's floor, trail and normal/deep mode, the **real ordered portraits**, profile icons, standout traits and arrival distances. Keep all 425 creatures available to floor-appropriate composition; do not rotate the same eight images across the tower.

A five-enemy opening with two energy should say:

> **5 enemies · 2 energy available**
>
> 1 energy is spent when each enemy's fight begins. The first 2 fights are at normal strength; the next 3 will be exhausted unless energy recovers.
>
> XP after each kill. Gold, materials and equipment after all 5 are defeated.

The three chosen weapons sit directly underneath. A three-blade loadout facing a flyer gets a readable **“None of these weapons can reach this enemy”** warning and a nearby collection button. Do not silently choose easier monsters after seeing the deck; a knowingly risky specialist selection is permitted. Show required gates and any unavailable weapon before entry.

Opening or reloading the preview is free and preserves the same offer. Selecting another already-defined route is allowed; it must not refresh each route's unstarted offer into a new lottery roll. Starting the first valid combat action consumes the offer, commits the three instance IDs and charges that enemy's energy in the same transaction. The player may leave an unstarted preview without a charge.

## One battle scene

Suggested arrangement, adapted to the existing renderer rather than a second UI:

```text
Marsh trail · enemy 2 of 4                   Energy 0 · this fight was paid
[defeated] [CURRENT] [next: flying] [next: Power]

Current creature art · Ground / Magic · speed · HP
Intent: charging on its next action       Gap: Near
Poison: 2 phases · Stun resistance: ready

Your HP · armor · shield condition · earned XP · pending haul
[Weapon 1 + ability] [Weapon 2 + ability] [Weapon 3 + ability]
[Approach] [Pull back] [Guard] [Escape] [Consumables]
Recent result: Shield absorbed 4. You lost 3 HP.
```

These are information priorities, not approved pixel dimensions. On narrow screens the weapon buttons wrap without hiding the active enemy, exhaustion state or Escape. Render through the common `Scene` / `render.py` / `pane.py` path so the website and Luna cards agree. Numbered text choices select the same explicit weapon/action IDs as buttons.

- **Weapon actions:** choose any of the three committed instances as the action. No separate switching toll and no free second hit. The correct instance supplies damage, technique, wear and cooldown even when all three are swords.
- **Space and speed:** show Contact, Near, Far or Cover, enemy pursuit and the consequence of push/pull-back. A push can enable the next bow shot or improve escape; that next choice still costs its normal action.
- **Intent and effects:** preview charge/stun opportunities; show poison/burn/bleed ticks, slow, Expose and immunity. A resisted effect says why. Changing weapons does not refresh cooldowns.
- **Energy:** distinguish “this enemy's energy was paid” from “exhausted for this fight.” The bar reaching zero after its last paid point does not weaken that enemy's fight retroactively. Show the next member's projected energy separately.
- **Information:** portraits and weapon details remain free reads, usable by keyboard and tap. Disabled attacks explain reach, broken equipment, ammo, cooldown or gate failures before any cost is taken.
- **Pending haul:** a compact counter, not an inventory the player can spend. Opening details does not interrupt combat or resolve a reward.

After a kill, animate a brief defeat and focus the next portrait in the same response. Award that kill's XP immediately. The next enemy is **waiting**: no pursuit, attack, energy cost or cooldown tick occurs merely because its image appears. The player can attack, approach, guard or use an allowed combat consumable to begin it, or **Leave and lose the pending haul**. This boundary avoids a compulsory extra click while preserving the user's energy rule.

HP, ammo, shield/weapon condition, player statuses, cooldowns and group-level rescue limits persist. Each next enemy has an authored arrival distance, shown before it engages. Do not grant every bow a free Cover opener, and do not make every arrival Contact. A new enemy cannot strike before the player's first accepted action against it.

### Resisted-hit feedback

When a landed hit is weakened by resistance, show **why at the moment of impact**. A small, crisp pixel icon appears above the defender, floats upward and fades alongside the actual reduced damage number. On a monster it rises from that monster's portrait/body; on a player it rises from the player. It is hit feedback, in addition to the persistent type badge.

| What actually reduced the hit | Feedback |
|---|---|
| Power resistance, such as an ordinary bow shot against a resistant monster | The game's Power shield icon rises in its established color, with the short label **Power resisted**. |
| Magic resistance, such as a spell or arcane arrow against a resistant monster | A distinct pixel **magic shield**, using the game's Magic symbol/color and shield motif, rises with **Magic resisted**. |

Show the damage that actually reached HP; the icon explains the small number without suggesting a complete block. Choose the icon from the resolved damage channel and resistance cause, not the weapon's appearance, rarity or the monster's badge alone. Arcane arrows use Magic feedback; the physical impact and Magic burn of a fire arrow can have different results. The Air Power spell-dispersal exception shows Magic resistance feedback when it reduces magic damage.

Do not show a resistance icon merely because an attack was weak: misses, lack of reach, exhaustion, worn equipment, ordinary armor absorption and immunity have their own explanations. The same feedback can describe an existing player resistance without adding new player/PvP resistance rules.

Keep the animation brief and nonblocking, synchronized with that hit and anchored to its defender even if the next group member appears. Preserve pixel edges rather than blur/glow. The combat log/text response also says **Power resisted — 3 damage** or **Magic resisted — 2 damage**, using real values. A reduced-motion setting shows the same icon/label without floating; meaning must remain clear on mobile and without animation or color. Re-rendering or retrying the same hit must not replay the popup as a new hit.

## Results, failure and reconnect

| Event | Player-facing result |
|---|---|
| Kill before the final member | “2 of 4 defeated. +12 XP earned. Haul pending.” Same battle scene; next enemy waiting. |
| Final victory while alive | “Group defeated. 46 XP earned; 120 gold, Wood ×3 and [item] secured.” Show actual totals; no second roll. Hunt again / Forge / recover are direct next actions. |
| Leave between enemies | “You kept 24 XP. You left behind 65 gold and Raw Metal ×2. Energy spent: 2 of the possible 5.” No escape roll against an unstarted enemy. |
| Escape during an active enemy | Uses distance/speed and a real action. Failure continues the battle; success forfeits pending haul and retains earned XP. |
| Death | Separate XP kept, pending haul lost, and penalties to possessions brought in. Never subtract unclaimed gold from the existing purse as well. Show repair/recovery access. |
| Revive in place | Same group, committed weapons, energy receipt and pending haul. Killing a member does not reset the group's life-save allowance. |
| Refresh / reconnect | Restore the same enemy, HP, deck, exhaustion, pending haul and already-earned XP. No reroll, extra charge, free heal or duplicate result. |
| Full pack at victory | Ownership is secured into a persistent claim area; resolve it before another hunt. Materials have their own compartment. No deletion or unlimited reward-storage workaround. |

## The rest of the game inherits this change

| Area | Required follow-through |
|---|---|
| Town / map / trails | Group size, known profile mix, danger and material carriers; direct return to the collection; deep route's improved odds and one-per-enemy cost. |
| School / Guildhall | Keep the School and its non-slot functions, including weapon mastery and training. Remove only extra battle-slot lessons, fees and unlock messages; preserve learned progress and unrelated pack progression. Explain XP reserve and normal advancement outside battle. |
| Shop / Forge / pawn / storage / gifts | Instance-aware cards and transactions, actual source +level/condition, deck locks and location rules; prevent selling or upgrading a committed weapon mid-group. |
| Tips, intro, help and Luna tools | Teach the same three slots, reward boundary and exhaustion rule. Agent suggestions must use actual available actions and never narrate a fourth equipped weapon. |
| Contracts / weekly / rescue / assist | Per-kill statistics and XP can progress; gold/item-paying objectives from that group become claimable only on a full clear. Extraction abandons the pending haul. |
| Warden opening and battle | One shared health bar, healing per second, actual attacks/contributors and your finite resources. No pledge button. Floor 100 announces victory/era closure only after real shared death. |
| Wiki | Collection/family/grade details; individual and group drop odds; route composition; monster images/parameters; effect timing; source settings; matching implemented/proposed labels. |
| Simulation website | Plain titles: “Days until players can defeat each floor's groups,” “Extra days needed for the next floor,” and “Players needed to defeat this warden.” Tooltips name the floor, days, population and player/strategy. |

Use the game's IBM VGA font at its established 16px size throughout these surfaces. Establish hierarchy with space, frames and color rather than varied font sizes. Reuse real shield/magic/air/material icons; distinguish shape as well as color. Common/Rare/Epic/Legendary selectors are visible framed choices; paths, affinities and six arrows are visible buttons. Lists with more than six options may stay dropdowns. All grade illustrations differ beyond tint, and all essential details work without hover.

## Review checkpoints

Phase 1 freezes this flow and the matching text/action contract. Phase 3 shows a working first-ten-floor loop in web and Luna before expansion. Phase 7 verifies the complete experience on desktop and a 390px phone, with player A reconnecting after player B has acted elsewhere. Screens that render correctly but leave a player unable to understand the next action fail the walkthrough.
