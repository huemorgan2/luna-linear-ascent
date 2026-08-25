# 02 — beginner pity: misses never stack past your level

## Preconditions
- Player fresh at level 1, training rank 0 (25% base miss), on floor 1.
- A second character raised to level 4, rank 0 (control).

## Scenario
1. As the level-1 player, fight monsters and attack repeatedly across
   several encounters — at least 60 attack rounds. Record every round's
   outcome (the card's miss line / hit damage; the arena's MISS float is
   corroborating).
2. Repeat ~60 rounds as the level-4 control.

## Expected behavior
- Level 1: single misses occur (the 25% rate is alive), but NEVER two in
  a row — every miss is followed by a hit.
- Level 4: at least one streak of ≥ 2 misses appears over 60 rounds
  (probability of none is tiny) — pity does not leak upward.
- Forced hits look like ordinary hits: normal damage line, no special
  "mercy" copy mid-fight.

## Fail conditions
- Two sequential misses at level 1 (or 4 at level 3 if spot-checked).
- Level ≥ 4 player never missing twice in a row across the full sample
  (suggests pity applied globally).
- Any crash/refusal on the attack option, or the miss counter visibly
  surviving into a new fight (first swing of a fresh encounter behaving
  as forced).

## Verify
- Tally from the recorded rounds: max consecutive misses per level.
- Plugin test suite green, including the replay-exact tests
  (test_048_the_weapon_decides.py, test_smoothness.py) at the deployed
  SHA.
