# Combat and weapon identity — short research plan

11 September 2026 · **Proposed design, not implemented game behavior.** Companion: the interactive Combat Atlas in `site/`. This extends the [weapon/material research](../weapon-upgrades/RESEARCH.md) and supersedes its three-family, twelve-template catalog. The exact [84 upgrade states and 100-floor money/material tables](../weapon-upgrades/PROGRESSION-TABLES.md) remain the neutral baseline. Mining stays in [its separate plan](../../plans/013-mining-and-gathering/PLAN.md).

## Decision

Build **16 weapon families across four grades: 64 variants**, each +0–20. Give weapons identities through damage channel, reach, endurance, movement and timed effects. Let prepared players win faster, spend less energy and need fewer raid members. Do not equalize route rewards, success rates or every weapon’s effective DPS.

All coefficients below are tuning candidates. Arithmetic preservation of the old attack curve is not proof that the new combat system preserves difficulty.

## What exists and why it needs changing

| Area | Current source behavior | Proposed change |
|---|---|---|
| Catalog | 145 weapon records: 141 paid, four zero-price basics/compatibility records | 16 tactical families × four grades; retain migration aliases and starter access |
| Enemy type | One of plain, fly, armoured, magic_resist | Independent Ground/Air and Common/Power/Magic, plus species traits |
| Counters | Blade cannot hit flyers; some matchups reduce damage to 1.5% | Visible, less absolute resistances; still no blade reach against Air |
| Effects | Poison and slow arrows exist; fire arrows multiply the immediate hit | Consistent poison/burn/bleed/control effects with readable timing |
| Defense | Ordinary hit starts with a 25% chip rule; **Shield wall explicitly blocks all damage** | One absorption pipeline; wall improves shield defense without immunity |
| Distance | Approach/retreat and an initial treeline shot already exist | Persistent 0–3 gap and a new opening after a successful push |
| Progression | Floor-based catalog and weapon honing; ten energy gear bands | +0–20 replaces weapon honing; preserve ten energy bands and character cap 30 |
| Wardens | Ordinary shared HP differs from milestone war-party pledges | Every warden, including 100, uses shared HP, continuous healing and accepted actual attacks |

Source evidence: `plugin-linear-ascent/plugin_linear_ascent/economy.py` (`FORGE`, `TYPE_MULT`, `creature_stats`, reference loadout, regen); `engine/combat.py` (`_monster_hit`, `_arrow_effect`, `shield_wall` around line 2581); `engine/state.py` (slug-based gear/hone and durability); `worldd/app/social.py` (`_fx_boss_commit`). Current ordinary creature stats already depend on creature bar, body and bite, not only floor. Preserve those authored differences; the atlas’s neutral species previews are illustrative.

## Monster taxonomy

POWER describes defensive affinity, not automatically its outgoing attack channel. Store the latter separately. Enemy power can be Physical or Magic independent of the icon identifying its vulnerability. “Common enemy” and “Common weapon grade” are separate concepts in UI and data.

| Profile | Icon/color | Speed default | Blade/Power damage | Bow/Power damage | Magic damage, including arcane arrows |
|---|---|---:|---:|---:|---:|
| Ground Common | Diamond / neutral | 5 | 1.25× | 1.25× | 1.25× |
| Ground Power | Shield / orange | 4 | 0.45× | 0.45× | 1.50× |
| Ground Magic | Spark / violet | 5 | 1.50× | 1.50× | 0.45× |
| Air Common | Common + wing/cyan | 9 | Cannot reach | 1.25× | 0.90× |
| Air Power | Power + wing/cyan | 10 | Cannot reach | 1.25× | 0.35× |
| Air Magic | Magic + wing/cyan | 9 | Cannot reach | 1.50× | 0.30× |

**Explicit assumption:** Air Power is the exception requested in the conversation: spell dispersal makes bows with ordinary arrows its best answer. This conflicts with a universal “Power is weak to Magic” rule, so the card must name the exception. If that interpretation changes, update this row and the shared site data together. Air is always fast, but not literally an unavoidable hit every action: stun, push and escape still create useful decisions.

