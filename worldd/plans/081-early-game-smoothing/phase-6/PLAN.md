# 081 phase-6 — the encounter card reads at a glance: type icons + swap at the sizing-up

## Goal

A new player looking at an encounter card understands in one glance what
kind of monster this is and which weapon answers it — big type icons with
numbers instead of the current wall of verdict prose — and can actually
switch to the right weapon from the pack at the encounter (sizing-up)
phase instead of being told "nothing this one can do in the middle of
this". Measurable: dojo scenario 06 — a tester shown only the card names
the monster's type and the right weapon in under 5 seconds; a pack
weapon equips from the opener card.

## Current state (mapped 2026-08-25)

- The encounter card IS `fight_scene` with `opener=True`
  (combat.py:786; entry combat.py:232-310). Opener body_lines today:
  prose, "You — ATK … DEF …" (combat.py:919-922), the type triangle
  line `economy.type_line` (combat.py:924), and 1-3 `_verdict` prose
  lines (combat.py:753-783). That prose is what the user wants gone.
- Monster fields: `profile["type"]` ∈ fly/armoured/magic_resist/plain,
  `profile["flying"]`, `profile["speed"]` (`TYPE_SPEED` economy.py:700),
  flat `e["def"]` (combat.py:296). Magic resistance has NO number — it
  is the type; display % derives as
  `round((1 - TYPE_MULT[t]["staff"]) * 100)` (arena.py:285-286 precedent).
- Best-weapon truth (`TYPE_MULT`, economy.py:713-718):
  fly → bow full / staff 0.6 / blade zero; armoured → staff full
  (staff also ignores flat DEF, economy.py:918) / blade half / bow
  glances; magic_resist → blade full / bow half / staff glances;
  plain → everything full.
- Icons exist keyed by type: `_ARENA_TYPE` (render.py:2203-2208) maps
  type → (icon key, ink, word) over 16×16 masks (icons.py t_wing:426,
  t_armor:388, t_resist:407, t_speed:445); masks already scale to
  32/56 px elsewhere (render.py:3298, 3335). Per-type plain-English
  tips exist (`_TIP_KIND`, render.py:2223-2233). No-emoji law:
  render.py:292-317.
- Mid-fight pack lockout: core.py:372-384 ("Nothing this one can do in
  the middle of this.") and the dispatcher guard core.py:509-520
  ("you don't re-rig your hands with teeth in your face"). Switching
  between HELD weapons mid-fight already exists (`attack_{slug}` rows,
  `_promote_held` combat.py:1280-1306).
- Dismissable-box precedent: the Crier's paper — `data-opt` ✕ button
  (render.py:417-419) + server-side flag (`p["news_day"]`,
  core.py:643-645). Dismissal is a doc flag, not localStorage.

## Steps (engine — submodule first, then vendor + pointer)

1. **Structured type block replaces the verdict prose (opener only).**
   In `fight_scene`'s opener branch (combat.py:912-925): keep
   `e["prose"]` and the "You — ATK/DEF" line; DROP the
   `economy.type_line` line and `_verdict` prose. Attach instead
   `scene.foe_sheet` (new Scene field, additive, default None), built
   from the profile:
   - `def`: `{"n": e["def"], "best": "magic"}` — staff ignores flat DEF.
   - `fly`: `{"yes": profile["flying"], "best": "bows and magic"}`.
   - `resist`: `{"pct": 99 if type=='magic_resist' else 0, "best":
     "swords"}` (arena.py:285 derivation).
   - `speed`: `{"n": profile["speed"], "closes": speed >= player speed}`
     (`_mspd` combat.py:372 vs `state.spd(p)`).
   Non-opener rounds keep today's compact body (user asked about the
   encounter; round cards stay dense for veterans).
2. **Render the block big** (render.py, near the enemy head): a
   `.foesheet` row of up to 4 cells, each a 32 px tinted mask icon
   (reuse `_ARENA_TYPE` inks/keys + `t_speed`) over one bold line:
   `DEF 12 — best weapon: magic` / `FLY — YES — best: bows and magic` /
   `MAGIC RES 99% — best: swords` / `SPEED 7 — closes distance fast`.
   Only truthy cells render (a plain walker shows DEF + SPEED and a
   "no sign — every weapon bites full" cell). Grey the "best" hint on
   the cell the player's held weapon already answers. CSS next to the
   dossier styles (render.py:2936-2969); mobile: 2×2 grid, no
   horizontal scroll.
3. **Dismissable swap hint** under the sheet:
   `You can switch to the proper weapon from your pack ✕` — paper
   pattern: ✕ is `data-opt="foehint_close"`, engine handles the option
   by stamping `p["foehint_done"] = True` (no scene change, current
   card rebuilt), box renders only while the flag is unset. Server-side
   flag ⇒ survives reloads and other devices, mirrors news_close
   (core.py:643-645).
4. **Weapon swap at the encounter phase.** Relax the two guards for
   weapons only, while the fight has not begun —
   `e["range"] == "at_range" and not e.get("attacked") and not
   e.get("shot_used")` (the same predicate that gates the treeline
   shot, combat.py:885-886):
   - `pack_actions` (core.py:375-384): in that window, weapon slugs get
     their normal Hold row (hint "swap before the steel meets");
     everything else keeps the lockout line.
   - dispatcher guard (core.py:509-520): allow `wear_{weapon}` in the
     same window; route the equipped weapon through `_promote_held`'s
     bookkeeping so durability stashing stays consistent; return the
     rebuilt opener card (foe sheet + new "You — ATK …" line reflects
     the swap). Once the fight has begun the old refusal stands —
     re-rigging mid-melee stays forbidden.
   - The opener card gets one row `Option("pack", "Open your pack",
     "swap weapons while you still can")` so the pack is reachable
     without leaving the card; pack return path comes back to the
     fight card, not town.
5. **Copy drift fix (adjacent, one line):** render.py:1350-1351 says
   "×0.6 in this press" while `BOW_CLOSE_MULT = 0.5` (economy.py:570)
   — print the constant, not folklore.
6. **Tests** (plugin suite, `tests/`):
   - foe_sheet payload correct per type (fly/armoured/magic_resist/
     plain) incl. resist pct and closes flag; absent on round cards.
   - verdict prose gone from opener body_lines; prose + You-line stay.
   - `wear_` weapon accepted at the sizing-up, refused after
     `attacked`/`shot_used`/close quarters; durability stash intact
     after swap (reuse `_promote_held` test patterns).
   - `foehint_close` sets the flag; box absent after.
   - Replay determinism: swap consumes no RNG draw (rng_counter
     unchanged).
7. **Vendor sync** + parent pointer bump.

## Verification

- Targeted plugin tests above, then full plugin + worldd suites.
- Manual: fresh L1, first wilds encounter — screenshot desktop + mobile
  (2×2 grid, icons legible, no overflow); swap Rusted Shiv → bow from
  the opener vs a flyer, verdict line updates, fight proceeds; after the
  monster attacks, the swap refusal returns.
- Dojo scenario 06 (phase-7 run).

## Rollback

Revert the commit(s). `foe_sheet` is additive on Scene (old clients
ignore it); `p["foehint_done"]` is a harmless orphan flag; no
migration.
