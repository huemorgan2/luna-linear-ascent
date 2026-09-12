# Combat expansion — read this first

**Latest research: [Three-weapon decks and monster groups](DECKS-AND-MONSTER-GROUPS.md).** Three battle slots are available from the start; School slot purchases are removed. Weapons have deliberately unequal matchups. The recommended hunt is one continuous sequence of at least two enemies, with XP earned per kill and gold/materials/items secured after the complete group. It covers deck choices, floor progression, energy, overflow XP, loot, migration and validation. These are design changes, not live gameplay.

The earlier [plan015: weapons, combat and player progression](../../plans/015-weapon-combat-progression/PLAN.md) has eight phases and nine browser scenarios. Its phases and acceptance gates now need rebasing around groups and three-weapon ownership before execution. Runtime implementation has not started. The research above takes precedence over the earlier single-enemy implementation order below.

The current visual reference is the [game wiki](https://linearascent.net/wiki), published12 September2026. It contains425 authored creatures, full rarity drop tables, deep-hunt modifiers and64 weapon source settings. See [Wiki loot and sources](WIKI-LOOT-AND-SOURCES.md) for this follow-up; it supersedes the eight-creature prototype.

**Proposal:** 16 weapon families in Common, Rare, Epic and Legendary: **64 variants**, each upgradeable from +0 to +20. Pick a weapon because of what it does, then invest in it. This replaces the earlier suggestion of only one blade, bow and staff per grade.

The [detailed plan](PLAN.md) contains exact coefficients, material recipes, effect timing, migration work and implementation phases. The [interactive atlas](https://linear-ascent-combat-atlas.vaselin957545.chatgpt.site) lets you explore the proposal. No live game mechanics have changed.

## Monsters have two independent badges

Movement tells you whether your weapon can reach the enemy. Defensive affinity tells you what hurts it. Species then add traits such as poison immunity, a charge or vulnerability to fire.

| Enemy | Main counter | What makes it dangerous |
|---|---|---|
| Ground Common | Any weapon | Simple early fights |
| Ground Power | Magic or arcane arrows | Resists physical hits |
| Ground Magic | Blade or ordinary arrows | Resists spells |
| Air Common | Bow; spells also work | Fast pursuit, blades cannot reach |
| Air Power | Ordinary arrows | Fastest pursuit, disperses spells |
| Air Magic | Ordinary arrows | Very strong magic resistance |

Air Power is an **explicit draft exception** based on your description that magic is particularly weak against it. It does not follow the ground Power rule. Give that exception a visible “spell dispersal” trait so the player understands it.

## More weapon identities

| Path | Families and roles |
|---|---|
| Blades | **Breach Cleaver:** strongest plain hit. **Viper Edge:** poison. **Ramguard Sword:** push away. **Thunder Maul:** stun. **Briar Saber:** bleed. **Sundering Falchion:** weaken defense. |
| Bows | **Hawkeye:** cover shots. **Skirmisher:** better at contact. **Recoil:** push. **Pinning:** slow. **Runestring:** stronger arcane arrows. |
| Staves | **Ember:** burn. **Frostbind:** slow. **Stormbell:** stun. **Repulsor:** push. **Hexglass:** weaken defense. |

Every family exists in all four grades and has its identity at +0. Upgrades improve attack and endurance; they do not make stuns last longer. Different recipes, prices and weaknesses create real tradeoffs.

All bows accept ordinary, arcane, poison, fire, pinning and concussive arrows. Arcane arrows change the hit to Magic. Fire arrows have a physical impact followed by a Magic burn. A player can bring different payloads for different targets.

## Fights become a sequence of decisions

Distance has four steps: Contact, Near, Far and Cover. Flying enemies pursue faster. Speed changes retreat and escape odds.

A successful Ramguard push opens two steps and delays pursuit for that phase. On the next action the player can switch to a carried bow and shoot, or try escaping. Both still cost an action; pushing does not grant free attacks.

Poison lasts three enemy phases; burn and bleed last two. Stun skips one enemy action. Slow reduces speed. Expose weakens flat defense without removing affinity. Techniques trigger on successful hits and have action cooldowns, so timing matters more than random proc luck. Immunities and remaining durations must be visible.

Shields absorb part of a landed hit, with **at least 25% reaching HP**. Shield wall increases absorption instead of blocking everything. If the shield absorbs 55 damage, it loses 55 endurance units. Armor, dodges and spell barriers must not be charged to the shield.

## Keep progression and teamwork meaningful

| Grade | Reference floors | Materials |
|---|---|---|
| Common | 1–25 | Wood + Raw Metal |
| Rare | 26–50 | Hardwood + Steel |
| Epic | 51–75 | Meteorite + Starforged Steel, working name |
| Legendary | 76–100 | Mythic Threads + Shard Matter |

Keep the previous research’s neutral upgrade curve, exponential prices and creature drops. Materials use matching pixel rarity frames and a dedicated pack compartment. Cards show gathered/required amounts and link to **Upgrade in the Forge**. Only the Forge performs the upgrade. Mining stays in its separate plan.

For wardens, including Floor 100, use one shared health bar that continuously heals. Players win by attacking at the same time fast enough to overcome healing, while having enough energy to finish. Remove stored pledges and combined-power victory. Better counters and coordination should let fewer players succeed; do not increase boss stats automatically to cancel their advantage.

The atlas preserves the neutral attack reference across all 100 floors. **That is not full balance validation:** statuses, family premiums, ammunition and shield changes still need simulation. Before launch, test neutral, smart and wrong-counter builds across the floors, then real multi-player fights. Keep clever shortcuts; fix universal best weapons, permanent stun and infinite kiting.

## Implementation order

1. Separate monster traits and add safe item-instance migration.
2. Implement damage, shields, movement and effects with readable combat events.
3. Add weapon families, Forge recipes, materials, arrows and all card changes.
4. Replace milestone pledges with actual shared warden combat.
5. Simulate progression, play-test through Luna with multiple players, then canary release.

Kingdom Rush/Battles informs the readable enemy entries, counters and distinct abilities. The detailed plan links the inspected sources and explains where Ascent deliberately differs.
