# Shared rules, ownership and migration

Review companion to [plan 015](PLAN.md). Exact coefficients are candidates until verified in the actual engine. No executable implementation is introduced by this document.

## One game model and clear ownership

| Owner / current source | Responsibility in the redesign |
|---|---|
| `plugin-linear-ascent/plugin_linear_ascent/economy.py`, content schema/floors | Versioned weapon/family/grade definitions, source gates/recipes, monster axes/traits, group templates, costs and reward functions. |
| Plugin `engine/state.py`, `engine/core.py` | Item instances, fixed deck, XP reserve, save conversion, ownership checks, starter/School/Forge flow and group entry. |
| Plugin `engine/combat.py` | Sequential state transitions, per-enemy energy latch, exact weapon action, damage/status/movement/shield resolution, kill and final settlement intents. |
| Plugin `engine/scene.py`, `profile.py`, `render.py`, `pane.py`, tool entry points | One inspectable action/scene contract rendered and described consistently in web, Luna and headless play. |
| `worldd/app/game.py`, `social.py`, persistence/migrations | Atomic player actions and shared effects, idempotent ownership/reward/refund operations, shared warden time/HP, world unlock and era closure. |
| `worldd/app/webplay.py`, served site/wiki, `worldd/tools/gen_wiki.py` | Existing web action transport, game assets, and a generated wiki describing the same definitions. |
| `worldd/tools/vendor_game.sh`, plugin pointer | Distribute the exact plugin implementation; a build must not silently overwrite new engine code with an older submodule. |
| `simulation/game_adapter.py`, agents/planner/results/search | Same imported game choices and future shared service, isolated time/storage, software policies, measurements and parallel orchestration. No copied combat resolver. |

The newer wiki and engine baseline lives on published `origin/main` at `1897edd`; the current simulator branch starts from `65f3c1c` and an older vendored engine. Phase 1 integrates the published work in a clean checkout and records the chosen plugin/vendor hashes before editing rules. Historical reports retain their old hash. Preserve unrelated working-tree edits.

## State contracts

These are proposed fields/contracts, not existing API field names.

| Record | Required meaning |
|---|---|
| Weapon instance | Stable ID, owner/location, definition/family, grade, upgrade 0–20, remaining/max endurance, acquisition source, rules version, conversion provenance. Never identify a particular weapon solely by its slug. |
| Selected deck | Ordered three cells of instance IDs, optional empty cells, active selection and revision. Unique IDs; ownership, usability and location validated. |
| Persisted group offer | ID, owner, floor/route/mode, fixed enemy identities/order/specimens/arrival gaps, creation/rules revision, consumed state. Reads/deck edits cannot reroll it. |
| Active group | ID, offer ID, committed deck IDs, members, current member, resources/cooldowns, action revision, earned-XP receipts, pending haul, outcome/settlement receipt. |
| Enemy member | Stable ID, waiting/active/defeated state, HP, profile/traits, gap, statuses, reward basis, engagement receipt, kill receipt and once-only loot result. |
| Engagement receipt | Start action ID, energy before/after, charge 0 or 1, funded/exhausted latch, exhaustion rules revision. |
| Settlement receipt | Unique group outcome, credited kill IDs, final haul ownership, overflow claims, final survival result and provisional objective credits. |

All accepted mutations validate owner, encounter/rules revision and action ID. Local and HTTP backends must enforce the same invariants. A rejected/stale/illegal action spends no energy/ammo and does not begin a waiting enemy. A duplicate valid action returns its stored result, not a second transition.

### Encounter state machine

`persisted offer → first valid combat action → active member → kill → next member waiting → ... → final clear / successful retreat / death`

The first action commits the deck. Against each waiting member it also charges one energy if available; otherwise zero, recording exhaustion. The final available energy point funds that enemy normally. Attacks later in that same fight never charge entry again. Regeneration can fund a later member; it does not change the active enemy's recorded status. Merely showing the next enemy cannot charge or act.

