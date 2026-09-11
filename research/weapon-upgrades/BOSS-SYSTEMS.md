# Warden healing and simultaneous attacks

The intended rule is simple: **a warden heals at a known rate, and players defeat it by attacking together faster than it can heal.** Higher floors demand more combined damage. Skilled preparation can reduce the required group or shorten the fight. Pledges and an automatic comparison of accumulated player stats are not the desired mechanic. Accommodating different time zones is not a design objective for this system.

This document records what the code does today and what must change to reach that rule. No boss behavior has been changed by this research.

## What the source currently does

### Ordinary, non-milestone floors

Players encounter a shared HP pool. The engine resolves their individual exchanges, then emits a `warden_strike` effect on departure, death, or victory. The server subtracts that exchange's reported damage from the world pool under a lock. It is not currently a server-side HP decrement for each individual landed hit. Entering the keep is free in the current flow; a damaging swing costs three energy. [B1–B3]

Below floor 31, ordinary wardens do not continuously regenerate. Floors 1–9 have no wound timeout; ordinary floors 11–29 reset after 30 hours of silence. Above floor 30, ordinary wardens heal at 2.7778% of max HP per hour and have a separate silence window. Fully closed wounds reduce the next maximum HP by 3% through a pity counter. These are descriptions of existing rules, not the recommended future simplicity. [B1, B4]

| Ordinary floor | Formula target N at census 200 | Shared HP before pity | HP healed/hour | Reference exchange rounds |
|---:|---:|---:|---:|---:|
| 1 | 1 | 426 | 0 | 19 |
| 9 | 1 | 3,484 | 0 | 14 |
| 11 | 1 | 6,321 | 0 | 14 |
| 29 | 1 | 1,762,759 | 0 | 45 |
| 31 | 2 | 6,268,416 | 174,123 | 32 |
| 49 | 3 | 1,555,629,312 | 43,211,925 | 142 |
| 69 | 9 | 1,320,550,463,016 | 36,681,957,306 | 213 |
| 79 | 16 | 39,504,251,770,880 | 1,097,340,326,969 | 260 |
| 89 | 28 | 1,165,649,627,667,840 | 32,379,156,324,107 | 318 |
| 99 | 48 | 33,524,979,405,318,144 | 931,249,427,925,504 | 387 |

These N values come from economy formulas, not observations of a successful party. The “active” census used in these paths counts rows in `stage='playing'`, not necessarily players available for the current attack. A party recommendation must not silently interpret that count as concurrent players.

### Every tenth floor, including 100

The shared-world keep routes to a war-party board. A pledge spends five energy. The server considers pledges with `world_day >= today − 2`: three world-day buckets, not a precise rolling 72-hour interval. A `(floor, tenant, player)` primary key prevents one account from supplying multiple counted rows for that floor. [B2, B5]

Once the quorum is met, the server reads each participant's current document and computes:

```text
player power = 2 × ATK + DEF + current HP / 4, with integer division
party power = sum(player power)
boss power = 2 × boss ATK + boss DEF + boss HP / 4
win when party power × random factor in [0.9, 1.1] >= 0.75 × boss power
```

This is an automatic resolution. Participants do not need to land concurrent attacks. Current HP matters, but hit timing, the weapon/type interaction during a real encounter, and individual fight decisions are not simulated by this power sum. A loss returns the pledge energy; either outcome clears the floor's pledge rows. Winning floor 100 also closes the era. [B2]

| Milestone floor | Current quorum at census 200 |
|---:|---:|
| 10 | 2 |
| 20 | 3 |
| 30 | 4 |
| 40 | 5 |
| 50 | 6 |
| 60 | 7 |
| 70 | 10 |
| 80 | 17 |
| 90 | 29 |
| 100 | 50 |

This explains why the existing system appears to require many players at the top while still not being the intended simultaneous fight. The combined-stat branch duplicates boss victory logic and bypasses much of the combat engine. Its era completion, participant reward receipts, and historical records are useful infrastructure to reuse; the pledge and auto-resolution rules are not part of the desired design.

## A pre-existing units mismatch

`SUSTAINED_FIGHTS_PER_HOUR = (60 / 45) / 3` treats three energy as one entire reference exchange. The current combat handler instead charges three energy per swing. At floor 31 the exchange unit contains 32 reference rounds; at floor 99 it contains 387. The pool/regen calibration and the real energy cadence therefore operate in different units.

The existing exchange tests explicitly refill energy every round to isolate exchange limits. Their passing would not prove a normal player's sustained damage or a real group's ability to beat regeneration. The coordination tests compare formula-derived full-exchange damage/hour with formula-derived healing/hour, so they do not resolve this discrepancy either. [B6]

This is a source-supported calibration concern, not a reproduced production outage. It should be measured and tracked before a boss redesign. Weapon upgrades should not conceal it by giving one account thousands of times more power or by quietly reducing healing.

## The desired direct-combat model

Each boss has one HP value `H`, maximum HP `Hmax`, and healing rate `R` in HP per second. It also retains its normal attacks and defenses. On a valid landed hit, the server first advances healing from the last timestamp and then applies that player's damage:

```text
H_healed = min(Hmax, H_previous + R × elapsed_seconds)
H_new = max(0, H_healed − accepted_hit_damage)
```

The first transaction reaching zero settles the death once. Further actions see the fallen boss. A read can compute current healing lazily from server time; the UI can animate it between updates. This does not require writing to the database every rendered frame.

Apply hits as they occur. Do not let someone fight privately for minutes and then submit an old damage total as if every hit landed at the same instant. If an internal exchange still collects animation events, authoritative timestamps and damage settlement must retain the real sequence. An abandoned fight cannot bank damage to cash in during another group's attack.

