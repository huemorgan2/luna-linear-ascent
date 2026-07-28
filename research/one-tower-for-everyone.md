# One tower for everyone — the MMO redesign, the ending, and reincarnation

Roy's brief, 28 Jul: *"This is an MMORPG — all players together. Everyone is
playing against only 100 wardens, so we might have tuned it all wrong. The
higher the floor, the tougher the warden exponentially — more people, more
coordination in time. Faster rejuvenation means less time to kill it. The
100th warden should take at least 100 players in a coordinated attack — or
10% of active players, but no less than 50. The game has an end, for everyone
together. After that we reset the world and grant everyone one reincarnation
point, so players who have been to 100 are recognised forever."*

This file thinks that through end to end: what exists, what the numbers say,
the model, the coordination curve, the ending, and what survives a reset.

---

## 1 · Setting the record straight: there are TWO warden systems

Not a hallucination — a duplication, and the duplication *is* the fundamental
flaw. The shipped game contains both models at once:

**System A — the personal warden.** Every player fights their own copy of each
floor's warden (the "Warden's keep", 3⚡). Victory raises **that player's**
`unlocked_floor`:

```720:723:plugin-linear-ascent/plugin_linear_ascent/engine/combat.py
    if e["kind"] == "warden":
        nxt = floor.floor + 1
        if p["unlocked_floor"] < nxt:
            p["unlocked_floor"] = nxt
```

This is the only place in the codebase a floor is unlocked for anyone.

**System B — the shared world warden.** One HP pool per frontier floor, lives
in worldd (`ascent_world`, key `warden:{floor}`), struck by anyone for 3⚡,
regenerates 8%/hour, and when it dies the **world frontier** advances and the
reward pool splits by damage dealt (`worldd/app/social.py:591-704`).