Selecting a committed weapon accompanies a normal combat action, without an additional switch turn. A free inspect or selection preview does not tick status/cooldown clocks. Use explicit instance IDs: two poison swords with different condition cannot silently select whichever slug is found first. Out-of-deck weapons, newly dropped weapons, trade, pawn, gifts, Forge, level-up, sleep and town healing cannot change the committed equipment/resources in mid-group. Existing legal carried consumables still work at their normal combat cost.

Normal combat uses accepted-action time. Disconnecting does not advance enemy turns. Freeze/defer dawn, sleep and level-up recovery so reconnecting or crossing midnight cannot heal a group secretly. Ordinary time-based energy regeneration may continue and is checked at each engagement boundary; define and test that separately from combat HP/status time. Warden healing/status events use real server time, not private-group clicks.

### Rewards and edge cases

- Per resolved kill, credit base/rested XP exactly once and preserve overflow. Compute XP from that enemy's reward basis, not the zero gold currently credited to the purse. Normal level/learning costs and character cap 30 remain.
- Proposed reserve semantics: `gain_xp` fills the visible bar then the reserve; `spend_xp`/advancement refill from reserve without clipping; at level 30 merge into the existing uncapped XP currency. Spending cannot duplicate totals. No automatic mid-fight level/stat/HP gain.
- Roll each enemy's materials and categorical weapon result once at its death. Store them pending. Completion transfers the existing pending result; it never rerolls.
- Full clear requires every member defeated **and the player alive after that action's complete resolution**. A final mutual death keeps earned kill XP and loses the haul. The event order, including poison deaths, must be pinned in tests.
- A failed escape keeps combat active. Successful escape, rescue extraction or death forfeits the pending haul. Revive-in-place retains it and the same group-level rescue limit.
- Previously owned gold/materials/items are distinct from pending rewards. Apply the published death policy once; never count unclaimed haul as purse loss. Proposed persistent weapon levels and protected secured materials need an economy/migration test.
- Lifetime kills may update per kill. Gold/item-bearing contracts, weekly rewards, assist/alpha payouts and similar side paths remain provisional until group completion; their APIs cannot bypass the haul rule.
- Full-pack victory creates persistent secured claims. Resolve claims before another hunt; no silent deletion and no unlimited storage by abandoning claim screens.
- A consumed offer is retired even on failure; repeated kills require another real encounter with its actual time/resources. Free refresh of an unstarted offer is forbidden, but selecting a genuinely different route is a valid strategic choice.

## Combat definitions to retain and test

Affinity describes defense; outgoing monster damage channel is a separate field. “Common monster” is not the same field as Common item grade. Retain authored species/stat differences and at most three visually similar variants per animal on neighboring suitable floors.

| Target | Blade / Power | Bow / Power | Magic, including arcane arrows |
|---|---:|---:|---:|
| Ground Common | 1.25× | 1.25× | 1.25× |
| Ground Power | 0.45× | 0.45× | 1.50× |
| Ground Magic | 1.50× | 1.50× | 0.45× |
| Air Common | Unreachable | 1.25× | 0.90× |
| Air Power, Spell dispersal | Unreachable | 1.25× | 0.35× |
| Air Magic | Unreachable | 1.50× | 0.30× |

This is the existing **proposed** matrix, with the Air Power exception explicitly visible. Air also pursues faster. Apply movement/reach, defensive affinity and trait factors once, rather than multiplying both this matrix and the old mutually exclusive `TYPE_MULT`. Use the damage/effect specification in [combat research](../../research/combat-atlas/PLAN.md) as the first candidate; Magic's proposed flat-defense step is a real change from its old bypass and must be measured.

| Weapon path | Families retained; all four grades each |
|---|---|
| Blade | Breach Cleaver (impact), Viper Edge (poison), Ramguard Sword (push), Thunder Maul (stun), Briar Saber (bleed), Sundering Falchion (Expose). |
| Bow | Hawkeye Longbow (range), Skirmisher Bow (contact), Recoil Recurve (push), Pinning Bow (slow), Runestring Bow (arcane payload). |
| Staff | Ember (burn), Frostbind (slow), Stormbell (stun), Repulsor (push), Hexglass (Expose). |

