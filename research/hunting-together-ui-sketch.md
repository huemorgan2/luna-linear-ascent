# Hunting together — how it looks, how it feels

A written picture of multiplayer on the hunting grounds, in the game's own
card language. Ping-pong material, not a spec. Companion to idea 27 in
`plan-suggest-ideas.md`.

Three feelings we are engineering, in order of appearance:

1. **The floor is inhabited.** Other players stop being roster rows and
   become torches on your floor.
2. **The fight is shared.** Your friend's blows land in *your* round log.
3. **Being saved.** The flare. This is the moment people tell stories about.

And one law over all of it, because this is an async chat game:

> **You never wait for another player.** Their actions appear between yours
> when they are there; the fight stays fully playable when they are not.
> Joining is always one tap. Leaving is never a penalty to the other side.

---

## Scene 1 — arriving: torches on the floor

Today the wilds are empty of people. One new block changes that:

```
FLOOR 12 · EMBER GULCH
Ash on the wind. Two other torches burn on this floor.

· Kettle — hunting the north scarp        level 14 · Redvane
· Brakka — at the Warden's keep, hurt

[1] Hunt the wilds                        1 ⚡
[2] Hunt with Kettle                      join her ground
[3] Go to Brakka                          someone should
[4] The Warden's keep                     3 ⚡
[5] Back to the gate
```

Presence is ambient — nobody asked to be social, the floor just *has people
on it*. "Hurt" is deliberate: a one-word status that manufactures reasons to
walk toward a stranger.

## Scene 2 — the shared fight, from your side of it

You tapped [2]. Kettle is mid-fight; you drop in as the second blade. This is
**your** card — she has her own, seeing the same fight mirrored:

```
EMBER GULCH · CINDER WOLF                 41/58
Kettle fights beside you.

▪ your blade opens its flank — −11
▪ Kettle's arrow takes the eye — −18 · it wheels on HER
▪ it lunges at Kettle — she slips it. Speed tells.

[1] Strike                                its back is to you
[2] Guard Kettle                          pull its eyes off her
[3] Shard: mark the throat                both your next blows crit · 6 ✦
[4] Fall back
```

What is happening mechanically, hidden under plain language:

- **Aggro is a sentence, not a stat.** "It wheels on HER" — the wolf faces
  whoever hurt it last. Your options change with its facing: a turned-away
  wolf offers `Strike (its back is to you)`; a wolf on your friend offers
  `Guard`.
- **Together adds verbs.** Solo combat has strike/brace/shoot/flee. Company
  adds *guard*, *flank*, *mark for both* — co-op is not two solos running in
  parallel, it is new grammar.
- **The card breathes.** Every time you act, the world has moved: her two
  arrows landed while you wound up. You feel her presence as lines you did
  not write in your own log. If the channel can push, her blows appear live;
  if not, they arrive folded into your next card. Either way the fiction
  holds.
- **The never-wait rule, concretely.** The wolf's turn meter runs per
  player. Kettle answering slowly does not stall you; if she goes quiet, the
  line reads "Kettle falls back into the smoke" and the fight narrows to 1v1
  without a beat of waiting.

## Scene 3 — the flare (the emotional core)

You are at 6 HP, out of medgel, and the wolf is not done. Solo, this is a
death card. On an inhabited floor, one new option exists at the bottom of a
bad fight:

```
[!] Shard flare — every climber on this floor sees it     3 ✦
```

You burn it. On **every** floor-12 card in the world, within the minute:

```
✦ A RED FLARE over the south scarp — a climber is dying there.
[5] Answer the flare                      run toward it
```

And on yours, two rounds later, if someone comes:

```
▪ a horn on the ridge — BRAKKA crashes down the scree, axe first
▪ Brakka takes the wolf's charge on his shield — it staggers
```

