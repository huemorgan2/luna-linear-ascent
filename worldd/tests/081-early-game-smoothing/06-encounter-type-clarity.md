# 06 — the encounter card explains the monster and lets you re-arm

## Preconditions
- Fresh level-1 player with a melee starter weapon held AND a bow (or
  staff) in the pack.
- Floors reachable that spawn each type: armoured (floor 2+),
  magic_resist (floor 3+), fly (floor 4+) — level/gear the player as
  needed to walk there safely.
- Desktop and a mobile viewport.

## Scenario
1. Trigger a wilds encounter. Screenshot the opener card.
2. Without scrolling or hovering, note what the card says about the
   monster's qualities and which weapon is recommended.
3. Click the pack / swap affordance ON the encounter card and equip the
   bow. Screenshot the returned card.
4. Let the monster act once (or shoot), then try to swap weapons again.
5. Dismiss the "switch to the proper weapon" hint with its ✕, finish
   the fight, trigger another encounter, and reload the page.
6. Repeat step 1-2 against one monster of each type: plain, armoured,
   magic_resist, fly.

## Expected behavior
- The opener shows a big-icon stat sheet, not paragraphs: DEF with a
  number (best weapon — magic), FLY YES (best — bows and magic),
  MAGIC RES with a % (best — swords), SPEED with a number and "closes
  distance fast" when it is fast — only the cells that apply, with the
  monster's prose line still above. The old multi-line verdict prose is
  gone from the opener.
- Numbers match the dossier/arena values for the same creature; the
  "best weapon" hints match the damage triangle (a flyer really is
  immune to the blade, etc.).
- Swapping from the pack works at the sizing-up moment: the card
  returns with the new weapon in the You-line, no round consumed, no
  red banner.
- After the fight has begun (monster attacked / shot fired / close
  quarters), the swap is refused with the existing "re-rig" line — not
  silently ignored.
- The ✕-dismissed hint stays gone: next encounter and after reload the
  sheet renders without the hint box (server-side flag).
- Mobile: 2×2 icon grid, readable, no horizontal scroll.

## Fail conditions
- Verdict prose still on the opener, or the sheet ALSO appearing on
  every round card (it is opener-only).
- A wrong pairing (e.g. "best weapon — swords" on a flyer) — file as
  severe: this is the exact confusion the phase exists to kill.
- Emoji glyphs instead of the tinted masks (no-emoji law).
- Swap possible after the fight began, or the swap eating durability /
  duplicating a weapon (check the pack after).
- Hint box resurrecting after ✕ + reload.
- Fly shown as a number, or MAGIC RES shown on a non-resistant monster.

## Verify
- Fragment HTML: `.foesheet` present on the opener fragment, absent on
  a round fragment; icon cells are mask `span`s, not `<img>`/emoji.
- Doc after ✕: `foehint_done: true`; after weapon swap mid-sizing-up:
  gear.weapon changed, old weapon in inventory with its durability
  stashed exactly as `_promote_held` does for held swaps.
- Replay tests still green (swap consumes no RNG draw).
