# Shared group resolver — implementation contract

The implementation belongs to `plugin_linear_ascent.engine`, imported unchanged by local play, worldd and the simulator. The first-ten-floor slice proves this resolver before content expansion. No research-only calculator resolves an actual fight.

## State and actions

A group has a monotonic ID, persisted full roster, current member index, committed deck IDs, cooldowns, pending money/materials/weapons, action sequence and result. Members store their exact identity/art, independent affinity/reach, HP/attack/defense/speed, gap, effects, started/paid/exhausted/kill-paid flags and rolled rewards. Opening rolls once, costs no energy and does not commit the deck; the first valid combat action commits it. Re-reading never advances any counter or roll. No action can skip a member.

`strike:<instance>` attacks with one of the committed three. `skill:<instance>` uses its described ability only if ready. `approach`, `withdraw` and `flee` change distance or attempt escape; only legal begun actions charge a previously waiting enemy. Flee before starting an enemy abandons the haul without charging that enemy. Invalid IDs, unreachable strikes and cooling abilities refuse before cost/RNG/wear. A legal zero-energy action starts that member exhausted: half outgoing attack and two less speed until that member ends. New energy can pay for the next member only.

Enemies resolve sequentially. A kill pays XP once immediately, copies rolled rewards into pending haul and reveals the next member at cover distance; it does not heal, reset cooldowns or charge the next member. Final victory transfers the entire haul exactly once. Items live in the dedicated collection/material store, so old consumable-pack capacity cannot erase them. Encounter objectives and external kill notifications receive completion only after the full group; preserve immediate per-kill XP in the engine ledger. The result records kill count, paid energy, exhaustion and secured/lost haul for clients and simulator accounting.

The group dispatcher takes priority over all legacy global inventory/town actions. During committed combat, allow only scene/collection inspection and explicit combat actions/validated combat supplies. No remote healing, weapon replacement, banking, Forge, School, sleep or claim can escape this boundary. Uncommitted preview may return to camp without reward/cost. Expedition groups inherit a locked deck and return their winning haul to the expedition, never the bank.

## Combat and progression

Use the approved six-entry affinity/reach matrix and authored weapon families. Blade contact is required; ordinary bows are Power, staves Magic. Bow contact penalty, cover shot, push, stun recovery, slow, poison/burn/bleed and expose come from engine-owned values. Tick status durations and cooldowns once per enemy response phase, including blocked responses, with unique event IDs. Push suppresses pursuit that phase. Stun cannot chain without its shared recovery. Damage-over-time uses source attack, never maximum enemy HP. Landed hits leave at least25% HP damage after shield absorption; shield wear follows blocked damage. All resistance events identify defender and damage channel explicitly.

Keep the existing power pillar1.3 and income pillar1.3/1.04. Remove the opening cliff caused by deriving ordinary monster attack from an unowned reference loadout: candidate ordinary stats use direct floor anchors and authored species multipliers. Initial anchors and any adjustment are recorded with measured actual-engine runs; they are not accepted as balanced by construction. Weapon acquisition/upgrades retain the authored level/grade/floor mapping. Character growth, defenses and weapon progression must be measured together, including grade boundaries and capped player level30.

Opening grants a modest blade/bow/staff kit exactly once to new characters so mandatory reach/counters never depend on a rare drop. Existing earned weapons remain owned. Forge upgrades validate location, owned ID, +20 cap, floor access, gold and both materials atomically. Repairs restore only paid condition. Starter recovery is affordable with zero carried gold and has a time/energy cost; no infinite free healing/repair loop during fights.

## Gathering slice

Add Drowned Copse and Bog-Iron Field on floor3, including named gate links. Each requires an owned tool outside the deck. A gather spends one energy and tool condition, persists target-resource yield and ambush roll, and may open the same group resolver. Explicit extraction banks the expedition haul once. Flee or death loses the entire unbanked expedition haul while retaining previously secured materials. Broken tool and zero energy always leave an extraction action. Tool prices, net yields and ambush costs are measured alongside hunting, with separate gold/XP and full recipe completion metrics.

## Verification and rollback

Tests exercise real core actions, not direct helper-only success paths: roster persistence; 5 enemies/2 energy; retreat after2; illegal IDs; switching; status/cooldown carry; partial shields; kill XP overflow; retry final kill; dawn; deck locks; wrong-location upgrades; exhausted victories; death/recovery; full old pack; gather ambush/extract/retry/loss. Add actual HTTP/local transactions for final settlement. The headless policy must clear complete groups before recording victory/readiness.

Keep the candidate enrollment flag off in production. Revert this phase's commits in reverse order only before candidate writes. After writes, stop new starts and retain readers/settlement for active group/expedition receipts; never overwrite earned ownership with an older document. Append exact commit IDs, run paths and browser evidence to the phase plan before advancement.
