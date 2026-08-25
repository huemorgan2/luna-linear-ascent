# 05 — item stats on tap, an honest pawn broker, a visible [HOLD]

## Preconditions
- Fresh level-1 player: starter weapon (Rusted Shiv or class variant) in
  hand, gate armor worn, at least one FORGE weapon AND one sellable item
  (e.g. medgel) in the pack, plus a gate piece moved to the pack.
- Walk once on desktop, once on a mobile viewport (touch emulation).

## Scenario
1. On the profile gearmap, click/tap the held starter weapon, the worn
   gate armor, and (if worn) a charm. Screenshot each popup.
2. Open the pack and click/tap a weapon there. Screenshot the popup and
   its action rows.
3. Choose the hold/equip action and confirm the weapon moves to hand.
4. Go to the pawn shop with the rusted starter weapon and a gate piece
   in the pack. Screenshot the shop card.
5. Sell the legitimately sellable item as a control.

## Expected behavior
- Every popup for a stat-bearing item opens with the item name and its
  parameters right under it — ATK (weapon), DEF (armor), durability —
  on desktop AND mobile; the starter bow / gate armor specifically show
  their real numbers (ATK 5 / DEF 7), not a bare name.
- Items with no numbers (some charms/potions) show their effect line or
  simply omit the stat block — never a broken/empty row.
- The equip action reads as an option: `[HOLD] — move to hand`
  (gold-bracketed key, consistent with the card's numbered rows), and
  works.
- The pawn shop card plainly says the broker won't take the rusted
  basics and gate steel (naming them), lists NO ◈ 0 offer rows, and the
  control sale pays the quoted rate.
- Desktop hover tooltips behave as before.

## Fail conditions
- Any popup where a FORGE item shows no stats (the original report).
- Mobile tap showing a tooltip that instantly vanishes under the menu,
  or requiring hover to see numbers.
- A ◈ 0 sell row, or the rusted weapon silently ignored with no
  explanation anywhere on the pawn card.
- "Hold" still rendered as plain text, or the restyle breaking other
  popup actions (Wear, Move to the pack, repair rows).
- Popup layout overflow on a narrow viewport.

## Verify
- Fragment HTML: gearmap cells carry `data-params` with the stat spans;
  pawn scene body contains the waves-off line naming the excluded
  items; popup template renders `.key`-bracketed action labels.
- Ledger after step 5: exactly one sell row at the day's pawn rate; no
  ledger rows from the refused items.