For a late boss, a solo player should have `DPS_solo < R`, while a prepared group has `sum(DPS_i) > R`. Positive net damage is necessary, but finite energy makes another condition essential:

```text
sum(DPS_i) − R >= remaining_HP / available_attack_window
```

A tiny positive margin can still be too slow to finish before energy or HP runs out. Size the pool and healing together against actual burst duration, including misses, counters, range setup, consumable actions, latency, and recovery. A “regenerates every minute” label without this calculation is not enough.

### An illustrative group calculation

These are normalized example units, not replacement floor-100 stats:

| Group | Damage/player/second | Total DPS | Boss regen | Boss HP | Result while the group can attack for 30 seconds |
|---|---:|---:|---:|---:|---|
| One skilled player | 15 | 15 | 300/s | 4,500 | Cannot sustain progress. |
| 40 ordinary prepared players | 10 | 400 | 300/s | 4,500 | Needs 45 seconds; runs out of the modeled burst first. |
| 50 ordinary prepared players | 10 | 500 | 300/s | 4,500 | Wins in 22.5 seconds. |
| 35 skilled, well-prepared players | 15 | 525 | 300/s | 4,500 | Wins in 20 seconds. |

This preserves both intentions: many people attack together, and better play produces a real advantage. No rule needs to count 50 pledges. The number of people is an outcome of damage, healing, and available resources.

The design example assumes continuous rates only to explain the relationship. The implementation must simulate discrete attacks and finite energy. Three energy per swing and the current energy cap imply only a small number of swings in a fresh burst; the actual allowed cadence and animation/request limits determine its duration. Rapid repeated requests must not create more accepted attacks than the combat rules permit.

### Floor progression

Early floors can have slow enough healing for a solo player to learn the loop. Around floor 10, aim to make joint attacking useful and then necessary for appropriate frontier equipment. Increase the target group demand through the tower toward dozens of players at floor 100. This moves cooperative pressure earlier than today's ordinary-floor healing curve and is a boss retune, not merely a new item UI.

Use the current exponential player/gear curve as the scale for HP and healing. Keep money and material costs on their documented curves. Do not directly retain an old pool measured as hundreds of energy-unlimited exchanges and expect it to fit a seconds-long party burst. Calibrate absolute pool anchors and the increasing group factor explicitly.

Fix the reference profile used for tuning. Do not increase boss healing whenever the actual party equips better weapons: that would cancel smart play. Nor should every route have equal success rates. Better counters, healthy arrival, good upgrade choices, and coordinated opening attacks can all matter.

Measure unusually strong legal characters at early frontiers separately. A level-30 character visiting floor 10 is not the at-floor reference profile. Decide whether over-preparing can solo some early gates or whether progression eligibility must bound that case. For late cooperative bosses, verify that the strongest permitted single-player build remains below the healing/energy threshold. Do not claim both arbitrary player power and a guaranteed minimum party size without a rule that actually enforces their relationship.

## What to remove and what to reuse

Remove the pledge-to-autoresolve branch for milestones in the eventual boss implementation. Refund unconsumed legacy pledges once during conversion. Reuse common participant accounting, rewards, memorials, frontier advancement, and floor-100 era closure, triggered by the real death transaction.

Use one healing rule across ordinary and milestone bosses. A separate long silence timeout and repeated full-heal pity are not necessary to explain the intended fight; evaluate removing them in the boss phase, with a snapshot and explicit conversion of active wounds. Nothing in the weapon migration should silently wipe an active warden or change its remaining HP.

Boss materials, if added later, must reward verified contribution to one death event. There is no extra reward for retrying a hit or submitting a duplicate final blow. Ordinary creature materials remain sufficient for weapon progression without depending on a boss drop or a mine.

## Verification required before implementing this direction

1. Reproduce the current energy-limited ordinary fight and the separate milestone flow with real browser players; record the existing behavior without fixing mid-run.
2. Simulate hits in real timestamps for the full floor range, with low, reference, and optimized builds. Check solo failure and feasible group victory at deep floors, including limited energy and unequal player damage.
3. Verify a wound visibly grows while idle and decreases immediately as two browsers land overlapping hits. Staggered low-DPS attacks should fail against a boss that the same players can beat with a coordinated burst.
4. Check server-side hit ordering, idempotency, concurrent kills, disconnect/reconnect, late hits, stale cards, one-time rewards, and exact large-integer arithmetic.
5. Test the actual floor-100 real-fight death path into era closure. A formula or pledge-count test cannot substitute for that scenario.

This is a required direction for a future boss implementation plan. The current task produces research and tables; neither this document nor the weapon reference mapping is evidence that the desired combat system is already present.

## Sources

- **B1.** [Economy and shared-warden formulas](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/economy.py:1255), local checkout 11 September 2026.
- **B2.** [World social engine](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/app/social.py:2080): `_fx_boss_commit`, `_resolve_boss`, `_power`; also `_warden_now`, `_world_warden`, and `_fx_warden_strike`.
- **B3.** [Combat hit/report flow](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/combat.py:1528) and [keep routing](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/core.py:4037).
- **B4.** [Current shared-warden UI and actions](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/plugin_linear_ascent/engine/social.py:1590).
- **B5.** [Pledge table schema](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/migrations/003_social.sql:26).
- **B6.** [Exchange tests](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tests/test_026_the_gate_bites_back.py:55) and [coordination arithmetic tests](/Users/roy/Documents/my-projects-docs/luna-linear-ascent/plugin-linear-ascent/tests/test_022_002_retune.py:84).
