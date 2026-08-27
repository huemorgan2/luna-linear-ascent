# 082 phase-1h — the number keys reach the map chips (roy, 2026-08-27)

## Goal

The map chips wear `[1]..[5]` but pressing those keys does nothing:
the 041 number-row handler in `pane.py` clicks `button.opt` rows by
DOM index, and on the map card the mapped options are chips
(`button.mk`), not rows. Roy: "the new map doesnt support key strokes
[1] for the one key and so on.. fix and deploy."

Measurable: on the map card, pressing "4" opens the GATE lobby (the
chip labeled `[4]`); rows on non-map cards keep working; dojo re-walk
PASS with a new keystroke check. Deploy to live.

## Approach

Both button kinds already PRINT the right number from scene.options
position — rows `<span class="key">{i}</span>`, chips
`<span class="mknum">[{i}]</span>` ("numbered by the option's position
… so the typed-number fallback never notices the layout" — the render
half was built; the pane half never learned about chips). So the
handler stops indexing DOM order and matches the DISPLAYED number
across `button.opt, button.mk`; buttons printing no number keep the
old DOM-order fallback.

## Steps

1. `pane.py` 041 keydown handler: query
   `button.opt, button.mk` (visible, enabled), pick the one whose
   `.key`/`.mknum` digits == the pressed key; fall back to DOM order
   among numberless buttons.
2. `version.py` → 0.110.3. Vendor sync.
3. Tests: extend `test_041_qol.py` pane-script assertion to the chip
   selector; targeted 041 + 082 suites.
4. Dojo: walkthrough gains a keyboard check (press "4" at the map →
   gate lobby, back) — results folder 0061.
5. Deploy (`deploy.sh`), post-deploy prod verification includes the
   keystroke.

## Verification

- `test_041_qol.py`, `test_082_floormap.py` green.
- Dojo run 0061 PASS incl. the new keystroke check.
- Prod: live 0.110.3; keystroke "4" navigates on the live map card.

## Rollback

Revert the phase-1h commits, vendor re-sync, redeploy (the handler
returns to rows-only; chips stay clickable by mouse/touch).