All bows may use ordinary, arcane, poison, fire, pinning and concussive arrows. Arcane changes the direct channel; fire's impact is Power and later burn is Magic. Grade-scaled payloads have actual inventory/cost/consumption; an invalid shot consumes nothing, an accepted missed shot consumes its arrow. Ammo versatility can legitimately replace a staff, but compare its price and contact performance.

| System | Initial candidate / required invariant |
|---|---|
| Poison / burn / bleed | Respectively three / two / two enemy phases; snapshot source attack, not enemy max HP. New effects first tick next phase, never twice on apply. Trait immunity is visible. |
| Stun / slow / Expose | Skip one action with subsequent shared resistance; slow affects speed; Expose weakens flat DEF without erasing affinity. Preserve effect-specific timing and no permanent control cycles. |
| Knockback / gap | Four gaps 0–3; push +2 capped at Cover and prevents that phase's pursuit; next action may exploit it. Arrival rules do not grant a free opener after every kill. |
| Cooldowns | Count accepted combat actions, persist through switches and member deaths; reads and previews do not tick them. Enemy effects die with that enemy; player/weapon timers persist. |
| Shields | A landed incoming hit always leaks at least 25% through combined armor/shield absorption in the first candidate. Shield wall increases absorption; never complete protection. Shield wear is only its absorbed share; broken shield provides no shield DEF. |
| Exhaustion | Candidate 0.5× outgoing damage and −2 effective speed, minimum 1, latched per enemy. Apply once to direct and new DoT damage before final rounding; never halve at both application and tick. Keep normal XP. |
| Minimum damage / immunity | Round at the specified stage, with small-number fixtures. Immunity/reach cannot become minimum-one damage. A minimum-one floor must not make exhausted frontier fighting effectively unchanged. |

A direct action resolves validation/start → direct hit → landed-hit effects → pre-existing DoTs → surviving enemy action/pursuit → expiry/outcome. Pin death order and whether a killed enemy can act; do not carry a dead member's intent to the next member. Boss status clocks are separate timestamped service rules, independent of the number of attackers.

## Sources, materials and upgrades

Use per-family acquisition settings from wiki revision `089.3` as candidates, not hardcoded rarity-wide logic. All 64 records need explicit gates, delivered condition, cost and art.

| Grade | Materials A / B | Craft: gate, level, condition | Shop: gate, level, condition | Monster: level, condition |
|---|---|---|---|---|
| Common | Wood / Raw Metal | 1, +0, 100% | 1, +0, 100% | +0, 40% |
| Rare | Hardwood / Steel | 26, +0, 100% | 28, +2, 100% | +0, 30% |
| Epic | Meteorite / Starforged Steel | 51, +0, 100% | 57, +4, 100% | +0, 20% |
| Legendary | Mythic Threads / Shard Matter | 76, +0, 100% | 84, +6, 100% | +0, 10% |

Rare/Epic discoveries remain possible very early at tiny rates; Legendary discovery starts at 50 in the existing proposal. Equip gates remain separate from finding an item: 1/26/51/76. A +6 Legendary purchase is not offered at 76 with floor-84 power. Revisit these gates explicitly if testing shows an acquisition cliff; do not silently inflate power. Existing neutral reference tables have hold floors and durability-only levels; describe the actual benefit honestly.

Forge upgrade: validate owner/location/deck lock/rules revision/+level/gates and one quote; deduct gold and both materials atomically, advance one level once. Preserve remaining condition fraction as max endurance increases; a broken item stays broken. New upgrades replace weapon honing, never stack with it. Repair/crafting/bought-condition/resale remain separately priced operations, with no currency or durability arbitrage.

Each killed monster has four independent material-grade rolls and one categorical weapon-grade roll including “no weapon.” Keep floor, species/body/bite, specimen, deep mode and family-weight differences. A group may contain several item drops. Wiki shows per-enemy percentages and `1 − product(1 − p_i)` for at least one grade drop, conditional on full completion and independent rolls. Once pity/correlated rolls exist, derive the actual conditional distribution rather than using that shortcut blindly. Secured odds per attempted hunt also require measured survival.

A required new grade must be reachable with the preceding grade while collecting both native materials. Recipes cannot require defeating a monster that only the newly crafted weapon can beat. Optional dry-streak protection is not enabled by default in this plan; if adopted, version it, publish it, and settle its progress/guarantee atomically with the haul.

