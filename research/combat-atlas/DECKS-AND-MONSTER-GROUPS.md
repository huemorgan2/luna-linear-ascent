# Three-weapon decks and monster groups

**Execution roadmap updated:** [plan 015 revision 2](../../plans/015-weapon-combat-progression/PLAN.md) now incorporates this research into eight rewritten phases and fourteen browser scenarios, including the collection/profile/opening/battle flow and actual-engine simulator. It is ready for review; runtime implementation has not started. The phase-rebase discussion below records the reason for that revision, not an outstanding task to repeat.

12 September 2026 · Design research and proposed replacement scope for [plan 015](../../plans/015-weapon-combat-progression/PLAN.md). **No gameplay changes have been implemented or tested for this proposal.**

## Recommendation

Adopt three permanent battle slots and make an ordinary hunt a continuous encounter against a monster group. Start with enemies arriving **one after another**, with no trip back to town between them. Keep health, wear, ammunition and cooldowns through the encounter. Award XP for each kill; secure the group's gold, materials and items only after surviving the entire group.

**Energy revision from the user:** spend one energy when each individual enemy's fight begins. There is no whole-group prepayment. An enemy begun without energy is fought with significantly reduced performance. Retreat leaves energy for unstarted enemies unspent; the point already spent on an active enemy is not refunded.

This makes preparation matter over several different threats. A sword–staff–bow deck is a useful starting lesson. It should not become a compulsory recipe. A specialist who knows a hunting ground should sometimes earn much more, spend less, or finish faster with two swords and a bow, three bows, or another unusual deck.

**The object of tuning is the deck against a particular group, and the player's progress over many hunts. Individual weapons should have unequal strengths.** A poison sword should be excellent against a living, durable enemy and poor against a short fight or an immune creature. That difference is the reason to own it.

The main reservation is pacing: putting four existing full-length fights in a queue could make hunting slower. Groups need shorter transitions, deliberately composed enemies and an encounter budget. More monsters alone does not remove repetition.

### Decisions from the request and recommendations in this document

| Status | Rule |
|---|---|
| User direction | Exactly three available weapon slots from the beginning; School does not sell more battle slots. |
| User direction | Different weapons are strong against different enemies. Clever preparation and farming can give substantial advantages. |
| User direction | Ordinary monsters travel in groups of at least two; group size and complexity develop through the tower. |
| User direction | A kill earns XP. The player cannot take the group's gold without defeating the whole group. |
| User direction | Each enemy costs one energy when its fight begins. Larger groups demand more energy through their members, not through an upfront group fee. |
| User direction | A player may continue without energy, with significantly reduced performance against those later enemies. Unstarted fights cost nothing if the player retreats. |
| Recommendation | Materials, equipment and consumable drops also belong to the unclaimed group haul. They require a complete victory. |
| Recommendation | First implementation is sequential. Prototype two enemies acting together later; do not introduce unrestricted simultaneous mobs in the first release. |
| Recommendation | Commit the three weapon instances when entering a hunt. Change the active weapon freely as part of an action; rebuild the deck outside the hunt. |
| Recommendation | Start with two enemies; ordinary groups usually contain two to six. Larger authored challenges remain possible after separate pacing tests. These are starting ranges, not a permanent global maximum. |
| Recommendation | Preserve all earned kill XP, including overflow beyond the current bar, without automatic mid-fight level-ups or healing. |

“Three slots” means capacity, not three mandatory occupied slots or one of each class. An empty slot is legal. The pack, armor, shield and charm retain their separate purposes. This is a chosen loadout, not a random card draw system.

## What the game currently does

Inspected the game 0.112.0 source in checkout `1897edd`, including the engine vendored in release `4e052b1`. These are source findings, not a new production playthrough. The wiki's weapon/monster redesign remains a proposal.

| Current behavior | Consequence for this change |
|---|---|
| New players start with one held slot. School sells slot two for 60 XP + 30 gold; slot three requires character level 8, 500 XP and a frontier-scaled fee. | Three slots must be changed in creation, save loading, School, locks, help and clients. Existing purchases need a documented conversion policy. |
| Held weapons use slugs and an active weapon pointer. Some class actions select the first held weapon of a class. | Multiple swords or bows with distinct levels and conditions require explicit instance selection. Slot order must not choose the wrong special ability. |
| A hunt creates one `encounter` with one enemy's HP, profile, specimen and distance. | Add a persistent group containing individual enemy instances and an active member or wave. |
| `_victory` awards XP, gold and loot, updates contracts/weekly progress, clears the encounter and returns to town. | Split individual defeat from group completion. Merely calling the old victory function after each monster would leak rewards and reset the hunt. |
| Ordinary hunt entry costs 1 energy; deep entry costs 2. Ordinary attack turns do not each charge this entry cost. Wardens have separate per-strike energy. | The new hunt rule supersedes both entry prices: one energy per enemy as it engages, in normal and deep groups. Remove the separate group-entry fee; preserve warden energy as a separate design. |
| `gain_xp` clips awards at the current level's full XP bar. Death itself does not remove XP in the inspected death path. | Keeping XP on failure largely fits; honestly awarding every kill requires solving overflow. |
| Ordinary encounter selection reduces the weight of likely lethal enemies using the player's current sheet. Deep hunting skips that adjustment. | Author and publish group selection deliberately. Do not silently adapt the group to counter a clever deck. Any retained beginner mercy needs its own visible, testable rule. |
| Deep hunting starts at floor 4, removes frail/feeble prey and runts, increases attack by 20% and speed by 1, and has its own gold/XP premium. | Retain the tougher-hunt identity. Its old premium was built for single enemies and must be recalculated for group completion. |