Candidate species are examples using existing art, not claims about current live traits. Multiply neutral same-floor `creature_stats(floor, [])` HP/ATK by these factors for the atlas; production mapping must retain authored bar/body/bite before choosing replacement type weights. Do not multiply both old and new type weights.

| Species | Profile | HP / ATK factors | Speed | Extra trait and counter |
|---|---|---|---:|---|
| Hedge Rat | Ground Common | 0.70 / 0.65 | 4 | Living, low defenses |
| Ironhide Boar | Ground Power | 1.25 / 1.15 | 5 | Telegraph charge one action ahead; interrupt with push/stun |
| Barkplate Troll | Ground Power | 1.60 / 1.30 | 3 | Burn 1.5×; poison 0.5× |
| Glade Wight | Ground Magic | 1.00 / 1.00 | 5 | Bloodless, venomproof; direct physical damage |
| Lamp Moth | Air Common | 0.65 / 0.65 | 9 | Flammable; arrows or burn |
| Ironwing Vulture | Air Power | 1.15 / 1.15 | 10 | Spell dispersal; ordinary arrows |
| Stormwing Shade | Air Magic | 0.95 / 1.10 | 9 | Bloodless; physical arrows, close-handling bow |
| Forge Sentinel | Ground Power | 1.80 / 1.25 | 3 | Steadfast, venomproof; Magic and Expose |

Gradually teach rather than add a new damage multiplier every floor: floors 1–3 Common/reach; 4–9 one affinity or effect; 10–25 interrupt timing and shared wardens; 26–50 mixed traits and material routes; 51–75 complementary builds; 76–100 coordinated specialization. These are introduction bands, not a ban on early exceptional encounters or clever skips.

## Weapon families

ATK is a multiplier on the **weapon contribution**, not total character attack. END multiplies neutral max endurance; gold multiplies the neutral step charge. Material A/B names follow the grade table below; the ratio multiplies that step’s Q. Each row exists in all four grades. Techniques are available at +0. Cooldowns count subsequent committed combat actions: a 3-action cooldown used on action 1 becomes ready for action 5; a 4-action cooldown becomes ready for action 6. Free reads/equip previews do not tick them.

| Family | Path | ATK | END | Gold | A:B | Identity / recharge |
|---|---|---:|---:|---:|---|---|
| Breach Cleaver | Blade | 1.15 | 0.90 | 1.05 | 1:3 | Direct impact; no effect |
| Viper Edge | Blade | 0.80 | 1.00 | 1.10 | 1:3 | Poison / 3 |
| Ramguard Sword | Blade | 0.85 | 1.20 | 1.15 | 1:4 | Knockback / 3 |
| Thunder Maul | Blade | 0.75 | 0.85 | 1.20 | 1:4 | Stun / 4 |
| Briar Saber | Blade | 0.90 | 0.90 | 1.10 | 2:3 | Bleed / 3 |
| Sundering Falchion | Blade | 0.85 | 1.10 | 1.15 | 1:4 | Expose / 3 |
| Hawkeye Longbow | Bow | 1.10 | 1.00 | 1.05 | 3:1 | Readied cover shot, +20% direct impact at gap 2–3 / 3 |
| Skirmisher Bow | Bow | 0.90 | 1.10 | 1.00 | 3:1 | 90% contact impact; ordinary bows retain 65% |
| Recoil Recurve | Bow | 0.80 | 0.90 | 1.15 | 4:1 | Knockback / 3 |
| Pinning Bow | Bow | 0.85 | 1.00 | 1.10 | 4:1 | Slow / 3 |
| Runestring Bow | Bow | 0.90 | 0.85 | 1.20 | 3:2 | Arcane arrow impact ×1.25; ordinary ammo stays Power |
| Ember Staff | Staff | 0.85 | 1.00 | 1.10 | 2:2 | Burn / 3 |
| Frostbind Staff | Staff | 0.80 | 1.15 | 1.10 | 3:2 | Slow / 3 |
| Stormbell Staff | Staff | 0.75 | 0.90 | 1.20 | 2:3 | Stun / 4 |
| Repulsor Staff | Staff | 0.80 | 1.05 | 1.15 | 2:3 | Knockback / 3 |
| Hexglass Staff | Staff | 0.90 | 0.90 | 1.15 | 3:3 | Expose / 3 |

