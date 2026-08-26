# 084 / 01 — the opener is the sheet, nothing else

## Preconditions
- Local worldd on :8600 with the 084 engine (0.106.0), Postgres seeded.
- A player able to start a wilds hunt (energy topped up as needed —
  precondition management, not gameplay).

## Scenario
1. Log in, walk to a floor gate, start a hunt to a fresh encounter
   opener (desktop 1280px viewport).
2. Read the whole opener card top to bottom; screenshot.
3. Hover/click the [i] on the stat slab over the creature art; verify
   the dossier panel opens; screenshot.
4. Dismiss the swap hint with ✕; act once (attack) to reach a round
   card; screenshot it.
5. Repeat step 1–2 on a mobile viewport (390×844, touch).

## Expected behavior
- The opener shows ONLY: the creature art with the black stat slab
  (HP/ATK/DEF/SPEED **and the [i]** at its right), the grey floor bar
  reading "FLOOR N · <PEOPLE> · <PLACE> · <MONSTER NAME>", the foe
  sheet, the gold swap-hint bar (until dismissed), and the option rows.
- No headline name line, no ◇ status lines, no "It is between you and
  the way forward.", no sidekick whisper, no description prose, no
  "You — ATK …" line.
- The foe-sheet cells sit in ONE row: solid dark-grey cells, no
  outlines, white label + hint text, colored type icons.
- The [i] opens the same dossier panel as before (range verdicts live
  there now).
- Round cards after the first strike are unchanged from 083 behavior
  (their own prose/feedback intact).
- Mobile: the one-row sheet fits 390px with no horizontal scroll.

## Fail conditions
- Any of the removed text blocks still renders on an opener.
- The [i] is missing, dead, or the dossier no longer opens.
- The floor bar lacks the monster name, or the name renders twice.
- Foe-sheet cells stack in a grid/second row on desktop, or overflow
  horizontally on mobile.
- Round cards lost their prose or the mid-fight swap-refusal line.

## Verify
- Fragment HTML from `/play/api/act`: no `class="headline"` /
  `class="ehead"` / `class="support"` on the opener; exactly one
  `class="info"` inside `class="estat"`; eyebrow text ends with the
  monster name; `.foesheet` computed style is a single flex row.
- After ✕: doc flag `foehint_done=true`; hint absent on the next
  opener.
- Round-card fragment still carries its body/feedback lines.