Design notes: the flare costs aether so it cannot be spammed; answering one
pays a real reward (gold, aether, and a Stone line — "Brakka answered a flare
on floor 12"); and the dying player's death timer stretches while an answerer
is en route, so rescue is *possible* but never guaranteed. **This single
mechanic produces more stories than everything else on the page combined.**

## Scene 4 — meeting without fighting: the stew pot

Not all presence is combat. The Lodge fire becomes the floor's porch:

```
ROOTHOLLOW · THE LODGE — THE LONG FIRE
Three climbers sit the fire tonight.

· Kettle — sharpening arrows              back from floor 12
· Mox — counting coin, poorly
· a stranger with era-mark ✦✦             twice reborn

[1] Sit — leave a word at the fire        "well fought on 12"
[2] Stand Kettle a stew                   ◈ 2 · +5 HP, hers
[3] Take a room                           ◈ 140 /night
```

No free chat needed — canned words and tiny gifts (a ◈2 stew for someone
else) carry warmth with zero moderation surface. The ✦✦ stranger is
reincarnation doing its real job: being *seen*.

## Scene 5 — the war, when forty show up

The same grammar scaled to a siege — this is what floor-47's warden card
looks like during a rally:

```
FLOOR 47 · SKARNHOLD KEEP
THE WARDEN BLEEDS                          ██████░░░░  61%
the wound closes in 3h 12m — keep striking

▪ your strike lands — −214
▪ Kettle, Brakka, Mox +24 others struck this hour
▪ Redvane leads the damage roll — 9,400 dealt
· the Crier, tower-wide: "47 bleeds. Bring blades."

[1] Strike again                           3 ⚡
[2] Sound the horn                         letter every guildmate
[3] Answer as a pair                       your next strike guards Kettle's
```

The bar, the countdown, the named crowd, the faction scoreboard — the siege
is legible at a glance, which is what turns "please coordinate" into "we are
so close, get in here."

## The reward law (so togetherness is never a tax)

- No kill-stealing exists: contribution split, and **both** players get full
  contract credit for a shared kill.
- An assisted kill pays a small bonus over the sum of two solo kills — the
  system's thumb on the scale toward company.
- Flare answers pay the answerer; guarding pays the guard. Every social verb
  has a selfish reason, so the kind choice is also the smart one.

## The live counter — "hunting here with you: 10 warriors"

Roy's addition: ambient proof that the others are *there right now* — a count
that moves 10 → 9 → 11 like a room, without polling infrastructure.

### Presence is derived, not subscribed

No rooms, no websockets, no sessions. A player's every action already syncs
to worldd; presence is just a **heartbeat read off that** — one indexed count
per floor, cached with a short TTL. The tick down happens naturally when
someone's heartbeat lapses: presence as derived state, decay instead of
disconnect events.

**Roy's rule: the window is 3 minutes, or it isn't multiplayer.** "Hunting
with you" must mean *acted on this floor in the last 3 minutes* — not "got
there and left the game." A stale count is worse than a small one: eleven
ghosts who never answer breaks the illusion harder than two warriors who are
real. The counter's product is **trust**.

Two tiers keep the tight window honest without making floors feel dead:

```
EMBER GULCH — 3 blades hot on this floor · 2 camps smouldering
```

- **Hot** — acted within 3 minutes. These are the "with you" warriors, the
  number that moves 3 → 2 → 4, and the only people a flare targets (they can
  actually answer).
- **Camped** — acted within the hour. Not "with you"; texture. Their fires
  say the floor is lived-on, and their names can still receive a letter.

The natural rhythm protects the hot tier: fight rounds are seconds apart, so
an actually-hunting player never flickers out mid-fight; someone reading a
long card for four minutes drops to camped and returns on their next strike —
"Kettle's torch gutters… and flares again." Implementation is the same
derived query with a tighter bound and a cache TTL shorter than the window
(~30s), so the number can never lag its own promise.

### Two grades of "live", both cheap

**Grade 1 — free, ships with the world payload.** Every card render already
carries world state, so the count rides along: the gate lists "Floor 12 — 11
hunting", the floor header reads "Ember Gulch — 11 torches", and every fight
round refreshes it. In combat you act every few seconds, so during the
moments that matter the number is effectively live — *in a turn-based game,
"live" means "fresh every time you look", and you look by acting.*

**Grade 2 — nearly free, the pane peek.** `/pane/peek` (routes.py:265) is
already a freshness probe with no world round trip. Add one integer to its
response — `floor_presence` — served from the plugin's cached value and
lazily refreshed (at most one world call per player per minute, only while
the pane is actually open). The pane re-renders just that number. Result: the
counter breathes while you idle-watch, which is exactly the "room" feeling,
at the cost of one cached int on an endpoint that already exists.

### The design layer: deltas are story, not UI

A number silently mutating is infrastructure; a number *arriving with a
sentence* is a world. Between your actions, changes fold into your next card
as narrative lines:

```
· two more torches on the ridge since you last looked — 13 hunt Ember Gulch
· Brakka's torch is gone from this floor
```

And the count is not decoration — it is **matchmaking**. Showing "11 hunting"
at the gate makes players cluster on busy floors; clustered floors mean
flares get answered and parties form. The counter causes the encounters the
rest of this document is about.

## Open questions for the ping-pong

1. How much does the wolf scale when a second blade joins — +HP, +a second
   attack, or nothing (fast kills as the reward for company)?
2. Can strangers join your fight uninvited (SAO field-boss style), or only
   flare-answerers and invited friends?
3. Should the flare reach neighbouring floors (±1) so rescue works on quiet
   nights?
4. Party size cap — two feels intimate, three feels like a band, five feels
   like a queue. I would cap at three outside sieges.
5. Does "hunt with Kettle" require her consent tap first, or is hunting the
   same ground consent enough?