All bows accept all arrow payloads. Ordinary: Power ×1.00. Arcane: Magic ×1.00. Poison/fire: Power impact ×0.90 plus their effect. Pinning: Power ×0.85 plus Slow. Concussive: Power ×0.80 plus Knockback. Fire’s later burn is Magic. For ten arrows, candidate material recipe units are respectively 1/2/2/3/2/3; each unit costs 3A:1B of the bow’s grade. Ammo gold remains a separate pacing decision; this table specifies materials only. Higher-grade bows require same-grade payloads; do not let Common ammo obtain Legendary effect strength for Common cost. One accepted fired shot consumes one arrow, even on a miss; invalid/no-reach actions consume none.

## Effects and the fight

| Effect | Candidate strength | Duration / resistance |
|---|---|---|
| Poison | 8% source ATK, Power | Three enemy phases; venomproof immune |
| Burn | 12% source ATK, Magic | Two phases; fireproof immune, flammable ×1.5 |
| Bleed | 10% source ATK, Power | Two phases; bloodless immune |
| Knockback | +2 distance, capped at 3 | Steadfast immune; suppress this phase’s pursuit |
| Stun | Skip next enemy action and chase | One phase; then immune for two phases |
| Slow | −3 speed, minimum 1 | Two phases; strongest slow only |
| Expose | −20% flat enemy DEF | Next two direct hits; no affinity reduction |

A valid action resolves: reach/energy/ammo → direct hit → apply landed-hit effects → tick pre-existing DoTs → enemy action/pursuit unless prevented → phase expiry. New DoTs first tick on the **next** enemy phase. A stunned phase still advances existing DoTs. The source attack snapshot includes character, current weapon contribution and training before target resistance; no percent-max-HP damage. DoTs skip flat DEF, apply their channel multiplier once, then trait resistance; round once, minimum 1 if not immune. One stack of each DoT per source, refresh without immediate bonus ticks. Separate sources can contribute on a shared boss. One hard-control effect per hit, with the player choosing weapon technique or arrow control; no double stun/push payload.

Direct damage proposal: `A = body + round(B(f) × family_factor)` followed by current training and wear. Apply contact/arrow/technique factors; call the result X. Then `max(1, round(max(0.15X, X − DEF/2) × affinity))`, after reach succeeds. **Magic would now use this flat-defense step too**, unlike the current bypass; its advantage comes from affinity. This is a material balance change to simulate. The site isolates 100 reference weapon attack and DEF 40, excludes body/training/techniques, and is not a full fight simulator.

Distance is Contact 0, Near 1, Far 2, Cover 3. Ground pursues one step; Air two. Blades strike only ground at contact; a ground blade attack from farther away must spend the action approaching, not deal damage remotely. A shove guarantees one following **opportunity**, not a free attack: switch to a carried bow as part of the next paid action, or attempt escape. Reaching gap ≥2 rearms the positional cover opportunity; the technique cooldown still applies. Slow affects movement-success odds; it does not grant extra click attacks.

`pull_back = clamp(.20,.80,.50+.06×(player_speed−enemy_speed))`; success adds one gap, failure allows a counter. `escape = clamp(.10,.90,.35+.10×gap+.05×speed_difference)`; failure spends the action and allows a counter. A speed-5 player escaping a speed-9 flyer has 15% at contact, 35% at gap 2. Preserve this advantage instead of equalizing escape chances.

