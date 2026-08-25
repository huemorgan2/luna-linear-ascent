# 081 phase-4 — the level-up explainer box

## Goal

Level-1 players see, in their profile block directly under the XP rail, a
small dismissable box:
`LEVEL UP — XP {xp}/{need} + ◈ {fee} — the Guildhall levels you up`
with live computed numbers (24 XP / ◈ 60 for 1→2 — never hardcoded
copy). ✕ dismisses it and the dismissal survives every card re-render
and page reload; it stops rendering entirely at level ≥ 2. Measurable:
dojo scenario 04.

## Steps

1. **Render** (both copies): in `_profile_html`
   (render.py:1048-1081), between `right = _meters_html(m)`
   (render.py:1050) and the ATK pip-row block (render.py:1051), when
   `m.level == 1`:
   ```python
   fee = economy.levelup_gold(m.level)
   right += (f'<div class="lvlhint" data-hint="levelup">'
             f'<b>LEVEL UP</b> — XP {m.xp}/{m.xp_need} + ◈ {fee:,} — '
             f'the Guildhall levels you up'
             f'<button type="button" class="x" aria-label="close">✕</button>'
             f'</div>')
   ```
   `m.xp` / `m.xp_need` / `m.level` are already on `Meters`
   (scene.py:53, populated at combat.py:135); the fee is computed
   render-side (`economy.levelup_gold`, economy.py:1045) — no `Meters`
   field added, no wire change.
2. **CSS**: `.lvlhint` next to `.piprows` (render.py:3499-3507) — small
   bordered box, the notices' aether ink (see `.notices` at
   render.py:2994-3018), `position:relative` for the ✕.
3. **Dismissal** (`pane.py`, both copies): the card is server-rendered on
   every act, so dismissal is client-enforced. Use the `la_ntf_seen`-style
   store from phase 3 (or its own `la_tip_levelup` boolean via the
   blessed `plyStore` copy, pane.py:1203-1211). Hook where the fragment
   is injected into the DOM (`showScene`): after every swap, if the key
   is set, remove `.lvlhint`; delegate the ✕ click to set the key and
   remove the box. If phase 3 lands first, reuse its store.
4. **Consistency with the Guildhall**: the drillmaster's line
   (engine/social.py:315-329) and `guild_train` (engine/social.py:910)
   already quote the same `xp_need`/`levelup_gold` — no change needed,
   just verify the numbers match in the walkthrough.
5. **Tests**: worldd `test_web_play.py`-style render assertion — level-1
   fragment contains `lvlhint` with `24` and `60`; level-2 fragment does
   not contain `lvlhint`.
6. **Vendor sync**: submodule first, then `worldd/vendor` + parent
   pointer; bump the pane/render version param in `app/webplay.py` if
   stamped.

## Verification

- Targeted render test, then both full suites.
- Manual: fresh level-1 player — box shows under the XP bar with 24/◈60;
  fight once (card re-renders) — box persists; ✕ — box gone; act again
  and reload — still gone; level up at the Guildhall — box never returns
  even in a fresh browser (server stops emitting it).

## Rollback

Revert the commit. The localStorage key is inert without the element.

## Execution status

Executed 2026-08-25.

1. `render._profile_html`: level-1-only `.lvlhint` box quoting live
   computed numbers — `XP {m.xp}/{m.xp_need}` + `◈ {levelup_gold(1):,}`
   ("the Guildhall levels you up") with a ✕ close button; aether-ink CSS
   added. No folklore constants in the copy.
2. Client (pane.py): generic `[data-hint]` sweep — `hintSweep()` runs on
   every scene swap, removes boxes whose `la_tip_<name>` localStorage key
   is set, wires each box's ✕ to set the key and remove the element.
   Reusable for phase-6's foe hint.
3. Tests: `tests/test_081_levelup_hint.py` — the box quotes XP 7/24 and
   ◈ 60 from economy (asserted equal to the computed values), levels
   2/3/10 never render it. 2 passed.
4. Suites: plugin at baseline, worldd 221/221 (phase-3 run covers this
   commit range). Vendor synced. Deploy rides phase-7.
