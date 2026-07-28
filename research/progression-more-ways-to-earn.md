# More ways to progress — research

Question: *"I feel stuck. I can do two things — grind my energy and get
interest in the vault. What other way is there to get more gold / XP to
advance and kill the boss?"* Plus: what does World of Warcraft do about
this, and what transfers?

Date: 2026-07-28. Sources: the shipped code (numbers below are from
`economy.py` and the engine, not from `vision/economy.md`, which is
stale in places), and current WoW guides for the Midnight season.

---

## 1 · The diagnosis: it is one loop, not two

Energy regenerates **1 per 45 real minutes** (`economy.py:15`), about
**32 a day**, and a wilds hunt costs exactly **1** (`economy.py:18`).
So the day is capped at roughly **30 fights**. Each fight pays:

    gold_per_kill(F) = round(8 × F × 1.2^(tier-1))     economy.py:285
    xp_per_kill(F)   = 4 × F  (±25% jitter)            economy.py:280

Everything else is passive, incidental, or small:

| Route | What it pays | Ref |
|---|---|---|
| Bank interest | 5%/day compound, credited on Vault visit | `economy.py:1045`, `state.py:385` |
| Pawn shop | 25–55% of item value, rate reseeded daily | `economy.py:720` |
| Present (away ≥20h) | 50 × level gold, 40% of the roll table | `economy.py:1055`, `core.py:238` |
| Solo warden | 80 × F gold, 25 × F XP | `economy.py:393-398` |
| PvP win | victim's *carried* gold, capped 2 attacks/day | `worldd/app/social.py:521` |
| Faction weekly | hoard prize split by attendance | `worldd/app/factions.py:337` |

**So daily progress is very nearly a constant.** At level 20 on floor
20: `xp_need(20) = 60 × 20^1.5 = 5,367` (`economy.py:300`) and a kill
pays 80 XP, so a level is **67 kills — over two full days of perfect
energy usage**. Nothing compounds except the bank, and no decision made
today beats yesterday. That is a structural problem, not a content
shortage: a single faucet behind a hard rate limit, so the only
strategy left is patience.

The **fade rule** already closes the obvious escape — income on floors
more than 5 below the frontier decays to a floor of 0.25
(`economy.py:318-325`). So "farm easier floors faster" is deliberately
dead, which means the fix has to be new *kinds* of income.

### There is no quest system at all

Searched hard for quest / bounty / contract / task / daily / weekly /
job / errand / commission across the engine and every content YAML.
**Nothing exists as a mechanic.** What turns up is only:

- **PvP XP bounty** — 5% of the victim's level need (`economy.py:1048`)
- **Faction weekly challenge** — collective hoard/cull/climb, not
  personal (`worldd/app/factions.py:40`)
- **Morning Crier / happenings** — a news feed, not objectives
- The word "bounty" as **flavour prose** in floor YAML (e.g.
  `floor_020.yaml`), wired to nothing
- `BOARD_PRICE = 10` — a town notice board price, **defined and never
  used** (`economy.py:1070`). `vision/economy.md:128` describes a ◈25
  board post; it was deferred back in
  `plans/004-difficulty-review/summary.md` and never built.

---

## 2 · What WoW actually does

WoW's answer to this exact problem is **not** more grind and **not** a
bigger energy bar. It is *many loops on different clocks, each with its
own cap, plus a guaranteed weekly payoff the player chooses.*

**World quests and dailies.** Small, varied, refreshing objectives that
pay a bonus for kills you were already making. They do not add
playtime; they add direction and a multiplier to the playtime you have.
The daily/weekly count is the cap, so they never become infinite grind.

**The Great Vault** — the retention spine, and the most transferable
idea here. During the week you hit thresholds across **three separate
activity tracks**: raid bosses at 2/4/6, Mythic+ dungeons at 1/4/8,
delves/world at 2/4/8. Each threshold unlocks a slot, up to nine. At
reset you pick **exactly one** reward from the slots you unlocked. Two
things make it work: it rewards **breadth rather than repetition**, and
it converts a random week into a **guaranteed payoff with agency** —
you choose, so a bad RNG week still moves you forward. Guides
explicitly advise "nothing good? take the socket" — the floor is never
nothing.

**Rested XP.** Accrues while logged out in an inn and gives a **200%
bonus** on mob kills (it does not apply to quest rewards). This is the
mechanic that makes being offline feel like *accrual* rather than loss.

**Gathering professions.** WoW's most reliable raw gold is Herbalism
and Mining — a **non-combat loop where time converts to gold without
touching the combat rate limit at all**. Crafting and auction-house
arbitrage sit on top: daily profession cooldowns, consumables timed to
raid nights, crafting orders.

**Currency caps that force breadth.** Crests are capped at 100 per type
per week, so you cannot solve gearing by repeating one activity — the
cap pushes you sideways into another loop.

Sources: `gbhbl.com/world-of-warcraft-midnight-season-1-routines`,
`guildorder.com/games/wow/guides/weekly-reset-triage`,
`wowutils.com/loot/great-vault-explained`,
`lfcarry.com/guides/wow-gold-guide`.

---

## 3 · The three routes worth building, in order