## Shields

For a landed incoming hit D after its attack-type modifier:

- Armor absorbed = `min(floor(armor_DEF/2), floor(.50D))`.
- Shield absorbed = `min(floor(effective_shield_DEF/2), max(0,floor(.75D)−armor_absorbed))`.
- HP loss = D − both absorbed shares, always at least `ceil(.25D)`.
- Shield wall multiplies shield DEF by 1.5; it no longer negates the hit.
- Shield endurance wear equals **only its absorbed share**. Store wear in absorbed-damage units; calibrate full capacity to `50 × base_shield_DEF/2`. Stronger defense blocks more and spends more per hit; capacity also grows. At zero endurance, shield DEF is zero until repair. This requires explicit conversion from current wear units.

Example: D100 / armor40 / shield80 → armor20, shield40, HP40, wear40. With shield160 → armor20, shield55, HP25, wear55. Avoid charging shield wear for a dodge, range reduction, armor, or a spell barrier. New persistent attributes and broken-shield behavior need migration; they are not a cosmetic bar change.

## Upgrades, materials and progression

| Grade | Reference floors | A / B materials | Pixel frame |
|---|---|---|---|
| Common | 1–25 | Wood / Raw Metal | Single gray-green outline |
| Rare | 26–50 | Hardwood / Steel | Double blue outline |
| Epic | 51–75 | Meteorite / Starforged Steel (working name) | Violet double frame, stepped corners |
| Legendary | 76–100 | Mythic Threads / Shard Matter | Gold double frame, larger corner ornaments |

Use the previous table’s exact neutral B, Q, gold and floor gates; apply family factors once. Q is `max(previousQ+1, ceil(Q0×1.18^level))`, with Q0=1/3/8/20. Gold follows the previous grade coefficient ×1.3^(gate−1), then the family premium. +0 is acquisition; only +1–20 are upgrades. Upgrade costs and materials strictly increase within a grade; grade transitions can reset recipe requirements. Existing character/training gates remain. Give the starter access to one baseline weapon and needed tutorial materials; cost premiums must not block the opening tutorial.

Neutral attack still matches all 100 existing reference floors. Family factors intentionally differ. **The earlier +0.18% reference effort comparison does not include these family gold premiums, ammo, changed recipes or combat outcomes.** It must not be presented as final pacing validation. Retain PILLAR 1.3, income 1.25, PACE 1.04, WARDEN_RISE 1.02, character cap 30 and the existing ten energy bands. Do not combine old honing with new upgrade multiplication. Epic +17/+18 currently advance durability without neutral attack: show that honestly.

Materials live in a dedicated pack compartment, outside the six combat stacks. Show same-grade colored pixel material icons, owned/needed amounts on hover **and keyboard focus/tap**, and gold readiness. The weapon card links to “Upgrade in the Forge”; the Forge atomically validates instance/version, gate, materials and gold before deducting all three and raising one level. Repeated requests cannot double-charge. +20 displays “Max level”. Preserve existing item identities, equivalent power and invested value during migration; never silently demote rare old gear into a starter.

Keep creature drops and unequal material carriers from the previous research. A planned route, correct counter or cheaper specialist build may progress faster. Mining, its equipment and its death-loss rules remain entirely outside this change.

## Shared wardens and Floor 100

Replace milestone pledges and combined-power victory with actual shared HP. On each server-accepted damage event at time t: `H = min(Hmax,Hprevious + heal_per_second×elapsed) − hit_damage`. Serialize damage/regen, deduplicate hit IDs, award the kill once, and report each accepted strike promptly rather than banking an exchange’s damage until its end. Server action cadence and finite energy remain authoritative.

For a stable attacking window, `group_DPS > heal_rate` is necessary; `H / (group_DPS−heal_rate) ≤ usable_energy_window` must also hold. Illustrative only: HP 4,500, heal 300/s, 30-second energy budget. Fifty players ×10 DPS win in 22.5s; forty need45s and run out; thirty-five skilled players ×15 DPS win in20s. Floor 100 must be calibrated with actual optimized weapon/status DPS and energy-per-swing, not this toy HP.