The two systems do not connect. Killing the world warden bumps the world's
`frontier` counter and prints "floor N+1 is open for everyone" — but opens
nothing for anyone, because entry is gated on the *personal* `unlocked_floor`
from System A. Meanwhile three places in the game (the Stone, the worldd
announcement, the `floor_level_req` docstring's "world lift") describe the
shared model as if it were real.

So today: every player privately re-climbs all 100 wardens, and the shared
warden is a co-op piñata that pays gold and pretends to open doors. Roy's
brief resolves the ambiguity: **keep System B, make it real, and demote or
re-purpose System A.** The rest of this file designs that.

## 2 · "We tuned it all wrong" — checked, and confirmed, with a twist

How many players does the shared warden actually require today?

The strike (`engine/social.py:818-832`): 3⚡ buys one swing —
`max(1, rng(ATK/2, ATK) − DEF_w/2)` — roughly **one combat round of at-level
damage**, and you eat one counter-swing. Compare the solo warden fight: the
same 3⚡ buys the *whole fight*, ~12 rounds of damage (`WARDEN_HP_MULT = 1.9`,
"a real boss fight (~12 rounds)"). So striking the shared pool is ~12× less
damage per energy than solo play — deliberate, it is a raid pool.

Measure everything in "rounds of at-level damage":

- World warden HP = 4 × solo warden HP ≈ **48 rounds** (`WARDEN_WORLD_HP_MULT
  = 4`).
- Regen = 8%/hour of max = 1.92 × pool/day ≈ **92 rounds/day** while wounded.
- One player, spending *all* 32 daily energy on strikes: ~10.7 strikes/day =
  **~10.7 rounds/day**.

Therefore, at every floor, as shipped:

| Question | Answer |
|---|---|
| Can one player ever solo the world warden? | **No** — 10.7/day against 92/day regen. It out-heals them forever. |
| How many players to hold ground (sustained)? | ~**9**, all-in. |
| How many to kill it in one rally? | ~**7** with full energy bars striking within the hour (7 × 8 = 56 rounds vs 48 + ~4 regen). |
| How does the requirement scale from floor 5 to floor 95? | **It doesn't.** HP mult (4×), regen (8%/hr), the strike formula and the at-level player all move together. The head count is ~flat across the whole tower. |

So Roy's instinct is confirmed, precisely: the coordination requirement is
**flat at roughly seven players from floor 1 to floor 100**. The floor-100
warden is exactly as much of an event as the floor-10 warden. Worse, at *low*
floors seven-players-or-nothing is probably too hard for a young world, and at
high floors it is absurdly too easy for a climax. The tuning is wrong at both
ends — not because anyone mis-set a constant, but because **no constant scales
with the floor or the population.** (Caveat: these are at-level-reference
numbers; under-levelled strikers deal less and the counter-swing culls the
squishy. The shape — flat — is the finding.)

## 3 · The model: One Tower

The identity change, stated once: the game stops being **ten thousand private
staircases climbed in parallel** and becomes **one tower, one war, everyone in
it.** A floor falls once, for the world. Your personal story is what you
contributed and where you stood when it happened.

### 3.1 All 100 wardens are shared — Roy's ruling

An earlier draft of this section recommended a hybrid (personal wardens
1–30, shared 31+). **Roy rejected it: there are only 100 wardens, all
shared, full stop.** The first climber to fell warden 1 clears the path for
everyone, exactly like the first to fell warden 71. The personal-unlock
system (`combat.py:720-724`) is deleted, not demoted; `unlocked_floor` rides
the world frontier from floor 1, leashed by
`floor_level_req = max(1, floor − 10)`.

The 1–30 boundary is **tuning, not structure**:

- **Floors 1–30:** the shared warden's regen sits *below* one player's
  maximum sustained output and its pool is worth one or two full energy bars
  — so a single amazing player can fell it alone. Hard, achievable.
- **Floor 31 up:** regen sits *above* any single player's maximum possible
  output. Solo impossible by arithmetic, not by rule — no message forbids
  it; the wound simply closes faster than one blade can cut.

**And the warden fight becomes a real fight.** The single-swing strike
merges with the full 12-round keep fight: you battle the warden properly,
and the damage you dealt persists to the shared pool when you die, flee or
withdraw. Take the pool to zero and it falls — for everyone, your name first
on the Stone. At low floors the pool is one great fight's worth, so the solo
kill is a single legendary session; at high floors your best fight is one
cut in a siege. One combat system, one warden list.

**Echo fights, optional.** A fallen warden can be re-fought as an echo —
personal reward at a fraction, no world effect — so a late joiner in a
racing era still meets the boss content.

### 3.2 What a player's climb means now

Level (capped, per §13) and gear carry personal power; floors 1–30 are yours
to conquer; from 31 up, your progress is the **world's** progress plus your
standing in it — contribution to sieges, faction glory, wealth, gear depth.
A returning player's news becomes "while you were away, floor 47 fell" — the
world moves even while you sleep, which no single-player tower can offer.
That one sentence is the retention argument for the whole redesign.

## 4 · The coordination curve

### 4.1 The requirement

Let `A` = active players (worldd already has the roster and by-floor counts).
Define the head count required at floor 100:

    R100 = max(50, 0.10 × A)        # Roy's rule

and the required simultaneous strikers at floor F (31 ≤ F ≤ 100):

    N(F) = ceil( R100 ^ ((F − 30) / 70) )

— exponential from 1 at floor 30 to R100 at floor 100, which is the "tougher
exponentially, more people" curve requested. Worked table at A = 1,000
(R100 = 100):

| Floor | N(F) required |
|---|---|
| 35 | 2 |
| 40 | 2 |
| 50 | 4 |
| 60 | 7 |
| 70 | 14 |
| 80 | 27 |
| 90 | 52 |
| 100 | 100 |

At A = 200 (R100 = 50): floor 50 needs 3, floor 80 needs 15, floor 100 needs
50. The curve reshapes itself to the population.

### 4.2 Enforcing N players with the two knobs we already have

"Requires N players" must be mechanical, not aspirational. Two knobs:

- **Regen sets the minimum head count.** A player's sustained output is ~10.7
  rounds/day. Set regen so that fewer than N(F)/2 players cannot hold ground:
  `regen_per_day(F) ≈ (N(F)/2) × 10.7` rounds. Below that head count the
  warden visibly out-heals the assault — the game itself says "bring more."
- **HP sets the rally size.** A full energy bar is 8 strikes ≈ 8 rounds. Set
  `HP(F) ≈ N(F) × 8` rounds — the pool falls when N players with full bars
  strike within the same window, and not before.
- **The silence window keeps it honest.** From the earlier warden research:
  wounds persist only while strikes keep landing; silence for W hours closes
  them fully. W scales with floor — tight early (6h), generous at the top
  (24h+) — so "coordinated" means *within the same day*, not *within the same
  minute*, which an async chat game in mixed time zones can actually deliver.

Roy's "faster rejuvenation means less time to kill it" is these two dials —
regen for head count, window for tightness — and they can now be tuned per
floor instead of being one flat constant.

### 4.3 The small-world failure mode — flagged, not hidden

`max(50, 10%)` has a sharp edge at low population. At A = 300 the final
siege needs 50 = 17% of everyone; at A = 80 it needs 62%; at A = 40 it is
mathematically impossible. Three honest options:

1. **Accept it**: "the Tower outlasts small worlds" — an era simply does not
   end until the game is big enough. Thematic, risky for early life.
2. **Scale the floor**: `R100 = max(min(50, 0.5 × A), 0.10 × A)` — the 50
   minimum only binds once the world can afford it.
3. **A pity ramp**: each failed grand siege permanently weakens the final
   warden by a few percent. The world can always *eventually* win; drama
   preserved, softlock impossible.

Recommendation: 2 + 3 together. 1 is a beautiful sentence and a bad launch.

## 5 · The ending

### 5.1 The grand siege

Floor 100, Vharuk. This one should not be ambushed into falling on a random
Tuesday — it is the era's finale:

- **Declared, not stumbled into.** When the frontier reaches 100, the game
  announces the siege window in advance (the Crier, the Stone, letters). The
  world knows the final battle is this weekend. (Helldivers 2's major orders
  and GW2's world bosses both show scheduled collective events work.)
- The kill requires `R100` strikers within the window, by the §4 mechanics.
- Failure closes the wound and schedules the next siege — with the pity ramp
  ticking, so the story is "we get stronger", never "we are stuck."

### 5.2 What happens when it dies

Everyone's game ends **together, in victory** — which almost no MMO has ever
dared to ship and is the single most memorable thing this design buys. An
era-end sequence: the fall announced, the Stone's final inscription written,
a closing ceremony scene, the ledger of the era (first clears, top strikers,
faction standings) frozen forever. Then the world resets.

### 5.3 What resets, what survives

| Resets (the world) | Survives (the record) |
|---|---|
| floors, frontier, all warden state | **the reincarnation ledger** (new, permanent worldd table) |
| player level, XP, gold, gear, inventory, relics | titles and era marks per player |
| factions, hoards, letters, PvP standing | the **Stone of Eras** — each era's frozen ledger, readable in-game forever |
| the bank (interest hoards die with the era — quietly fixes long-run inflation) | cosmetic recognition (name glyphs ✦) |

The reset is also the economy's safety valve: every faucet-vs-sink worry in
`progression-more-ways-to-earn.md` becomes bounded by era length. Mudflation
cannot outlive the world it happened in.

## 6 · Reincarnation

### 6.1 The grant

When an era ends in victory, **one reincarnation point to every player who was
part of that era** (definition needs care: e.g. reached level 5+, or was
active in the final 60 days — pick a line that excludes empty registrations
without punishing casual players; the collective ending should feel
collective). On top of the shared point, **recognition tiers** that are earned,
not given:

| Mark | Earned by |
|---|---|
| Era mark ✦ | being part of the completed era |
| *Centurion* (or better name) | personally standing on floor 100 before the fall — Roy's "been to 100 once will be recognised" |
| *Siegebreaker* | striking Vharuk in the final siege |
| *The Hand* | the final blow — one player per era, ever |

### 6.2 What a point buys — the law from the economy research applies

**Prestige buys time, never power** (the generalisation of "gold buys time,
never power"). A reincarnated climber must not out-stat a newcomer, or every
fresh era starts pre-lost and new players bounce. Safe perks: start with the
Relay and Arcanum already open; a pre-filled rested-aether pool; echo fights
unlocked from day 1; a visible glyph and era-count by your name; first pick of
cosmetics. Unsafe and refused: stat bonuses, gear head starts, energy cap
increases that compound across eras.

### 6.3 Precedents worth stealing from

- **A Tale in the Desert** — the only MMO that actually ends and resets, in
  "Tellings" that run 1–2 years; veterans carry recognition forward. Proof
  the model retains a community across resets.
- **Path of Exile leagues** — 3–4 month economy resets as the *main* mode;
  proof that resets are an acquisition event, not churn. New leagues are PoE's
  biggest player spikes.
- **Helldivers 2** — one shared war, the whole playerbase against one
  objective, with real endings and community-wide victory/defeat memory.
- **WoW** — seasons reset the gear ladder on purpose (per the §12 research);
  Ahead-of-the-Curve titles are the recognition-tier pattern.
- **Sword Art Online** — the fiction Roy named: one tower, floors cleared once
  for everyone, the clearing group carries fame, and the game *ends* when
  floor 100 falls. This design is that, made mechanical.

## 7 · Era pacing

Target from the vision docs: the climb is "a season, not a weekend" — ~4–6
months. Under One Tower the frontier's speed is the sum of siege times:

    era_length ≈ Σ (time to organise + kill warden F), F = 31…100

With N(F) as in §4 and a healthy population, floors 31–60 fall in a day or
two each and 90+ take a week or more of rallying — roughly 4–7 months, with
the top of the tower consuming most of it, which is the right dramatic shape.
The knobs (N-curve exponent, HP, windows) tune directly to the era target,
and *population-adaptive* N means era length stays roughly constant whether
the world holds two hundred players or twenty thousand. That is the deepest
virtue of Roy's 10% rule: **the game's finale scales itself.**

## 8 · What this costs to build (sketch)

**worldd:** active-player count endpoint (roster exists); per-floor warden
params from N(F) instead of constants; frontier-opens-floors (the System B
promise made real); siege windows + announcements; era state machine; the
permanent reincarnation ledger and Stone of Eras tables (outside reset scope);
reset tooling.

**plugin:** `unlocked_floor` rides the world frontier above 30 (leash
enforced); echo fights; era-end and ceremony scenes; reincarnation display;
strike UX that shows N-required vs strikers-present and the closing window —
the rally must be *legible* ("the Warden bleeds — 41 of 52 blades present").

**Prerequisites from the existing research:** plan 021 (floor/level split)
before any retune; the §13 level cap pairs naturally — level 30 cap, personal
wardens to 30, war from 31 — one coherent boundary.

## 9 · Open decisions for Roy

1. ~~Floors 1–30 personal, 31–100 shared — or all 100 shared with echoes?~~
   **Decided by Roy: all 100 shared.** The 1–30 solo band is tuning (regen
   below one player's output), not a separate system.
2. Small-world rule: accept / scaled floor / pity ramp (recommends 2+3).
3. Who gets the era point — everyone active, or participation-gated, and by
   what line?
4. Can an era end in **defeat** (a world deadline the players can miss), or is
   victory the only ending? Defeat is dramatically potent and brutal.
5. Do factions get era-level recognition (the faction that led the final
   siege), which would make faction membership matter far more?
6. Does PvP persist anything across eras (vendetta marks), or is combat
   history wiped clean?

---

*Companion files: `progression-more-ways-to-earn.md` (the economy evidence
this builds on) and `plan-suggest-ideas.md` (ideas 20, 21, 22 and 25 are
absorbed by this model — the shared-lift question is answered "yes, above
floor 30", the silence window becomes §4.2, and seasons become eras).*