The binding constraint is energy, and the pacing vision is explicit
that **the wait is the game** (`vision/ideas.md` §3: "No paid
skip-the-wait, at least initially: the wait *is* the game"). So new
routes must **pay more per energy spent**, or **pay no energy at all** —
never simply hand out more energy.

### 1 · A contract board  ← start here

Three contracts posted daily in town. "Bring down four ash-salamanders
on floor 3." "Six kills with arrows." "Strike the Warden once." Gold
and XP on completion.

Why this one first:

- It pays for kills the player was making anyway, so it **multiplies
  the value of the existing 30 fights** rather than asking for a 31st.
  It is the only one of the three that does this.
- It is the **biggest hole in the game** — no quest system of any kind
  exists.
- The hooks are already there: unused `BOARD_PRICE`, bounty prose in
  the floor YAML, a `vision/economy.md` notice board that was specced
  and dropped.
- The daily count is a natural cap, so it satisfies "no infinite
  grind".
- It answers the actual complaint — "I can only grind" — by giving the
  grind **direction**.

### 2 · A weekly strongbox at the Vault

The Vault is currently only a savings account. Give it the Great Vault
treatment: count **three things the game already tracks** — kills,
floors climbed, warden strikes — at 2/4/6 thresholds, then let the
player **pick one** reward from what they unlocked: a gold lump, an
aether lump, a gear-tier token, a relic.

- Costs **zero energy**.
- Rewards varied play instead of only hunting.
- Gives every week a guaranteed payoff with agency.
- The faction system already speaks `hoard` / `cull` / `climb`
  (`worldd/app/factions.py:40`), so reuse that vocabulary — collective
  prize for the faction, personal choice for the strongbox. Keep them
  distinct so it is not a duplicate of the weekly challenge.

### 3 · Rested aether at the Lodge

Time spent away banks a pool that doubles XP per kill until spent.

- Serves a goal the design docs already state:
  `vision/ideas.md` — "a break never punishes below baseline — we want
  forced breaks to feel fine." Rested XP makes breaks feel *good*.
- Turns the Lodge from a purely defensive purchase (◈10 × level for
  offline PvP protection and +20 HP at dawn, `economy.py:1046`,
  `core.py:1149`) into a progression purchase.

**Honest tension:** you pay gold for a Lodge night, so a naive version
is an indirect **gold → XP faucet**, which `vision/research.md` §6 and
plan 006 explicitly forbid. The fix: accrue rested aether from **time
away**, not from the payment, and cap it hard so it smooths pacing
rather than acting as a faucet.

### Also considered

- **Gathering / crafting / salvage** — the WoW non-combat gold loop.
  Best local fit is salvage: disenchant gear you would otherwise pawn
  into materials that discount honing. Turns dead inventory into
  progression. `vision/ideas.md` has nothing here; greenfield.
- **Offline hireling jobs** — WoW's mission table. Send someone on a
  timed job for gold while away. Already named as deferred in
  `plans/003-execution/phase-1/summary.md` ("agent carried-loot slot,
  offline jobs").
- **Per-fight quality bonuses** — streaks, first-kill-of-the-day,
  clean-kill (no damage taken). Since energy is the binding
  constraint, rewarding *better* play per fight is high leverage.
- **Player-built structures** (watchtowers, traps, shrines) —
  `vision/ideas.md` §2 and `vision/world.md` promise these; deferred
  since `plans/003-execution/phase-5`.
- **Prestige reset** after Vharuk on floor 100 — `vision/economy.md`
  §5 mentions it; plan 006 says explicitly "not in scope".

---

## 4 · Two quick wins (already-paid-for rewards that do nothing)

- **`repair_token`** is awarded by presents (`core.py:251-252`) and has
  **no spend path anywhere**. Plan 019 already flags it as dead code.
- **`rumor_day`** is set by the present roll and **never read** in
  combat.

---

## 5 · One correction: gold will not get you the boss

For milestone floors (10, 20, … 100) more gold is the wrong lever. A
milestone warden needs a **quorum of pledges** within the last two
world days, and the fight resolves on:

    party_power × swing ≥ boss_power × 0.75
    power ≈ 2×ATK + DEF + HP/4        worldd/app/social.py:726-743

Floor 20's Warlord Skarn (120/100/1,800) needs **quorum 3**; floor 100's
Vharuk needs **12** (`economy.py:430-441`). A loss refunds the 5⚡
pledge.

So that wall is **other players plus party gear**, not the bank
balance. If beating the boss is what feels blocked, the levers are
recruiting and gear tier — which is a direct argument for making the
contract board and the strongbox pay in **gear-tier tokens**, not only
coin.

---

## 6 · Constraints any new route must respect

From the vision docs and shipped plans:

| Constraint | Source |
|---|---|
| No gold → XP faucet | `vision/research.md` §6, plan 006 |
| No paid energy refills (v1) | `vision/economy.md` §1 |
| Death never takes XP or levels | `vision/economy.md` §7, plan 006 |
| No infinite same-floor grind | fade rule, `economy.py:318` |
| Gold alone cannot skip veteran gates | level ≥ 10·(T−1)+1 for gear tier; floor ≥ F−10 |
| Consumables are progression tools, not farming tools | plan 017 |
| Stacked drains ≤ 40% of daily income | `vision/economy.md` §9 |
| Faction armory stays economically neutral | `vision/economy.md` §9 |
| The wait is the game | `vision/ideas.md` §3 |

Pacing target, for calibration — `vision/economy.md` §3: "~3,300
at-level fights ≈ 165 days … cut to ~4–5 months by boss XP, quests, and
presents. **The climb is a season, not a weekend.**" Note that line
already assumes **quests exist**. They do not.

---

## 7 · Where the raw audits live

Two exploration passes produced the numbers above:

- Full map of energy / gold / XP faucets and sinks, the boss systems,
  the world-day tick, and every Roothollow building.
- Audit of every written plan (001–020, worldd 001–002), the faction
  system, what worldd shares between players, and the vision docs'
  stated intent and rejections.

Everything they found that matters is reproduced in this file.

---

# Part two — reacting to Roy's proposals

Roy's response to the above: (1) likes rested XP, (2) wants professions
in the style of *Jones in the Fast Lane* — study overnight to unlock a
job, jobs have levels, each rank earns more gold while offline, and each
might give its own quests, (3) clarified that the boss question was
about **level 1** and the ordinary solo warden, where gold buys an
energy fill and a better weapon.

## 8 · Three facts, checked in the code

**Gold buys energy — capped at once a day.** The **Energy cell**:
◈200 for **+5⚡**, `max 1/day`, sold at the Apothecary & Medlab
(`economy.py:879`). Applied at `core.py:1134-1137` via
`state.gain_energy(p, 5)`, with the once-a-day lock held in
`p["daily"]["energy_cell"]` (`state.py:56,381`) and refused with "One
cell a day. Your heart is not a reactor." (`core.py:1125`). Roy's model
was right and an earlier draft of this document was wrong — see §8b for
why that error matters more than it looks.

The other gold→meter purchases are HP, not energy: hunter's stew ◈2 for
+5 HP (`economy.py:1038-1039`), the healer's tent, the Lodge's dawn +20.
Free energy comes only from the away-present (`core.py:246`, which grants
99 — i.e. a full refill).

**Gold co-gates levels — a full XP bar is required as well.**
`economy.py:305-315`: "Levels are bought, never granted: a full XP bar
is the license to train, the gold fee is the price." `levelup_gold =
max(200, daily_income(level)/10 × 10)`.

**Soloing the warden at low floors is the intended design, not a
loophole.** `economy.py:328-332`: wardens are derived from the at-level
player model "so 'soloable at-level' holds by construction: win 65–85%
through floor 30, then HP/ATK ramps fade solo odds smoothly toward
'bring friends' (<10% well before floor 50)." Roy found the right lever
unprompted; §5 above answered the milestone-quorum question he wasn't
asking.

The energy cap is `24 + level//10` (`economy.py:16,25`) against 45-min
regen. **Past ~18 hours away, regen overflows and is silently lost.**
That fact matters in §9.

Energy costs, for the arithmetic below: a wilds fight is **1⚡**, a
warden attempt **3⚡**, a milestone boss commit **5⚡**, a PvP attack
**3⚡** (`economy.py:18-21`).

## 8b · What the Energy cell means: capped conversion is the house rule

The cell prices energy at **◈200 / 5 = 40 gold per ⚡**. Against
`gold_per_kill = 8 × F × 1.2^(tier-1)`, at tier 1 that break-even sits
at **floor 5**. So:

| Where you are | A cell's 5⚡ returns | Verdict |
|---|---|---|
| Floor 1–2, tier 1 | ~40–80 gold on ◈200 | **heavy loss** |
| Floor 5, tier 1 | ~200 gold on ◈200 | break-even, plus free XP |
| Floor 10, tier 2 | ~480 gold on ◈200 | strongly positive |
| Floor 20, tier 3 | ~1,150 gold on ◈200 | free money |

Two consequences worth naming.

**One: the forbidden gold → XP faucet exists, and the daily cap is what
makes it acceptable.** Above roughly floor 5 the cell converts gold into
energy into XP at a profit, which is precisely the conversion
`vision/research.md` §6 and plan 006 forbid. It is fine anyway *because
it is capped at 5⚡ a day* — at floor 20 that is ~400 XP against an
`xp_need(20)` of 5,367, so about 7% of a level per day, bounded and
knowable.

That is the important precedent for everything in §10 and §11: **this
game's answer to "may gold become progress?" is not "never", it is "yes,
with a hard daily ceiling."** An offline-earning profession therefore
does not need the conversion closed; it needs a ceiling, like the cell
has. Design new routes to the cell's pattern, not to a purity rule.

**Two: the cell's real job is converting a stock into a flow, and it is
sized for exactly that.** `COST_BOSS_COMMIT = 5` and the cell grants
`+5⚡` — **one cell is precisely one milestone boss commit** (or 1⅔
warden attempts at 3⚡). That is unlikely to be coincidence. The item
exists so that savings can buy *tempo* at a moment of blockage: you are
three energy short of the warden, you do not want to wait two hours, so
◈200 converts accumulated wealth into acting now. Roy's read of the
design intent is almost certainly the correct one.

An earlier draft of this section called it "a tax, not a decision" above
floor 5. That is too strong. It is a genuine decision whenever gold has
live competition — a gear-tier jump, a ◈600 trollblood tonic, the
`levelup_gold` fee, healing after a bad run — or when you will not be
back today to spend the 5⚡, or below floor 5 where it simply loses
money. It drifts toward automatic **only** once income comfortably
exceeds every sink. So the "daily chore" risk is a symptom of **gold
abundance in the mid-game**, not a fault in the cell.

**Three: the cell is very nearly the only pipe from stock to flow, and
that is why gold feels dead.** This is the same complaint the document
opens with — vault interest and pawn income accumulate and then have
nowhere meaningful to go. Everything else gold buys is a *stat* (gear,
honing, healing); the cell is the one place gold buys *more game*. And
that pipe is 5⚡ wide, once a day. The mechanism is right; being the only
one and being narrow is the problem.

One option that follows directly from Roy's framing: replace the hard
1/day lock with an **escalating same-day price** — second cell at 3×,
third at 9×. Nobody farms energy at ◈600 per 5⚡, so the ceiling holds
economically rather than by rule, while wealth can still buy the one
extra attempt in exactly the "I need to beat this boss before I upgrade"
moment. It also converts a daily chore with a right answer into a real
decision at every step. Caution: this leans on
`vision/ideas.md` §3 ("the wait *is* the game"), so the escalation has
to be steep enough to stay an emergency valve rather than a bypass.

**Three, for the level-1 question specifically: the cell is the worst
deal it will ever be at level 1.** ◈200 at floor 1 is ~25 kills of
income to buy back 5 kills of energy. The lever at level 1 is the
**weapon**, and then the **warden**: at 3⚡ for `80 × F` gold and
`25 × F` XP, a warden attempt pays **~27F gold and ~8F XP per energy**
versus **8F and 4F** for an ordinary kill — roughly 3× the gold and 2×
the XP per point spent. Cell-funded warden attempts turn gold-positive
from about **floor 2**. So the correct level-1 plan is *weapon first,
warden as the engine, cell only once the floor number justifies it.*

## 9 · Rested aether: yes, but not at 200%

The mechanic fits, and it fits for a reason worth naming: the energy cap
currently *punishes* long absences via overflow. Rested XP inverts the
same absence into banked value, so it fixes an existing wart rather than
bolting on a new subsystem. One number, one accrual clock, no new UI
beyond a line at the Lodge.

The caution is the multiplier. XP is deliberately the scarcest resource
in the game and 012 enforced that everywhere: `warden_xp = 25×F` sits
below `warden_gold = 80×F`, and milestone XP is fixed at 0.3 × gold
(`economy.py:429`). WoW can afford +200% because levelling there is a
transient phase before the real game. Here the climb **is** the game —
"a season, not a weekend", ~165 days. A 200% XP bonus on the scarce
resource compresses exactly the thing the pacing is built around.

So: keep the mechanic, shrink the number, and cap the pool hard (a few
days' worth, not unbounded). Also copy WoW's exclusion — rested applies
to **kills only**, never to contract or strongbox payouts, or a rested
week double-dips through every new route at once.

## 10 · Professions: right instinct, wrong shape, and one fix

### The mismatch with Jones

In *Jones in the Fast Lane*, time is the scarce resource: an hour at
university is an hour not earning, so studying **competes** with living.
That tension is the game. In Linear Ascent, offline time is free — you
are logged off anyway, so "study overnight" costs nothing you feel. A
cost you do not feel is not a cost, so the whole tree unlocks itself on
a calendar and no decision is ever made. The idea imports Jones's
*content* but drops Jones's *constraint*.

### The fix: one night, one action

Make the night a single slot with three uses:

- **Rest** — bank rested aether (XP later)
- **Study** — progress a profession rank
- **Work** — gold now

This is the best idea available here, because it does five things at
once:

1. Roy's ideas 1 and 2 stop being two systems and become **one**.
2. Studying regains a real price — a night studying is a night not
   resting and not earning. Jones's tension, restored exactly.
3. It is **self-capping** by construction: one night, one action. No
   infinite grind, no rate to tune.
4. It gives the Lodge a reason to exist beyond defence (today it is
   ◈10 × level for offline PvP protection and +20 HP at dawn).
5. It puts a **real decision in every day** — which is the actual
   complaint. Today's play is identical to yesterday's; this makes
   today's *absence* a choice.

### The real risk of offline gold, given the cell exists

Offline income bypasses the energy cap, which is both the appeal and the
risk. An earlier draft argued it was structurally safe because gold
could not become energy — that was wrong (§8). Gold *does* become energy
and therefore XP, so profession gold does feed progression directly.

The honest position is the one §8b draws out: that conversion is
tolerated because it is **capped**, and a profession must inherit the
same discipline. Two concrete implications:

- **Do not let profession income raise the cell ceiling.** One cell a
  day stays one cell a day, however rich the player gets. Offline gold
  should make the daily cell *easy to afford*, never *repeatable*. The
  ceiling is the whole safety mechanism.
- **Gear inflation is the second-order risk.** Enough offline coin and
  you sit in top-tier-for-your-band permanently, flattening the floor
  curve. Mitigation: pay professions mostly in **materials and access**
  — forge discounts, potion inputs, contract unlocks — rather than raw
  coin. That is what WoW's gathering does: you get herbs, and the gold
  only appears if you choose to sell.

There is also an upside now visible. Because the cell already exists at
◈200/day and is *strictly correct to buy above floor 5* (§8b), a
profession that reliably nets a few hundred gold a night has an obvious,
already-built sink to point at. It makes an existing daily tax painless
instead of introducing a brand-new faucet with nowhere to go.

### Where it is genuinely too complex

Not the concept — the version described. Three professions × a rank tree
each × per-profession quest lines is **three unbuilt systems stacked**,
plausibly larger than combat. And "each sends you on different quests"
presupposes a quest system that **does not exist at all** (§1). Also
worth noting the job sites need no new locations: the Forge, the Lodge,
and the Guildhall are all already in the town square
(`core.py:517-533`), alongside the Arcanum, Medlab, Vault, Pawn, Stone,
Relay, and fields.

Cut to: **one night slot, one profession, three ranks, gold + materials,
no profession quests in v1.** Add professions two and three only after
the first one proves people choose "work" over "rest".

## 11 · Revised build order

1. **Contract board.** Unchanged as first. It is the only route that
   multiplies the 30 fights you already get, and it is the quest
   substrate that profession quests would later ride on.
2. **The night slot** — rest / study / work, with one profession at
   three ranks. This is Roy's ideas 1 and 2 fused, and it is smaller
   than either sounded separately.
3. **Weekly strongbox** at the Vault, paying gear-tier tokens.

The level-1 experience needs none of the above, though: at floor 1–5 the
answer is already *buy a weapon at the Forge, then run wardens at 3⚡ for
~3× the gold and 2× the XP per energy of an ordinary kill.* The Energy
cell is part of that plan too — just not yet at floor 1, where ◈200 buys
back only ~40 gold of hunting (§8b). If none of that feels available at
level 1, the bug is discoverability, not economy.

## 12 · WoW after the level cap: the two-ladder trick

Roy asked: you hit level 80 and that's it — what is the game afterwards?

First, the cap is **90** now; Midnight raised it from 80. But the real
answer is that **hitting the cap does not end progression, it swaps
which bar you are watching.** Character level is only the first ladder,
and it is deliberately the short one.

### Two ladders, doing two different jobs

The clearest framing of this comes from a gamification analysis of the
system (`yukaichou.com/gamification-analysis/wow-endgame-item-level-progression`),
and it is worth stating precisely:

| | Ladder 1 — character level | Ladder 2 — item level |
|---|---|---|
| Range | 1 → 90, then stops | ~220 → 282 this season, then higher next patch |
| Speed | fast | slow, asymptotic |
| Bounded? | yes | **no ceiling, ever** |
| Visible to others? | barely | yes — it gates groups |
| Job it does | **commitment** | **retention** |

Item level is the average power of your equipped gear, and it begins
exactly where the level cap ends. The argument for splitting them: a
bounded, fast, satisfying bar is what gets a new player invested, and an
unbounded, slow, public one is what keeps an invested player for years.
**One bar cannot do both jobs** — unbounded from the start feels
endless, bounded runs out.

### What actually fills the endgame

*Gear tracks.* Five of them — Adventurer, Veteran, Champion, Hero, Myth
— each item upgradeable within its track by spending Dawncrests. So
every drop has two axes: which track it came from, and how far you have
pushed it.

*Content that gates itself on the ladder it feeds.* Heroic dungeons want
ilvl 220, Mythic 0 wants 225, Mythic+ opens at 235, Normal raid 240,
Heroic raid 255, Mythic raid ~275+. Gear unlocks content, content drops
better gear. **The loop is circular and self-gating** — that is the
whole engine.

*The Great Vault as the weekly anchor.* Guides put it bluntly: miss a
Vault reset and you miss 8–15% of a week's progression; everything else
supplements it rather than replacing it.

*Seasons.* Every season introduces a new tier and effectively restarts
the ladder. The treadmill is **intentionally reset** rather than
extended forever.

*Horizontal progression for when the ladder stalls.* Renown tracks,
professions, player housing (new in Midnight), collections, PvP rating,
and alts via Adventure Mode.

### The finding that matters most for us: WoW's pacing is many lockouts

Look at how the endgame is rate-limited. One Prey Hunt **per difficulty,
per zone, per week**. Raid loot **once per boss per week**. Mythic
dungeons **once per boss per day**. Great Vault **once per reset**.
Delves on their own tiers. Crafting Sparks on their own cooldown.

**WoW's equivalent of our energy bar is the lockout — but it has a dozen
of them, on independent clocks.** Linear Ascent has exactly one clock:
energy at 1 per 45 minutes, shared by every activity in the game. That
is the sharpest available statement of the structural problem in §1.
Because the pool is shared, every activity **competes** with every other
one, so there is only ever one decision — spend or save — and no
activity can have its own rhythm. Independent lockouts are what let WoW
put a dozen different loops in front of you without any of them
cannibalising the others.

This reframes the §3 / §11 proposals: the contract board, the strongbox,
and the night slot are valuable **specifically because each carries its
own clock** (daily, weekly, nightly) rather than drawing on energy.
That, not the extra gold, is the actual mechanism.

### And what it says about our ladders

Terminology, because an earlier draft of this section muddled it: **the
100 "levels" of the tower are floors — worlds — and the player's level is
a separate number.** They are genuinely two systems. What ties them
together is the tuning reference: `_at_level_loadout` (`economy.py:352`)
defines the design's at-level player as **"level = floor**, current tier
set, honing 2 floors behind. The reference all tuning points at." So they
are two variables that the whole game assumes advance 1:1.

That is the real problem. Two ladders locked to each other are one
ladder wearing two hats, and both of them end at 100. Prestige reset is
out of scope (`vision/economy.md` §5, plan 006), so that is a **cliff** —
exactly the shape WoW spent twenty years engineering around. §13 is
about unlocking them from each other.

## 13 · The player-level system, and capping it (Roy's proposal)

Roy: *"we never really addressed fully our player leveling system —
cap player levels, make them easier, then progress with better gear."*

That is precisely WoW's Ladder 1 / Ladder 2 split, and it is the right
instinct. But the current stat model is arranged the **opposite** way
round, so this is an inversion of the power curve rather than a tweak.
Here is exactly what stands in the way.

### What player level does today

**There is no level cap.** Searched the whole plugin for
`MAX_LEVEL` / `LEVEL_CAP` / `max_level` — nothing. Player level is
unbounded and every stat is linear in it:

| Stat | Formula | Ref |
|---|---|---|
| ATK | `3 × level + weapon_bonus` | `economy.py:68` |
| DEF | `2 × level + shield + armor` | `economy.py:72` |
| Max HP | `40 + 12 × level` | `economy.py:80` |
| Energy cap | `24 + level // 10` | `economy.py:24` |

Level also gates content: the Arcanum at 6, the Relay at 3, the fields
(PvP) at 5 (`economy.py:763-769`), beginner protection through 5 and
death mercy through 3 (`economy.py:1049-1050`), grants from 5.

### Level is already ~3/4 of your power — gear is the minority

Weapon ATK by tier is `8 × T`: 8, 16, 24 … 80 at tier 10
(`_FORGE_ROWS`, `economy.py:470-502`), plus honing at +1 per floor past
the band start, capped at `unlocked_floor - band_start`
(`economy.py:815`). Run the at-level reference:

| At-level point | ATK from level | ATK from gear | Level's share |
|---|---|---|---|
| Floor/level 20, tier 2, hone 7 | 60 | 23 | **72%** |
| Floor/level 100, tier 10, hone 9 | 300 | 89 | **77%** |

And **max HP is 100% level** — gear contributes none of it.

So today level *is* the progression ladder and gear is a modifier on
top. WoW is the reverse. Capping level therefore does not just shorten
Ladder 1; it removes roughly three quarters of all power growth, and
gear has to be rebuilt to carry it.

### Four changes this needs

**1 · Add the cap.** None exists. Something like `LEVEL_CAP = 30` is a
natural candidate, because floor 30 is already where the design's solo
curve turns: wardens are tuned to "win 65–85% through floor 30", then
fade toward "bring friends" (`economy.py:328-332`). Reaching the cap
there means the level game ends exactly where the cooperative game
begins.

**2 · Blocker: gear tier is gated on *level*, so a cap locks out the
top tiers.** `gear_level_req(tier) = band_start(tier) = (T-1)×10+1`
(`economy.py:55-57`), i.e. tier 5 needs level 41 and tier 10 needs level
91. **Cap at 30 and tiers 4–10 become permanently unreachable — the
gear ladder dies exactly when it is supposed to take over.** This must
be re-keyed to **floor** instead of level. Same for
`rung_level_req` (`economy.py:742`), which gates the 0.5 rungs at
`band_start(T)+5`. This is the single hard prerequisite; nothing else in
the proposal works until it is done.

**3 · Re-weight the formulas so gear carries the growth.** After the cap
the level terms freeze — ATK at `3×30 = 90`, HP at `40+12×30 = 400` —
while floors 31–100 keep escalating. So:

- Weapon bonus needs to scale far harder than `8 × T` (something nearer
  `30 × T`, so tier 10 lands around 300 rather than 80), and honing
  should carry more per step.
- **Armor has to start contributing HP.** Today HP is purely level, so
  a capped player's HP would flatline at 400 for seventy floors. This is
  the biggest single piece of surgery in the proposal.
- Energy cap currently rides `level // 10`, so it would freeze at +3.
  Re-key it to floor, or to gear/faction progress.

**4 · Good news: the retune is centralised.** Monsters and wardens are
*derived from* the player model — `warden_stats` builds off
`player_max_hp(floor)` and `_at_level_loadout` is described as "the
reference all tuning points at". So fixing the reference loadout
propagates to every enemy automatically instead of requiring a
content-wide re-edit. This is much less frightening than it sounds.

### The unexpected win: XP becomes a currency

XP here is not only a progress bar — it is already spendable. `§1b`
(`economy.py:31-35`) describes the ✦ bar as "earned by fighting, spent
on honing / spells / scans", and `scan_xp_cost` (`economy.py:50`) prices
a shard scan in XP.

So **capping level does not orphan XP income — it converts XP from a
gate into a pure resource.** At cap, every kill's XP flows into spells,
scans and honing instead of a bar that has stopped moving. That is a
genuinely elegant outcome, and it also quietly dissolves the
gold → XP anxiety running through §8b and §10: once XP is a consumable
rather than the gate on advancement, converting gold into it is much
less dangerous.

### The resulting shape

- **Ladder 1 — player level.** Capped (~30), fast, reachable in the
  first weeks. Produces commitment. Its job is unlocking the town
  (Arcanum, Relay, fields), lifting beginner protection, and setting the
  power floor.
- **Ladder 2 — gear tier + hone depth, keyed to floor.** 10 tiers × the
  0.5 rungs = 19 rungs, each with up to ~9 hone steps on three slots.
  That is already an item-level analogue in everything but weighting;
  it just needs to become the majority of power rather than the
  garnish.
- **The public marker.** Item level works partly because it is *visible*
  and gates who will group with you. Our equivalent is the floor number
  on the shared frontier and the Stone of the Climb — which is the piece
  that makes Ladder 2 status-bearing rather than private bookkeeping.

### Honest caveats

Every number above is a shape, not a tuning. The XP curve
(`xp_need = 60 × level^1.5`, `economy.py:302`) and the gear price ladder
were fitted together against the "~3,300 at-level fights ≈ 165 days"
target, so re-weighting level against gear is a spreadsheet pass over
the whole economy, not an afternoon. It should be its own plan, and it
should land **before** the contract board and the night slot, because
those routes pay in gold and XP whose meaning this change redefines.

## 14 · Rejuvenation / regeneration as a player stat (Roy's proposal)

Roy: *"introduce rejuvenation speed as a player parameter — you heal
over time, and there is a speed to that, so players with amazing
rejuvenation heal mid-battle. But that's only for the super advanced
ones."*

Verdict: the **out-of-combat** half is good and cheap and I would ship
it. The **in-combat** half is not a new stat sitting beside the balance
model — it is a direct edit to the single constant the whole combat game
is tuned around, and there is a hard number that shows why.

### There is no regen of any kind today

Searched `combat.py` and the economy: nothing regenerates HP. Every heal
is a purchase — stew ◈2/+5 HP, the healer's tent at 5×floor, medgel
◈25, trauma kit ◈120, trollblood tonic ◈600 — plus the Lodge's +20 HP at
dawn, which is already a crude once-a-day regen tick. So this is
greenfield, and the Lodge line is the proof of concept.

### The number that decides it

`WARDEN_DMG_BUDGET = 1.07`, documented as "**expected damage dealt ÷
player pool**" (`economy.py:335`), across a fight of ~12 rounds
(`WARDEN_HP_MULT`, `economy.py:334`). So an at-level warden is built to
deal **107% of your maximum HP**, at roughly **8.9% of your pool per
round**.

Two consequences follow immediately.

**Immortality arrives at ~9% of max HP per round.** Regenerate that much
and an at-level warden mathematically cannot kill you, and the fight
never ends. For ordinary monsters, which hit for less, the threshold is
lower still. So the entire safe design window for flat per-round regen
is a **single-digit percentage of max HP** — the stat does approximately
nothing until it abruptly does everything. That is the classic
sustain-stat failure: a cliff, not a slope.

**Even a "modest" value rewrites the win curve.** The whole solo model
is calibrated to win 65–85% through floor 30 at ~0% expected HP margin
(damage dealt ≈ 107% of pool is *designed* to be a knife edge). Regen of
even 2% per round over 12 rounds returns ~24% of your pool — a ~22%
effective-HP swing, which pushes win rates well past the target band and
forces `WARDEN_DMG_BUDGET` to be re-derived. In-combat regen is
therefore a **retune of the central balance constant**, not an addition
beside it.

### A second, sharper hazard: the stall exploit

Combat here is **player-paced and round-by-round** — `_ROUND_ACTIONS`
(`combat.py:640`) drives per-round options, and fight state persists in
the player record between messages. So if rejuvenation ticks on the
**clock**, a player simply waits between rounds and returns at full HP.
Every fight becomes unloseable for anyone patient, which is the one
resource this game's audience has by design.

**Rule: out of combat, regen may tick per minute. In combat, it must
tick per round — never per unit of real time.**

### The house pattern already exists, and it fits

The codebase has faced exactly this species of stat once before. Speed
grants dodge, and the answer was `DODGE_CAP_PCT = 12` with the comment
"**speed never becomes the main defense**", implemented as log-decay
from advantage only — `min(12, round(7 × log2(1 + a)))` — and documented
as "capped so armor and resist stay the primary defenses **by
construction**" (`economy.py:170`, `207-211`).

Rejuvenation should inherit all three properties: a **1–10 authorable
scale** like `SPEED_SLOW/NORMAL/FAST`, **log-decay with a hard cap**, and
**full visibility on the [i] card** — the chase model's stated law is
that a card can "show the whole chase without a single hidden number"
(`economy.py:165`).

### The shape I would actually build

Three candidate models, worst to best:

1. **Flat HP per round.** Has the 9% cliff. Avoid.
2. **Proportional (leech: heal a % of damage dealt).** No time cliff and
   it scales with your offence, but it still compounds with long fights
   and still needs a per-round ceiling.
3. **A per-fight regen budget — recommended.** You recover up to *N%
   of your pool per fight*, spent automatically as you take damage, and
   a longer fight yields **no more** healing. This kills the immortality
   cliff and the stall exploit in one move, because duration stops being
   the lever. Mechanically it is "second wind" charges, and it prices
   cleanly against the potion ladder it competes with.

### Two more things worth knowing

**It erodes a designed gold sink.** Healing is a real drain in the
economy, and `vision/economy.md` §9 budgets stacked drains at ≤40% of
daily income. Free healing deletes part of that budget and loosens
everything downstream. Out-of-combat regen should be slow enough to
matter across a break and too slow to replace a mid-session potion.

**It directly counters one enemy archetype.** `bulwark` is documented as
"the outlast-you enemy" with `BULWARK_HP_MULT = 2.2`
(`economy.py:151-152`). Regen is precisely the counter to an enemy whose
identity is *long fight*, so bulwark encounters need a look — either as
a deliberate rock-paper-scissors interaction, or bulwark gets a regen
suppression trait.

### Where it belongs in the plan order

"Only for the super advanced" is exactly right, and it lands better than
Roy may realise: a stat that is **gear-, relic- and faction-driven and
never level-driven** is a textbook **Ladder 2** stat under §13. It gives
the post-cap gear ladder a second axis to grow on besides raw ATK and
DEF, which is what stops item-level-style progression from being one
boring number.

So: ship **out-of-combat rejuvenation** alongside rested aether — same
family, same "a break never punishes below baseline" goal, cheap, safe.
Hold **in-combat rejuvenation** until the §13 level-cap retune, and
introduce it there as a capped Ladder 2 stat with a per-fight budget, so
`WARDEN_DMG_BUDGET` gets re-derived once with everything else rather
than twice.

## 15 · Boss regeneration and a time cap (Roy's proposal)

Roy: *"wardens — all bosses — need rejuvenation. I don't think they
should take 1 accumulative damage, otherwise it's too easy. You need a
time cap on killing them, and they all need super fast rejuvenation, a
few hours."*

Half of this is already built, the other half does not apply, and the
version Roy is asking for carries one serious risk. The three boss types
work completely differently:

| Boss | Damage model | Time cap today |
|---|---|---|
| Solo warden (3⚡) | one sitting, resolved in the fight | n/a — no accumulation |
| **World frontier warden** | **shared HP pool, chipped by anyone** | **regen only, no deadline** |
| Milestone boss (10, 20 … 100) | **no HP pool at all** | **rolling 3-world-day window** |

### The frontier warden already regenerates

`WARDEN_WORLD_REGEN_HOURLY = 0.08` (`economy.py:409`), applied by
`_warden_regen` (`worldd/app/social.py:221-231`) as a lazy computation:
`hp + hp_max × 0.08 × hours_since_last_strike`, clamped to `hp_max`, and
"never persisted on read — only strikes write." The pool itself is
`WARDEN_WORLD_HP_MULT = 4` × the solo warden's HP.

What that rate actually means: **8%/hour is 1.92 × the full pool per
day.** So a world must deal more than roughly *twice the pool's HP in a
single day* merely to hold ground, and about three times it to kill the
warden in a day. That is already a strong brake — not free accumulation.

But Roy's instinct is still half right, and the precise reason matters:
**it is a rate contest, not a deadline.** There is no point at which
progress is lost, so a slow, steady trickle of strikes does grind the
pool down eventually. What is missing is not regen. It is a **deadline**.

### Milestone bosses have no HP pool, so regen cannot apply

`_fx_boss_commit` (`social.py:707-724`) writes one commit row per pledge,
then counts `WHERE floor=$1 AND world_day >= day - 2` — **a rolling
three-world-day window**. Once commits reach `ms.quorum`, `_resolve_boss`
runs a single check: `party_power × swing ≥ boss_power × 0.75`, with
`boss_power = atk×2 + dfs + hp//4` and `swing` between 0.9 and 1.1
(`social.py:727-747`).

So milestone bosses never accumulate damage and **already have exactly
the time cap Roy is asking for** — pledges expire after three world
days. There is nothing to add here, and regeneration would be
meaningless because there is no HP pool to regenerate.

### Why "a few hours" regen is the risky version

Full recovery in a few hours means roughly 25–33%/hour, i.e. **6–8× the
pool per day just to hold ground**. That does not merely make the warden
harder; it changes what kind of game it is. It requires a group to strike
**within the same few-hour window**, which means synchronous
coordination.

That is in direct tension with everything else here. Energy ticks at 1
per 45 minutes; the away-present rewards being gone 20+ hours; the
pacing philosophy is "the wait *is* the game". This is an asynchronous,
idle-friendly, chat-based game whose players are in different time zones.

And the stakes are unusually high, because **the frontier warden gates
everyone's content** — killing it announces "floor N+1 is open for
everyone" (`social.py:700`). If the warden becomes unkillable without
synchronous raid coordination, the **whole world stops advancing**, not
one player. A too-fast regen does not produce a hard fight; it produces
a stuck world.

### The better mechanism: a deadline on a clock that already exists

What Roy wants is a time cap. Take it literally rather than through
regen:

**The warden's wounds close at dawn.** Reset the pool to full at each
world-day boundary. It delivers:

- **A real deadline** — 24 hours, all or nothing, which is precisely the
  "time cap" being asked for, and it removes accumulate-forever without
  touching the regen rate.
- **No synchronous requirement.** Anyone can contribute at any hour of
  their own day, so async play still works and the world cannot get
  stuck for scheduling reasons.
- **A lockout on its own independent clock**, which is exactly the
  prescription from §12 — WoW paces its endgame with a dozen independent
  lockouts, and we currently have one shared energy meter.
- **Drama.** A visible daily attempt that either lands or resets is far
  more legible than a pool slowly sagging over a week.
- **Cheap to build.** `pstate.world_day()` already exists and boss
  commits already key off it; `_warden_regen` is already lazy, so the
  reset is a stored-day comparison rather than a scheduled job.

Then keep the 8%/hour regen underneath as the within-day brake it
already is. Deadline plus gentle regen gives Roy the "you cannot chip it
forever" outcome; fast regen alone gives it *and* a coordination
requirement the rest of the design cannot pay for.

If a day proves too short once the frontier is busy, the honest dial to
turn is the pool multiplier (`WARDEN_WORLD_HP_MULT = 4`) or the window
length — not the regen rate, because the regen rate is the thing that
secretly demands everyone be online together.

## 16 · Roy's rephrasing: regen is a coordination mechanic, and healing
## should buy time

Roy: *"warden regen is something that forces lots of players to attack
together — maybe we have a different mechanic for that. It isn't really
recovering mid-attack, it's a few hours or a day, so if we all attack at
roughly the same time it means nothing — so it forces organised attacks,
which is what I was trying to get to. Also let's lose the mid-fight
regain, it means nothing for the player — we can pace it for 24h or more
so it just makes sense: healing costs money, buys time, or not if you
don't need it."*

This is the clearest statement of intent in the whole document and it
corrects §15 in two places.

### First, the solo path: what is true, and where it stops

The mechanism is solo. `combat.py:720-724`:

```
if e["kind"] == "warden":
    nxt = floor.floor + 1
    if p["unlocked_floor"] < nxt:
        p["unlocked_floor"] = nxt
```

Beating your own 3⚡ warden advances your own `unlocked_floor` with no
reference to the world. But an earlier draft of this section concluded
from that "the shared frontier warden is a parallel prestige track, not a
gate on anyone's climb", and **that is wrong** — it read the code path
and ignored the tuning on top of it.

Roy's model — *"the first maybe 30 floors are soloable if a player is
phenomenal; at some point they have to be unbeatable alone"* — is not a
proposal. **It is already the shipped design, almost to the floor
number:**

- `WARDEN_SOFT_FLOOR = 30`, commented literally "**last floor tuned for
  solo play**" (`economy.py:336`).
- Past it, `WARDEN_HP_RAMP = 40` and `WARDEN_ATK_RAMP = 100` apply
  `HP × (1 + (F−30)/40)` and `ATK × (1 + (F−30)/100)`. By floor 100 that
  is **2.75× HP and 1.7× ATK** on top of the normal curve.
- And the header states the intent outright: "win 65–85% through floor
  30, then HP/ATK ramps fade solo odds smoothly toward 'bring friends'
  (**<10% well before floor 50**)" (`economy.py:328-332`).

So the real shape is three bands:

| Floors | Solo warden | What the frontier warden is |
|---|---|---|
| 1–30 | tuned to win 65–85% | optional — a faster, shared alternative |
| 30–50 | fades smoothly; "phenomenal player" territory | increasingly the sane choice |
| 50–100 | **<10%; effectively dead** | **the only practical path** |

### Which means both earlier answers were half right

§15 worried that forcing coordination could stall the world. §16's first
draft said that worry dissolved because the solo path exists. Neither is
right across the whole tower — **each is correct in a different band**:

- **Floors 1–50: forcing coordination is safe.** A solo climber has a
  real path, so a demanding frontier warden costs them speed and
  prestige, not progress.
- **Floors 50–100: the frontier warden genuinely is the gate**, because
  the solo alternative is a <10% coin flip by construction. Up here the
  §15 concern is live and correct — a coordination requirement that a
  world cannot actually meet stalls everyone.

That is not an argument against Roy's design. It **is** Roy's design:
the tower is meant to stop being a solo game somewhere around 30–50.
The consequence is only that the coordination mechanic needs to be
**tuned by band** — forgiving enough at floors 50+ that a real
population can organise, since above there it is not a bonus route, it
is the route.

It also strengthens the §13 proposal from a different direction: a level
cap at **30** would put the end of the level game, the end of the solo
warden game, and the start of the cooperative game all on the same
floor. Three systems agreeing on one number is usually a sign the number
is right. And under a level cap, "a phenomenal player soloing floor 40"
stops being a story about levels and becomes one about **gear** — which
is exactly the Ladder 2 story §13 is trying to tell.

### Second: if coordination is the goal, say so in the mechanic

Roy's read of the current design is exactly correct. Regen at an
hours-to-days scale does nothing inside a single fight; what it actually
tests is *whether several people struck inside the same window*. It is a
coordination check wearing a healing costume.

The problem with leaving it implicit is **legibility**. A rate is
invisible; a player cannot look at `0.08 × hours_since_last_strike` and
know whether to rally. In a chat-driven game with a Crier and a Stone of
the Climb, the coordination signal should be something you can announce.

**Recommended: decay-on-silence, not reset-at-dawn.** The warden's
accumulated wounds persist only while it keeps being struck — if nobody
lands a blow for N hours (6 is a reasonable first guess), the pool closes
fully. Compared with §15's daily-reset suggestion this is strictly
better for this game:

- It **forces organised attacks**, which is the stated goal, because a
  scattered trickle can never finish it.
- It imposes **no global clock**. The window opens whenever the first
  striker hits, so a guild in any time zone can pick its own moment —
  where a dawn reset would hand the advantage to whoever lives near the
  reset hour.
- It is **announceable**: "the Warden bleeds — 3 strikers in the last
  hour, the wound closes in 4." That is a Crier line and a reason to call
  friends.
- It reuses the primitive we already have. Milestone bosses already count
  pledges inside a rolling window (`ascent_boss_commits`, `world_day >=
  day - 2`), so a windowed frontier warden makes the two boss types
  consistent instead of inventing a third pattern.

So §15's daily reset is superseded: keep the 8%/hour as the gentle
within-window brake, and add the silence timer as the thing that actually
demands a rally.

**The silence window should widen with the floor.** Per the band table
above, below floor 30 a tight window is a fair challenge because solo is
still a real option; above floor 50 the frontier warden *is* the only
path, so a window short enough to be exciting at floor 20 would stall the
tower at floor 80. Scaling it (say 6 hours early, 24+ hours near the top)
keeps the pressure high where players have an alternative and keeps the
world moving where they do not.

### Third: dropping mid-fight player regen removes three problems at once

Agreed, and it is a clean win — it deletes, in one decision:

- the **~9%-of-max-HP-per-round immortality cliff** (§14),
- the **pause-to-heal stall exploit**, since player-paced rounds no
  longer interact with a clock,
- the forced **re-derivation of `WARDEN_DMG_BUDGET = 1.07`**, which the
  entire 65–85% solo win curve is calibrated against.

Nothing of value is lost, because at any survivable rate the effect was
imperceptible anyway.

### Fourth: "healing buys time" is the design law this economy was missing

*"Healing costs money — buys time, or not if you don't need it."*

That is exactly what the Energy cell already does (§8b): ◈200 does not
give you power, it gives you **five energy you would otherwise have
waited for**. Generalise it and there is a single law that ties the whole
economy together:

> **Gold never buys power. Gold buys time.**

The cell buys energy-time. A potion buys HP-time. The Lodge buys
safety-time. Honing and gear are the exception that proves the rule —
they buy power, and they are gated on *floor*, which is earned.

This also quietly resolves the anxiety running through §8b and §10 about
gold becoming XP. Under this law the answer is clean: **gold cannot buy
progress, only earlier progress.** That is a far more defensible line
than "no gold → XP faucet", and it is one sentence a player can hold in
their head.

### The knob that keeps healing worth paying for

There is one arithmetic trap in free timed healing. Energy fills in about
18 hours (cap 24, one per 45 min). If HP also fully restores in ~24
hours, then a player returning from any real break arrives with **full HP
and full energy** — and will never buy a potion again. The gold sink dies
and `vision/economy.md` §9's drain budget goes with it.

The fix is a ratio, not a rate: **HP must regenerate slower than
energy.** If a full heal takes 36–48 hours while energy fills in 18, the
mid-session player is reliably in the state *"I have energy I dare not
spend"* — which is exactly the moment a potion is worth real money. That
tension is what makes "healing buys time" an economy rather than just a
nice sentence.

## 17 · The floor/level naming collision — an audit

Roy: *"we called floor levels and may have had problems with that."*

Correct instinct. Audited every call site of the level-typed functions
(`player_atk`, `player_def`, `player_max_hp`, `xp_need`, `levelup_gold`,
`energy_cap`). The good news is that **there is no live bug**: every
runtime call passes `p["level"]`.

There is exactly **one** place a floor is passed into a level parameter:

```
per_round = budget * player_max_hp(floor) / rounds
```
(`economy.py:386`, inside `warden_stats(floor)`)

`player_max_hp` is declared `def player_max_hp(level: int)`
(`economy.py:80`). It is being handed a **floor**. That is not an
accident — it is the `_at_level_loadout` convention ("level = floor")
expressed in code — but it is the conflation made load-bearing, and it
is the single most dangerous line in the codebase for §13.

**Why it matters for the level cap.** Cap level at 30 and
`player_max_hp(80)` still returns `40 + 12×80 = 1,000`, while a real
capped player has `40 + 12×30 = 400`. Warden ATK at floor 80 would be
derived from a player who **cannot exist**, over-tuned by ~2.5×. Nothing
would raise an error; both values are `int`, and there is no type checker
configured in the plugin (no `pyproject.toml`, no mypy or pyright config).
It would simply produce wardens nobody can beat, and the cause would be
one silent argument.

### The naming, separately

Three functions return a **floor** and call it a **level**:

- `gear_level_req(tier) → band_start(tier)`, whose own docstring reads
  "Level required to buy tier-T gear: the band's first floor"
  (`economy.py:55-57`) — and `band_start` is documented as "First floor
  of a gear band" (`economy.py:801`).
- `rung_level_req(g) → band_start(t) + 5` (`economy.py:742-748`).
- `floor_level_req(floor)` — "Level required to enter a floor"
  (`economy.py:60`). The name itself parses two ways.

These are the same three functions §13 identified as the hard blocker,
which is not a coincidence: **the places where the two meanings were
collapsed are exactly the places that must be separated to cap levels.**

Worth noting the **player-facing language is fine.** The UI consistently
says "floor" for the tower and "level" for the player, and even
distinguishes them in one sentence: "Floor {frontier} wants level {req}
legs" (`core.py:200`). The collision is in the code and in our
vocabulary, not in the game.

### What to do about it

Cheap, and worth doing *before* the §13 retune rather than during it:

1. **Rename to remove the ambiguity.** `gear_level_req` →
   `gear_player_level_req`, `floor_level_req` → `floor_entry_level_req`,
   and make each one's body state which quantity it is converting.
2. **Break the one conflated call.** Give `warden_stats` an explicit
   reference-player HP — e.g. `reference_player_hp(floor)` — so the
   floor→level conversion happens **once, named, in one place** instead
   of implicitly at a call site.
3. **Pin it with a test.** The plugin has no type checker but a heavily
   used `tests/` directory, which is the right tool: assert that warden
   tuning tracks the reference player rather than `player_max_hp(floor)`,
   so capping level cannot silently detune every warden above 30.

## 18 · Corrections log

## 13 · Corrections log

- **"Gold cannot buy energy"** — false. The **Energy cell** (◈200, +5⚡,
  1/day, Apothecary & Medlab) does exactly that; `economy.py:879`,
  `core.py:1134`. The search that missed it looked for *energy* near
  *refill / buy / purchase / meal / restore*; the item is named "cell"
  and its effect string is `energy_5`, so nothing matched and absence of
  evidence got reported as evidence of absence. Anything below phrased
  as "gold can only reach gear" inherited that error and is corrected in
  §8b and §10.
- **"Level and floor advance together, so they are one ladder with two
  labels"** — sloppy. They are two separate systems: the tower's 100
  levels are **floors/worlds**, and player level is its own number with
  its own XP curve. What is true is narrower and more useful: the tuning
  reference `_at_level_loadout` assumes **level = floor**, so the two are
  yoked by convention rather than by mechanism — which is what makes
  unyoking them (§13) possible at all.
- **"The warden is 10× a normal fight"** — misleading. `warden_gold =
  80 × F` against `8 × F` is 10× per *fight*, but a warden costs **3⚡**
  against 1⚡, so the honest figure is **~3.3× per energy** (still the
  best rate available, and ~2× on XP).