Boss DoTs tick once per 3 real seconds in this candidate, for two/three ticks; each source owns its timer. Boss stun lasts at most 1 second, followed by immunity until 12 seconds from its application, shared across all attackers. Expose is one shared two-hit state; push changes only the attacker’s local gap. All these timers are independent of the number of chat clients. No accumulated pledges, quorum victory, or timezone compensation. From around floor 10, tune fixed healing above a plausible solo optimized sustained ceiling at that progression band; late floors require increasingly large concurrent groups. Revisit any unavoidable solo burst kill separately. Better coordination still earns a smaller required group.

## Make the decisions readable everywhere

Combat cards show HP, two type badges, speed, distance, outgoing damage channel, next telegraphed action and active effects with remaining duration. Before committing, show reach, affinity, energy/ammo and technique readiness. Explain results concretely: “Shield absorbed55; you lost25HP; shield endurance−55” or “Pushed to Far; bow shot available”. Disabled actions explain why. Forge/pack, loot cards, enemy encyclopedia and Luna’s tool responses must all read the same definitions. Do not rely on color or a hover-only tooltip.

## Future implementation phases and verification

This is a research artifact. Execution requires committed runtime phase plans, each with exact rollback and real Luna dojo scenarios.

| Phase | Deliverable | Proof before proceeding |
|---|---|---|
| 1. Schema / migration | Separate movement, affinity, attack channel, status clock; per-instance upgrades | Old saves load; dry-run inventory mapping preserves value; rollback snapshot |
| 2. Combat core | Unified damage/shield allocation, distance, effects, typed event log | Reach/counters, leakage, wear attribution, duration and energy-per-swing tests; player browser fights |
| 3. Forge / content / UI | 64 variants, materials compartment, arrows, recipes, all cards | Atomic upgrade retries, +0/+20, insufficient gold/materials, old item migration; mouse/keyboard/mobile dojo |
| 4. Wardens / pacing | One damage-event model on all 100 floors; fixed healing schedules | Concurrent hit, idle regen, duplicate, death and kill-reward checks; multi-player dojo on10/50/100 |
| 5. Balance and release | Fixed scenario grid and canary rollout | Floors1–100 × representative types, neutral/optimized/wrong-counter builds; median/P90 energy, money and material time; raid size vs sustained DPS; rollback rehearsed |

Do not “fix” a dominant optimized route merely for beating the average. Flag universal best weapons, infinite stun, unlimited kiting, unaffordable mandatory counters and solo endgame kills. Preserve meaningful specialization and preparation gains. No runtime phase is complete based solely on this atlas or formula checks.

## Kingdom Rush references

Borrow readable resistance categories and paired armor/magic counters from the [KR resistance reference](https://kingdomrushtd.fandom.com/wiki/Armor_and_Magic_resistance), and concise tactical hints from the [in-game encyclopedia text](https://kingdomrushtd.fandom.com/wiki/Encyclopedia). Battles’ [Armored Golem](https://kingdomrushtd.fandom.com/wiki/Armored_Golem) distinguishes physical armor and flying variants; [Aegion Brightsteel](https://kingdomrushtd.fandom.com/wiki/Aegion_Brightsteel) presents displacement, cooldowns and an anti-air ability as separate parameters. These patterns support weapon identity without copying exact numbers. The official [Kingdom Rush Battles page](https://www.ironhidegames.com/Games/kingdom-rush-battles) establishes the multiplayer reference; the older [Kingdom Rush page](https://www.ironhidegames.com/Games/kingdom-rush) describes upgrade specializations. This proposal deliberately does not copy permanent immunities, tower placement, or their economy. Community wiki pages were available through search excerpts; direct Fandom opens were blocked. Accessed 11 September 2026.