## Shared wardens

The initial catalog adds no boss-healing suppression, percent-max-HP damage or new passive energy regeneration. Adding any of these later would require rechecking the cooperative ceiling explicitly.

Replace `_fx_boss_commit` / power-sum victory with individual validated damage events applied promptly to one shared HP pool, including every tenth floor and 100:

`healed = min(max_hp, hp + heal_per_second × max(0, server_time − last_time))`

`next_hp = max(0, healed − accepted_damage)`

Serialize regen, damage, energy/cadence and death settlement; compute damage from authoritative player/encounter state, never a client-supplied total. Every hit has a deduplication ID. No private exchange may bank its damage and publish it minutes later as one concurrent strike. Reads can project healing without a database write every frame. Use integer/fixed-point HP/regen with retained fractional remainder; large floor-100 values must round-trip through JSON/browser without unsafe-number corruption. Pin shared status event ordering and once-only ticks.

The one-energy-per-enemy rule applies to ordinary/deep groups. **Warden energy is a separate review decision.** Measure the existing three-per-swing behavior and energy cap; choose a documented cadence/cost/burst window before sizing HP/regen. Do not accidentally make one energy buy unlimited boss attacks or reuse an energy-refilled formula. Around floor 10, prepared frontier players should need cooperation; late floors need large concurrent groups. Fix reference HP/regen per warden generation, not from whichever deck happens to join.

Real-time DoTs, stun resistance and Expose are shared; push changes only the acting player's local gap. More clients cannot accelerate a poison timer, extra tabs cannot buy extra attacks, and a disconnected attacker cannot block other players. Participant eligibility and reward share derive from accepted contributions with a documented retention rule; contribution history is accounting, never banked future damage. Final death atomically issues rewards, unlocks the next floor and closes the era once on 100. Test overlapping attacks, late hits and two possible killing blows.

## Migration and rollback contracts

| Existing state | Required conversion / preservation |
|---|---|
| One, two or three held slots | Three available cells, retaining existing order/active weapon where possible. Preserve training and unrelated pack progression. |
| Old duplicated slugs, honing, style, oils and wear | Create distinct IDs and retain provenance; map equivalent power/investment. If an item cannot yet map fairly, preserve it via a functional compatibility path that is included in balance/solo-boss checks. |
| Paid School slots | Reconcile `train` receipts such as `carry 2` / `carry 3`; refund recorded gold/XP once. Missing historical costs need a capped, published compensation policy decided from the audit, not today's frontier price. Preserve refunded XP overflow. |
| Active old hunt | Finish with its old pinned rules. Do not append surprise enemies or reverse earned loot. Next entry adopts groups. |
| New active group | Same committed IDs, rewards, exhaustion and action receipts after save/restart. Legacy clients cannot mutate it through slug-only actions. |
| Trade, pawn, storage, faction assets, gifts | Preserve owner/location and pending transaction semantics; no duplication or bypass of an active deck lock. |
| PvP / labs / rescue / assist | Audit all old item/hit/reward consumers. Keep established PvP behavior via explicit compatibility rules until separately tuned; do not silently apply monster-only stuns/immunities to players. |
| Active warden wounds and old pledges | Separate world migration boundary. Preserve/remap wounds explicitly, refund unconsumed pledges once and archive historical records. Never reset shared HP unnoticed mid-battle. |
| Existing currency / XP / materials | Append-only receipts and reconciled totals; never infer or overwrite newly earned progress from a stale snapshot. |

Migration tooling is future work. It must support a read-only preview, stable idempotent apply, reconciliation report and compensating operations, on both local and HTTP-backed player states. Before release, the runbook must contain the exact implemented commands, receipt selectors, pinned revisions and tested inverse operations; placeholder commands are not deploy instructions.

Before new-format writes, code reversion may suffice. Afterwards, stop new entries, keep compatibility readers and settle/drain active groups, then apply verified compensations. Never roll the whole database/player document back to its pre-migration snapshot. Keep original fields/archives until reconciliation and production verification prove they are safe to retire in a separately planned change.