Source anchors: [state: creation, held slots and XP](https://github.com/huemorgan2/luna-linear-ascent/blob/4e052b184f15177dd8f8c40b13893d23582a7e33/worldd/vendor/plugin_linear_ascent/engine/state.py), [School and hunt entry](https://github.com/huemorgan2/luna-linear-ascent/blob/4e052b184f15177dd8f8c40b13893d23582a7e33/worldd/vendor/plugin_linear_ascent/engine/core.py), [encounters, victory, death and attack selection](https://github.com/huemorgan2/luna-linear-ascent/blob/4e052b184f15177dd8f8c40b13893d23582a7e33/worldd/vendor/plugin_linear_ascent/engine/combat.py), [costs and progression constants](https://github.com/huemorgan2/luna-linear-ascent/blob/4e052b184f15177dd8f8c40b13893d23582a7e33/worldd/vendor/plugin_linear_ascent/economy.py).

## What “unequal weapons” should mean

We should not target equal damage, equal win rates or equal farming income for every weapon. We should make the differences understandable and useful. Across the world, players need a collection of answers; in one hunt they choose only three.

There is no requirement to buy every one of the 64 grade variants. Every family should offer a useful reason to choose it somewhere. A mandatory purchase checklist would replace experimentation with shopping. An upgraded lower-grade specialist can remain useful while the player invests in a different higher-grade role.

| Matchup or situation | Advantage worth preserving | Meaningful disadvantage |
|---|---|---|
| Living enemy with enough HP to survive several phases | Viper poison or Briar bleed | Wasted duration on tiny enemies; corresponding immunities can defeat the idea. |
| Dangerous charge or heavy next attack | Thunder/Stormbell stun | Lower direct output; resilient enemies resist repeated control. |
| Ground pursuer followed by a vulnerable ranged target | Ramguard/Recoil push; bow follow-up | Costs setup; flying pursuit can close the opening quickly. |
| Armored ground enemy | Magic, arcane arrows or Hexglass/Sundering setup | Magic resistance and spell-dispersing flyers change the answer. |
| Fast flyer reaching contact | Skirmisher bow | A cover specialist may kill a slower flyer more efficiently. |
| Long approach or retreat-sensitive enemy | Hawkeye, Pinning, Frostbind or Repulsor | Less useful against an enemy already at contact or immune to displacement. |
| Flammable creature | Ember or fire arrows | Poor choice against fire-resistant targets; ammunition has a cost. |
| Short ground fight without a special defense | Breach Cleaver's direct impact | Cannot reach air; loses relative value when a specific utility prevents a dangerous action. |
| Mixed physical/magic targets | Runestring with selected arrows | Ammunition, contact penalties and lost specialist slots are real costs. |

The existing **16 families and 64 distinct grade drawings stay**. Groups strengthen the reason for those families; they do not justify shrinking the catalog to three default weapons. Revisit redundant families after testing actual encounters, not by forcing their attack averages to match.

### Enemy axes remain separate

Common, Power and Magic describe defensive affinity. Ground and Air describe movement/reach. A flying enemy can also be Power or Magic. A “Common / flying / Power group” therefore needs actual combined profiles, not three mutually exclusive labels.

| Enemy profile | Useful answer in the existing proposal | Group design use |
|---|---|---|
| Ground Common | All channels work well | An opening lesson, a fragile nuisance, or a fast threat; not automatically harmless. |
| Ground Power | Magic; arcane arrows | Tests access to a second damage channel. |
| Ground Magic | Blade or ordinary arrows | Punishes a deck built only around spells. |
| Air Common | Bow; weaker spell alternative | Introduces reach and pursuit. |
| Air Power | Ordinary arrows; visible spell-dispersal exception | Strong anti-air requirement; magic is especially inefficient here. |
| Air Magic | Ordinary arrows | Punishes reliance on magic for all airborne enemies. |

Keep the [existing proposed multiplier matrix](PLAN.md), traits and immunity displays as initial candidates. Their combination with groups still needs validation. We must not silently “fix” the deliberately unusual Air Power exception while implementing groups.

### Example decks and routes

| Deck | Where it should excel | What it gives up |
|---|---|---|
| Breach Cleaver + Ember Staff + Skirmisher Bow | First exploration of a mixed route | Fewer control combinations and weaker specialization. |
| Viper Edge + Ramguard Sword + Skirmisher Bow | Living ground prey with occasional flyers | Ground Power enemies may require costly arcane arrows or a slower kill. |
| Hawkeye + Skirmisher + Runestring | Air-heavy hunting; different ranges and arrow channels | Ammunition spending and fewer melee/control answers. |
| Thunder Maul + Hexglass Staff + Recoil Bow | A route with a few very dangerous actions | Lower burst against many weak enemies. |
| Breach Cleaver + Briar Saber + Ramguard Sword | A known, living ground route with favorable affinities | An airborne encounter may be unwinnable. The player should know that before entering. |

These are examples, not recommended equal performers. If an informed three-sword deck is exceptionally profitable on one ground trail, keep that advantage. If one deck is best on every trail in damage, safety and cost, it has erased the decision.

All bows currently accept multiple arrow types in the proposal. That can let a bow cover both channels and free another slot. **Allow that clever substitution.** Make payload quantities, costs, reach and contact effectiveness honest; do not add an arbitrary staff requirement to defeat it. Check whether bows cover every role too cheaply before changing their versatility.

## How a group encounter works

### Prepare, commit, fight, secure

Before entry, show the actual group members in order, their images, movement/affinity, visible traits, difficulty and reward rules. Show one energy per enemy, energy currently available and how many enemies it covers; a five-enemy group requires five energy to fight every member at normal performance. Insufficient energy is a warning, not an entry lock. The player can arrange their deck using what they already own. Browsing or reloading the card cannot reroll the offer. Encounter offers are persisted; deliberate scouting should reveal information, not provide unlimited free lottery rolls.

After entry, the three instance IDs are committed until victory or successful retreat. The player can attack with any of those weapons without a separate switch tax. The attack still consumes its normal combat action and ammunition/wear. Pack weapons, trade, gifts, crafting and School cannot supply a fourth answer in mid-hunt. A newly dropped weapon stays in the pending haul until victory.

Own several deck presets if useful, but only one is active. Duplicate families are allowed as separate owned instances; the same physical item cannot occupy two slots. Effects and endurance belong to the selected instance. Cooldowns persist when switching weapons; enemy control resistance prevents cycling three stun weapons into permanent safety.

### Sequential first; simultaneous later

| Approach | What it adds | Main problem | Recommendation |
|---|---|---|---|
| One enemy active, next arrives automatically | Deck coverage, resource endurance, order and commitment | Can resemble repeated old fights if transitions and HP are unchanged | First complete playable implementation. |
| Waves with up to two active enemies | Target priority, control one while attacking the other, future area attacks | Needs per-enemy intents, targeting, distance, DoT clocks and an incoming-damage budget | Separate prototype after the sequential first-ten-floor loop works. |
| An arbitrary number all attacking together | Large spectacle and area-damage value | One player action can trigger many enemy attacks; readability and survival collapse quickly | Not the initial ordinary-hunt design. Larger groups can still arrive in waves. |

The group should feel like **one scene**. The kill action awards XP, marks that portrait defeated and reveals the next enemy, ready to engage, in the same response. Showing that enemy does not start its fight or spend energy. The player's next combat action starts the fight, settles its one energy charge or exhausted state, and performs the action in the same transaction. No obligatory loot screen, town visit, new Hunt click or “Continue” click between members. Do not automatically choose the player's next attack.

Between enemies, the player may leave and forfeit the pending haul without starting or paying for the next fight. Once an enemy's fight has begun, retreat uses the normal escape mechanics and its energy is already spent. Inspecting portraits or weapon details is free; attacking, advancing, guarding or using a combat consumable begins the waiting fight. This prevents a free combat action before the energy check while preserving a zero-extra-click transition.

Preserve current HP, shield wear, weapon condition, ammunition, consumables, player effects and weapon cooldowns between enemies. Enemy-specific poison, stun and Expose belong to that enemy and end when it dies. Killing something is not a cooldown reset or free heal. Durable poison targets should remain in the roster; shortening every enemy into a one-hit victim would remove an entire weapon role.

Each group's arrival rules specify the next enemy's starting distance. Do not reset to Cover after every kill and hand bows repeated free openers. Do not always spawn at Contact and remove bows' range advantage either. Show the next arrival distance; flying enemies close it faster. A newly arrived enemy cannot attack before the player gets an action against it. Pushing an enemy buys distance in the current exchange, not an automatic advantage against every later member.

Local combat progresses through accepted actions. Disconnecting preserves the group and haul, consumes no additional turns and gives no automatic victory. Reconnecting restores the same enemies and resources. Town healing, sleeping, School advancement and deck changes require leaving the hunt. Explicitly prevent daily reset/level-up code from injecting a free heal or ability reset mid-group; any deferred outside-combat recovery must be recorded and applied once after exit. Wardens retain their separate real-time clock.

Consumables already carried may be used under their stated action cost. Fix the life-saving-item limit at the **group** scope: killing a member does not refresh it. A revive that keeps the player in combat keeps the group active. A daily rescue that extracts the player abandons the haul. A normal escape attempt remains tactical; if it fails, the hunt continues and the haul has not yet been forfeited.

### Group examples

These are encounter templates, not additions replacing the existing 425 species. Bind each role to actual local animals and images, respecting the three-nearby-variants limit.

| Template | Composition/order | Decision it creates |
|---|---|---|
| Opening pair | Two fragile Ground Common creatures | Learn health carry-over and the final group reward with a starter weapon. |
| Woodland patrol | Living ground prey → flyer → Ground Power guard | Keep ranged coverage and save a magic answer for the end. |
| Marsh hunt | Long-lived, poison-susceptible ground animal → fast Common flyer | Poison is valuable on the first target; switch before the air rush. |
| Arcane nesting ground | Ground Magic defender → Air Magic hunter → fast Air Common | Physical specialists can outperform the general deck. |
| Armored procession | Several Ground Power enemies with different control resistances | Magic-heavy decks get a profitable niche; repeating stun alone does not solve every defender. |
| Later two-enemy wave prototype | Slow heavy attacker + fragile ranged harrier | Interrupt one, kill the other; incoming actions are visibly scheduled. |

Authored routes should have different compositions and rewards. Not every group should include every counter check. Let players avoid a poor matchup, target a carrier, or specialize in an unusually profitable route. Preserve basic low-risk recovery routes at high floors as well as dangerous opportunities.

## Rewards: every kill teaches; the whole victory pays

| Event | XP | Gold/materials/items from this group | Other state |
|---|---|---|---|
| Non-final enemy defeated | Credit its full earned XP once | Roll once and record in pending haul; unusable | Health, wear and cooldowns carry into the next member. |
| Group fully defeated and player survives resolution | Credit final kill XP once | Atomically secure the complete haul once | Unlock reward-eligible contract/weekly/assist credit; leave combat. |
| Successful retreat or rescue extraction | Already earned XP remains | Entire pending haul forfeited | Energy for begun enemies, ammunition, consumables and wear remain spent. Unstarted enemies cost no energy. |
| Death, including mutual final defeat | XP for resolved kills remains | Entire pending haul forfeited | Apply the separately specified death policy to possessions brought into the hunt. |
| Revival that continues combat | Earned XP remains | Haul remains pending | Group and used life-save state persist. |
| Disconnect, refresh or request retry | No repeated XP | No new roll or payout | Resume the exact encounter, including whether the current enemy has begun and was funded. No repeated energy charge or exhaustion reset. |
| Full ordinary pack at final victory | XP is unaffected | Victory still secures ownership; overflow goes to a persistent claim area | No forced deletion or reward reroll; materials use their dedicated compartment. |

The haul is **not the player's carried purse**. Existing banked gold and previously secured materials do not become contingent on this hunt. Pending gold cannot pay for a potion, repair or trade. Failed-haul forfeiture must not also subtract that same pending gold from the player's purse. Death penalties and the earlier proposal to preserve upgraded weapons remain separate, visible rules.

An overflow claim area holds that victory's secured items until the player stores, sells or discards them; resolve it before entering another hunt. It must not become unlimited free pack storage. Compute each kill's XP from its defined reward basis before gold goes into escrow. The current rule limiting wilds XP relative to that kill's gold must not be applied to the zero gold credited to the purse during an unfinished group.

Lifetime kill statistics can update per kill with XP. Gold-bearing contracts, weekly milestones, alpha spoils and assist payouts must not become an alternate way to collect loot from an unfinished group. Record provisional qualifying progress and make it reward-eligible on completion. Include local play, HTTP play, rescue/assist hooks and multi-tab actions in this audit.

### XP overflow is a real scope change

The present full-bar clipping would make later kills teach nothing just as the group becomes interesting. Recommend preserving overflow as an **earned XP reserve**, shown alongside the current bar. It survives defeat and supplies the existing XP pool as School training/advancement consumes XP. The normal character-level cap, gold charges and advancement requirements still apply; there is no automatic mid-hunt level increase, stat increase or healing.

Count base and rested XP once in the same kill transaction; never consume a rested bonus and then discard its overflow. The reserve's spending order and level-30 behavior need explicit implementation fixtures. This changes XP retention, so it belongs in the progression simulation together with removed slot costs and weapon honing costs. It cannot be treated as a harmless UI change.

Choosing a route to earn easy XP and retreat is allowed. It spends energy only on enemies whose fights actually begin, plus time and the forfeited haul. Fighting without energy reduces performance, making further XP harder to earn. This controls acquisition speed; it does not resolve storage at a full XP bar, so the reserve above remains a separate recommendation. Do not add an exhaustion XP haircut: an enemy actually defeated still awards its normal earned XP. Replaying the **same kill ID** for repeated XP, free engagement resets or reopening the same dropped item are bugs.

## Progression through the tower

Increase the demands of composition, enemy behavior and preparation as well as count. Floor number still drives the existing exponential reference. Group size is an authored setting, not another exponential multiplier.

### Starting group ranges to test

“Actions” below means player combat decisions in a successful, sensibly equipped hunt, not energy charges. These are prototype budgets, not simulated results or a limit enforced by suddenly ending a fight.

| Hunting floors | Usual group size | New demand | Candidate ordinary action budget |
|---|---:|---|---:|
| 1–3 | 2 | Common ground pair, then a clearly taught reach/affinity check | 4–8 |
| 4–10 | 2–3 | Mixed profiles; first optional deep hunt; one useful control/status lesson | 6–12 |
| 11–25 | 2–4 | Choose a route and prepare for the strongest member | 8–14 |
| 26–50 | 3–4 | Grade transition, ammunition decisions, more species traits | 8–16 |
| 51–75 | 3–5 | Order matters; durable and fragile targets mixed | 10–18 |
| 76–100 | 3–6 | Specialized elite compositions and sustained resource pressure | 10–20 |

Short two-enemy routes can remain available later. Optional eight- or twelve-member challenges can be authored later as several waves, with an explicit duration and haul; they should not become the default grind simply because they are possible. This table concerns hunting on floor 100, not the shared floor-100 warden.

Beginner groups must be beatable using normally obtainable gear before introducing a hard reach requirement. Give basic Common blade, bow and staff access through the authored opening, without rare drops or former School slot fees. Three slots do not require a beginner to buy three expensive upgrades before making any progress. Test one main investment plus two serviceable tools, then different specialist spending policies.

### Energy is paid per enemy, when fighting it begins

This replaces the earlier `ceil(group size / 2)` entry-price suggestion and the doubled deep-group fee. **Normal and deep hunting both use one energy per enemy.** Deep hunting's additional danger and better rewards remain; removing its old energy premium requires recalibrating its net progression advantage.

1. Inspecting the group is free. Beginning its first enemy's fight commits the deck and checks energy once.
2. If at least one energy is available, deduct one and mark that enemy **funded**. The player fights it normally, even when this deduction leaves the energy bar at zero.
3. If no energy is available, spend zero and mark that enemy **exhausted**. The fight can proceed with the performance penalty; energy never becomes negative and no future debt is created.
4. Further attacks, misses, blocks, DoT ticks and weapon switches against that same enemy do not charge again. Its funded/exhausted state lasts until that enemy's fight ends.
5. After a kill, show the next enemy without beginning its fight. Continuing with a combat action repeats the check; leaving does not.

Energy availability is checked on the server at the actual start of each fight. Ordinary regeneration can fund a later enemy if a point has returned, but it does not retroactively refund a charge or remove the current enemy's exhaustion. Reconnect, revival and failed escape retain the current enemy's energy receipt and state. Any future energy-restoring consumable must explicitly define its interaction with this rule before release.

#### Five enemies, two energy

Assuming no regeneration or energy restoration during the encounter:

| Enemy whose fight begins | Energy before | Spent now | Energy after | Performance for this enemy |
|---|---:|---:|---:|---|
| 1 | 2 | 1 | 1 | Normal |
| 2 | 1 | 1 | 0 | Normal — its energy was paid |
| 3 | 0 | 0 | 0 | Exhausted |
| 4 | 0 | 0 | 0 | Exhausted |
| 5 | 0 | 0 | 0 | Exhausted |

Starting with five energy and leaving after defeating two enemies spends **two**, leaving **three**. Leaving during enemy 2 also spends two; beginning that fight already used its point. Merely viewing enemy 3 spends nothing. All XP from completed kills stays; leaving forfeits the entire pending haul.

#### Proposed exhaustion strength to test

The user specified a significant performance reduction; the exact numbers below are a **tuning proposal**, not an approved or measured result.

| Parameter against an exhausted enemy | Starting proposal |
|---|---|
| Player outgoing damage | 50% of the otherwise resolved damage, applied once before final integer rounding/minimum damage. Includes direct hits, new poison/burn/bleed damage and damaging techniques. |
| Effective player speed | Current effective speed minus 2, minimum 1, for pursuit, dodge and escape calculations. |
| Weapon identity and defenses | Keep reach, affinity, immunities, control rules, shield absorption and durability rules. Exhaustion changes performance; it does not change the weapon's permanent stats. |
| Rewards for a kill | Normal earned XP; normal pending drops. No additional exhaustion reward penalty. |

Capture the exhaustion multiplier for each damaging effect once; a DoT must not be halved both when applied and when it ticks. Existing rounding and minimum-damage rules need explicit small-number fixtures. The state belongs to the enemy engagement, so swapping weapons cannot clear it. Retain normal control resistance so low-damage stun cycling does not create indefinite safety.

This is a soft constraint, not a hard XP ceiling: sufficiently prepared players can still defeat some enemies while exhausted. Measure exhausted XP and secured rewards per active minute, not just per energy, especially on easier floors. Keep useful specialist advantages; verify that exhaustion materially hurts frontier performance and cannot be bypassed by armor, minimum-damage rounding, repeated control or stale clients. Do not claim that energy alone eliminates XP farming.

For a later simultaneous-wave prototype, every enemy costs one point when it becomes active, including enemies hit by area damage. Never charge waiting waves. The prototype must define how funded and exhausted opponents interact in the same wave before enabling simultaneous combat; the initial sequential implementation has one unambiguous current-enemy state.

### Threat budgets

Do not multiply every group's size by a full old monster's HP, attack and payout automatically. Choose a template's encounter budget, then distribute it unequally: a fragile opener, a durable central threat and a fast finisher can have different roles. Any group-role stat modifier must be visible in the dossier and reward calculation, with specimen/grade factors applied exactly once.

Estimate threat using actions to kill, incoming damage, pursuit, dangerous intents, control immunity and required resources against a specified deck. HP totals alone miss a flyer the deck cannot reach, or a heavy attack that a stun prevents. Do not secretly rescale enemies after observing the player's gear. Better equipment should actually make the same hunt easier.

Each fully funded enemy now consumes its own point, so group size no longer multiplies full-strength kills per energy. Partial runs spend only the points for fights that actually began. Retained wounds, shorter transitions, deep rewards and exhausted kills still change progress; simulate those effects before fixing reward coefficients. More efficient routes need not be equalized to the average.

### Why the old per-fight success target is insufficient

An illustrative model with independent 80% survival on each enemy gives these whole-group completion rates:

| Enemies | All defeated at 80% per enemy |
|---:|---:|
| 2 | 64.00% |
| 3 | 51.20% |
| 4 | 40.96% |
| 6 | 26.21% |

Real fights are not independent: retained wounds, order and limited tools change later survival. The example shows why we cannot reuse “80% ordinary encounters won” as an 80%-per-monster gate and call the new hunt playable.

For another **toy calculation**, assume three identical independent encounters, 80% conditional success each, 10 XP per kill, 100 total gold secured only on completing all three, and at least three starting energy. Each fight starts only if the previous enemy was defeated; failure ends the run. Expected energy spent is `1 + 0.8 + 0.8² = 2.44`. Expected XP is `10 × (0.8 + 0.8² + 0.8³) = 19.52`; expected secured gold is `100 × 0.8³ = 51.2`. Across repeated attempts, this is approximately `51.2 / 2.44 = 20.98` gold per energy before costs, and `19.52 / 2.44 = 8` XP per energy. A complete win uses three energy. This is not a prediction of Ascent's economy; insufficient starting energy changes later performance and invalidates the constant 80% assumption.

The account metric is:

`net gold per energy = (secured gold − ammo − repairs − healing − expected carried-gold loss) / total energy spent`

Use aggregated rewards and costs divided by aggregated energy over comparable attempts. If no energy was spent, report that metric as undefined and separately show exhausted kills, XP and net rewards per active minute and elapsed hour. Do not hide zero-energy hunting by dividing by an invented minimum energy cost or dropping those runs.

Measure comparable net materials, retained XP, actions, active minutes and waiting time. Also measure time to equip and maintain **three useful weapons**, not only time to max one sword. Keep the existing 1.3 power/capital scale, 1.25 income scale, 1.04 pacing ratio and character cap 30 as reference anchors; adding group size must not silently multiply the climb's income or required investment.

## Unequal monster drops inside a group

Keep the [wiki's species/floor/specimen/deep rarity model](WIKI-LOOT-AND-SOURCES.md) as the input to recalibration. Each enemy has its own roll: four independent material-grade chances and one categorical weapon result, including no weapon. A group can therefore contain multiple equipment drops from different enemies. Do not turn this into one identical chest roll for every group.

Resolve rolls once using the enemy instance and encounter ruleset; store the result on that enemy's kill receipt and in the pending haul. Securing the haul must not roll again. Bought starting levels 0/2/4/6, crafted +0, and dropped +0 with 40/30/20/10% condition remain separate acquisition settings; a group victory does not make damaged drops full-condition.

The wiki needs both **per-enemy drop chance** and **group chance of at least one drop of that grade**. With independent, fixed probabilities `p_i`, the latter is `1 − product(1 − p_i)`. For an illustrative two-enemy group with 2% and 5% chances, that is 6.9%, not 7%. Label it conditional on defeating the group. “Chance to take this home per attempt” additionally depends on the deck and survival and requires simulation; do not publish one universal number.

If a dry-streak safeguard is adopted, make its group semantics explicit: eligible kills count toward its pending progress, but only a cleared group's progress becomes permanent. A failed group cannot consume an owed guarantee. On a clear, secure the guaranteed bundle and reset the counter atomically. The guarantee stays within its native grade and preserves the appropriate carrier ratio. Publish base odds and guarantee state separately. This remains a recommendation, not a requirement to make rare outcomes equal.

Deep hunts should offer higher valuable-drop chances on their tougher creatures. Their **net** advantage should be real for prepared decks, while an unsuitable deck may lose most hauls. Do not increase every rarity by one common factor just to make tables symmetrical, and do not assume that a larger displayed chance compensates for repeated total losses.

## What the player sees in the game and wiki

Use the game's pixel icons, font, consistent text sizing and distinct grade artwork/frames. Add to the existing wiki instead of creating another competing reference.

| Surface | Required change |
|---|---|
| Deck/pack | Three fixed battle cells; active weapon, family ability, grade, upgrade level, condition and ammo requirements; clear separation from storage capacity. |
| Hunt preview | All group portraits, sequence or waves, floor/biome, profile icons and notable traits. Show “1 energy per enemy,” available coverage and likely exhaustion, plus “XP per kill; haul after full victory.” |
| Combat | Group progress, current enemy and next arrival, three weapon actions, gap, visible enemy intent, statuses/cooldowns, HP and endurance. Show whether this enemy's energy was paid or the player is exhausted, with actual affected stats. |
| Kill transition | A compact “enemy 2 of 3 defeated; +XP earned” event and pending haul. Next enemy is visible but not yet begun; its energy cost/exhaustion warning and the leave option are clear. |
| Victory/retreat/death | One receipt distinguishing XP retained, haul secured/forfeited and losses to possessions brought in. |
| Monster dossier | Actual species art and parameters, relevant group templates, effective role/specimen stats, individual rarity rates and material carrier mix. |
| Group settings in wiki | Floor, route, roster/order, mode, count, active-enemy limit, arrival rules, one-energy-per-enemy policy, proposed exhaustion coefficients, reward settings and conditional group rarity chances. |
| Deck comparison in wiki | Choose three weapon instances/levels and inspect coverage, blind spots and resource costs against a selected group. Show a matchup explanation, not one universal “best deck” score. |
| School and help | Remove battle-slot purchases and their unlock messages; keep weapon learning/mastery and unrelated pack progression. |

Follow the existing UI rule: up to six options use visible selectable controls; more than six may use a dropdown. Monster sliders must continue changing the actual floor roster and images. Display proposal versus implemented rules clearly until release.

## What must change in implementation plan 015

This is a foundational revision, not a later “groups” feature bolted onto phase 4. The reward boundary, XP retention, item selection and first-session budget all change. The existing phase instructions must be rebased before runtime execution; their old single-enemy acceptance targets are no longer sufficient.

| Existing phase | Revised scope needed |
|---|---|
| 1 — Baseline | Measure today's single hunts, action counts/latency, XP clipping, slot spending and energy. Model funded/exhausted group completion, partial energy spending and three-weapon ownership. |
| 2 — Definitions/migration | Add fixed decks, enemy/group instances, persistent offers, per-enemy start/energy receipts, per-kill XP receipts, pending haul, completion settlement and XP reserve. Map School purchases and active legacy fights. |
| 3 — First ten floors | Deliver the full sequential group loop with starter coverage, per-enemy energy, exhaustion, retreat before the next enemy, partial XP, lost haul, resumed groups and first Forge upgrade. This is the first playable milestone. |
| 4 — Combat/content | Compose local species into varied groups; validate all weapon roles. Prototype two active enemies only after sequential pacing is proven. Add target/intent rules before any multi-target ability. |
| 5 — Economy | Simulate three-weapon acquisition/upgrades, group failure, per-enemy drops, secured rewards, early retreat, exhausted XP farming, arrow substitution and deep routes at one energy per enemy. Retire per-single-monster fairness targets. |
| 6 — Wardens | Preserve real shared HP/healing and finite-energy concurrent attacks. Re-evaluate player damage/resources after the new hunting economy; remove pledges as already intended. |
| 7 — Real play | Add group/deck walkthroughs, multi-tab/reconnect/overflow/death cases, specialist routes and returning-player compensation. Rehearse migration and rollback. |
| 8 — Release | Release coherent rules in a QA canary first; monitor completion, net income, route/deck choices, XP retention and stalled progression. |

Keep the 64 weapon drawings, 425 creatures, source settings, exponential upgrade research, eight materials, Forge flow, partial shield protection and concurrent-healing warden objective. Recompute their combined outcomes. **Mining stays in [plan 013](../../plans/013-mining-and-gathering/PLAN.md).**

Shared wardens are not ordinary private monster groups. Do not make their attacks wait for a private group settlement or turn a player's three weapons into three free attacks. There is one accepted attack action at a time per player. The floor-100 kill still requires real players damaging shared HP faster than its healing and finishing within their energy/survival window. Clever preparation may reduce the headcount; gear improvements must not secretly raise boss healing to cancel that advantage.

### Technical contract and migration questions to resolve first

A versioned group needs: group ID, offer ID, owner, floor/route/mode, rules version, committed weapon instance IDs, enemy instance IDs and order/waves, action revision, shared encounter resources, XP receipts, pending loot and settlement status. Each enemy needs its own HP, distance, traits, status timers, kill ID and reward roll, plus waiting/active/defeated state and an engagement receipt recording energy before/after, actual charge (0 or 1), funded/exhausted status and the exhaustion rules version. The authoritative server must reject stale or duplicate actions and illegal deck substitutions.

Starting an enemy's fight atomically checks current energy, charges at most one point, records its status, and accepts the triggering combat action. Kill resolution marks the next enemy waiting, never charged. Repeating the start action, reconnecting, reviving or failing escape must not charge again or change the recorded status. Invalid actions cannot begin a fight or consume energy.

The last kill transaction must record kill XP, finalize enemy state and either settle the complete haul or record failure after resolving the phase. Group completion is **all enemies defeated and the player standing after resolution**. Retries cannot pay a second time. Distinguish this from a reconnect that simply displays an already committed result.

| Migration case | Recommended handling |
|---|---|
| Existing one-/two-/three-slot player | Set battle capacity to three; retain owned instances, order and active selection. Do not reset training or ordinary pack capacity. |
| Paid extra slots | Refund recorded gold/XP costs once where transaction history is available. Third-slot gold used the frontier at purchase, so today's price is not proof of the amount paid. |
| Missing purchase history | Inventory the evidence before selecting compensation; publish a consistent fallback. Do not invent a historical payment or pay an unbounded current-frontier windfall. Refund XP must not disappear at a full bar. |
| Old active single-enemy fight | Let it finish under its pinned old rules before the next hunt uses groups; do not append surprise enemies or claw back already awarded rewards. |
| New player without a counter | Authored starter access before the first mandatory reach/channel check; no rare-drop dependency. |
| Rollback after new group writes | Keep compatibility readers and receipts. Stop new group entries, then finish or explicitly resolve active groups once; never restore a stale whole-player snapshot. |

The School handler emits `train` ledger entries with `carry 2`/`carry 3` notes; audit actual retention before promising exact universal refunds. Rescue and assist flows also currently start or reward individual fights and must inherit an explicit group policy, not accidentally bypass it.

## How we prove this is playable

Test unequal policies on the **same authored offers**, with normal earned resources. A poorly chosen deck is allowed to lose. A specialist is allowed to dominate its favored route. We only guarantee that required progress has an understandable, obtainable route and that a failure does not leave the player unable to play again.

| Test | Evidence required before launch |
|---|---|
| First session | A fresh account handles the opening pair, sees both XP and haul, obtains the first required counter and reaches the planned first upgrade with ordinary resources. |
| Per-enemy energy | Five enemies with two energy: enemies 1 and 2 remain normal, 3–5 are exhausted, total spent is two. Five starting energy and retreat after two enemies leaves three. Previewing the next enemy, switching weapons and retrying a request do not add charges. |
| Exhaustion boundaries | Begin at zero; spend the final point; miss; fail escape; revive; reconnect; regenerate mid-enemy and between enemies. Check the state is latched per enemy, energy never becomes negative, modifiers apply once, and legal kills retain XP. |
| Useful specialization | Each family has a demonstrated intended niche. Compare general and specialist decks on several contrasting groups; publish time, damage, ammo and secured rewards, not equal win-rate targets. |
| No mandatory impossible group | Every required encounter has an obtainable answer before entry. A three-blade player gets a clear flyer warning rather than an invisible reach trap. |
| Encounter completion | Report whole-group victory, retreat, death and abandonment by floor, route and deck. As an initial QA gate, aim for at least 90% completion on the authored beginner route and 80% on designated prepared ordinary reference routes; these are not quotas for all decks, species or deep hunts. Freeze against baseline and actual play. |
| Pacing | Compare equal progression tasks, not just number of kills. Sequential transitions add zero compulsory clicks. Record median/P90 actions and active minutes; the candidate action ranges above trigger review when exceeded. |
| Economy | Track median/P90/P99 time to a functional three-weapon deck, first/next upgrades, grade transitions and recovery. Include uncompleted runs, partial energy costs, exhausted runs and secured material pairs, not just items rolled. |
| XP honesty | Fill the bar on an early kill, then kill again and lose the group. All earned XP is still accounted for once; no automatic level-up heal. Test rested XP and level 30. |
| Loot settlement | Win, flee, die, revive, rescue, disconnect and retry the last action from two clients. No premature items, duplicate XP, lost secured ownership or double gold. |
| Counter timing | Push→bow, poison→switch, stun resistance, arrival distance, shield leakage and cooldown carry-over work with the actual next enemy. No wave-transition heal or opener exploit. |
| Smart farming | Include profitable specialist routes and deliberate partial-group XP farming. Distinguish good choices from repeated receipts or free rerolls. |
| Deep hunts | A prepared route shows a real net benefit after failures and costs; wrong decks can perform much worse. Verify one energy per begun enemy, with no old two-energy entry fee or doubled per-enemy charge. Recalibrate each rarity, carrier and gold/XP premium. |
| Returning players/wardens | Migration preserves investment; removed fees and new XP/loot rates do not bypass the late shared-warden solo ceiling. Real concurrent groups can still win. |

Use at least 10,000 seeded account runs per representative policy after a small calibration run, followed by real browser/Luna walkthroughs. Report Monte Carlo uncertainty, especially for rare drops; 10,000 runs alone cannot validate exceptionally tiny Legendary probabilities. Add targeted probability/settlement checks for those tails. Coded tests do not substitute for judging whether the encounter feels repetitive or whether a player understands the last enemy's threat.

Retire the old blanket “all ordinary encounters 80%” interpretation, the one-main-plus-one-counter budget and the 25–50% smart-play improvement as a ceiling or required equal gap. Do not automatically reuse the earlier P90-material target or ±15% progression envelope: record them as historical benchmarks and decide intentional changes using complete-group outcomes. A very strong local strategy is welcome if other encounters still justify other tools.

## Relevant reference games

Ironhide's own **Kingdom Rush Battles** guide describes physical armor answered by magic, magic resistance answered by physical options, and a deck containing complementary tower classes. The useful connection is readable counters and coverage through several choices. Our inference for Ascent is to borrow that clarity while allowing specialist hunting decks and retaining this game's distinct Air Power rule. Ironhide's guide does not establish our group rewards, prices or progression numbers. [Official armor/deck guide](https://support.ironhidegames.com/support/solutions/articles/4000223666-armor-types-breakdown-kingdom-rush-battles-guide).

**Into the Breach** describes telegraphed enemy attacks and planning a counter each turn. The useful inference is that a player can make a smarter decision when the coming threat is visible. If Ascent later has two enemies active, show who will attack, move or charge before asking for a target. This is inspiration for information design, not a proposal to copy its combat system. [Subset Games' description](https://www.subsetgames.com/itb.html).

## Research status and next step

Plan 015 revision 2 is now rebased around **three fixed weapons → one energy per enemy as its fight begins → exhaustion when unfunded → per-kill XP → one secured haul**. The next step is user review of that complete plan before implementation. The user's energy rule replaces the original group-entry pricing; exhaustion numbers remain proposals. Build that complete first-ten-floor loop before expanding group complexity. Simultaneous waves remain a separate prototype decision; they are not necessary to deliver the first improvement.

This document records source inspection, design reasoning and illustrative arithmetic. It does not claim measured completion rates, tested economics or a finished gameplay plan. The parent plan is marked for revision so its original phases cannot be mistaken for an executable specification of the new design. No runtime code, wiki release, migration, simulation campaign or dojo run was performed.

Documentation verification after the energy revision: all 23 local Markdown links resolve. The five-enemy/two-energy trace, five-energy retreat example and revised expected-energy/XP/gold arithmetic match the displayed values. Whitespace and secret-pattern checks passed. These checks validate the document, not the proposed game balance; no runtime tests were run.

Documentation rollback: revert the documentation-only commit containing this research and its two index/scope updates, preserving unrelated work. Runtime rollback must be specified in the rebased implementation phases before execution.
