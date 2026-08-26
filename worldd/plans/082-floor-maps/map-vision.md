# 082 — floor-map (Labs)

**The camp menu becomes a map.** Each floor gets a 1-bit map card showing the
gate, the camp, the fields, the Warden's keep — and the floor's three places
of interest, each carrying a quest. Quests are expeditions: paid in energy up
front, cut off from Roothollow, ending at a super monster, paying out in the
prizes the game already has (coin, XP, weapons, armour, potions).

Ships as a **Labs experiment** (`floormap`), gated to floor 1 first.

- Floor-1 plan: `level001-plan/plan.md`
- Look &amp; feel: `mock-map/index.html` (open directly in a browser)

---

## 1. The vision (player-facing)

### The map replaces the menu
Arriving on a floor (or opening the camp card) with the experiment on, the
player sees the floor drawn 1-bit — same discipline as the banners: one ink,
pixelated, no second font, no second size. On it:

- **The gate** — where the lift left them, and the only way off the floor.
- **The camp** (gate-town) — the fire, the healer, the NPC.
- **The fields** — the hunting wilds close to the gate (today's `hunt`).
- **The Warden's keep.**
- **Three places of interest** — already written, floor by floor, in
  `plugin-linear-ascent/vision/lore/floors/floor_NNN.md` under
  "Places of interest", each with a quest seed. The map surfaces them.

Every existing camp option keeps working; it is the same scene wearing a map
instead of a bare list. Rows become markers; markers are still rows.

### Quests — three per floor
Each place of interest carries one quest, difficulty **1 easy / 2 medium /
3 hard** (shown as ▮ / ▮▮ / ▮▮▮). At the end of each quest path waits a
**super monster** — a named boss grown from that place's lore seed (a troll
with its horde, a wyrm, the thing in the sluice-arch). Hard means *harder
than the floor's Warden* — beatable by a strong player, not by the player
who just unlocked the floor. That is intentional: a climber who farms floor
N's fields with ease may only clear the hard quest of a floor several levels
down. **Old floors stay worth riding back to.**

### Expedition rules
1. **Energy is paid once, up front** — the whole quest costs a fixed ⚡ price
   on accept (see §3 ladder). Every fight on the path costs **0 ⚡**.
2. **No road to Roothollow.** While on a quest the town, gate, healer's tent
   and stew rows are gone. The only exits are forward, or back to the gate.
3. **Only what you carry.** No buying. The pack, quiver, oils and the charm
   pouch are the whole kit. Between fights the player may drink what they
   carry; in a fight, pouch law applies as today.
4. **The way back is watched.** Turning back means facing the same number of
   encounters met on the way out. Running away is allowed (existing flee
   mechanics) — but a failed flee hurts, and fled monsters may hunt.
5. **Leaving is safe; the path waits.** Close the game mid-quest and the
   expedition resumes exactly where it stopped.
6. **The hour away.** Returning after ≥ 60 minutes idle triggers one small
   surprise, good or bad, never lethal: a merchant who blessed the errand and
   left a gift; a health mushroom (full heal); a scorpion sting (HP down,
   floored at 1). Small measures only — flavor, not punishment.
7. **All tiers walk every path.** Every quest's encounter table includes the
   floor's whole roster up to its hardest (deep-hunt-tier) creatures; on easy
   quests the hard ones are merely *unlikely*, never absent.

### Prizes
From the systems that exist now: **coin, XP, weapons, armour, potions** —
scaled by difficulty, derived (never authored) per the numberless-content
law. Later, when gathering lands (iron etc.), quests become the natural home
for those rewards too.

---

## 2. What the engine already gives us (research, 2026-08-25)

| Fact | Where |
|---|---|
| Labs registry — per-player flags, floor-gated features, one file names the keys | `plugin_linear_ascent/engine/labs.py` (recipe: add a `Feature`, guard seams with `labs.enabled(p, key, floor)`, tip in `tips.py`) |
| The menu being replaced — `_gate_town_options` / `_gate_town_scene` | `engine/core.py:3439` / `:3808` |
| Places of interest — 3 per floor, with quest seeds, 99/100 floors written | `plugin-linear-ascent/vision/lore/floors/floor_NNN.md` |
| Floor data (numberless YAML: encounters, warden, npc) | `content/floors/floor_NNN.yaml` + `content/schema.py` |
| All numbers derive from economy | `economy.py` — `monster_stats`, `warden_stats`, `gold_per_kill`, `xp_per_kill` |
| Energy: per **action**, never per monster — 1 hunt / 2 deep / 3 warden swing / 5 boss commit; cap 24 base → 34 max; regen 45 min/⚡ lazy | `economy.py:35`, `:517`, `energy_cap()` |
| Existing quest precedent: the contract board (3 world jobs/day, passive progress, dies at dawn) | `engine/contracts.py` |
| Encounter state lives on the doc (`p["encounter"]`), fights resolve in `_resolve_round` | `engine/combat.py` |
| Death sets `floor=0`, teleports to town, no quest hook today | `combat._death` (`combat.py:1897`) |
| All timers are lazy — derived from stored timestamps on next touch; no scheduler | `engine/state.py` (`_regen`, `touch_daily`) |
| Weapon-path triangle: blade does **0** to `fly`; bow glances off `armoured`; staff off `magic_resist` | `economy.py` `TYPE_ATK`, `GLANCE_MULT` |
| Normal monsters drop no items — items come from alphas (10%), wardens (12%), shops, strongbox | `combat.alpha_drop_table` |
| XP is clamped to `gold // 2` on kills — the economy's calibration | `combat._victory` |
| Player doc is one JSONB blob; queryable fields need generated columns | `migrations/022_player_projections.sql` |
| 1-bit art law: one font, one size, ANSI hierarchy, art as mask/SVG | `worldd/static/site/site.css`, `mock/mock.css`, `mock/gmail-door.html` |

---

## 3. Design decisions

**D1 · Labs key.** `Feature("floormap", "Floor-map — the floor drawn, quests on it", …, floors=frozenset({1}))`. Off = today's list menu, untouched. Graduation = widen the floor set, then flip the default and delete the branch, per the labs contract.

**D2 · Energy ladder (the cap is the wall).** The idea was "15 or 40 ⚡" —
but the cap is **24 base, 34 absolute max**, so 40 can never be paid.
Proposed: **easy 8 ⚡ · medium 15 ⚡ · hard 22 ⚡**. Hard deliberately eats
nearly a full bar: taking it *is* the day's decision. New constants
`COST_QUEST = {1: 8, 2: 15, 3: 22}` in `economy.py` — same pattern as every
other `COST_*`.

**D3 · Path length by difficulty.** Easy **3** encounters + boss, medium
**5** + boss, hard **7** + boss. With 0 ⚡ per fight, the up-front price is
the whole price; length is the risk knob (HP attrition, no healer).

**D4 · Content home.** A `places:` block joins the floor YAML — three
entries: `id, name, prose, quest_title, difficulty (1-3), boss {id, name,
prose, kind, traits}`. Prose comes from the lore files' Places sections.
**Numberless law holds**: no stats in YAML; `schema.py` lint extends to
validate places (exactly 3, one per difficulty) on floors that have them.
Each place carries an `objective` field, `boss` for now — the enum is
**reserved for `gather` (iron etc.) and other non-combat objectives** so
the collecting future lands as data, not a schema break.

**D5 · Derived numbers.** In `economy.py`:
- `quest_boss_stats(floor, d)` = `warden_stats(floor)` scaled by
  d1 ≈ (0.55 HP, 0.8 ATK) · d2 ≈ (1.0, 1.0) · d3 ≈ (**1.7 HP, 1.25 ATK**) —
  hard is provably worse than the Warden.
- `quest_gold(floor, d)` ≈ `gold_per_kill(floor)` × {d1: 8, d2: 18, d3: 40}.
- `quest_xp = quest_gold // 2` — respects the global XP clamp.
- Item prize by difficulty: d1 consumables (medgels), d2 a trauma kit +
  coin, d3 a **gear piece one tier above the floor's band** + a trollblood
  tonic. Path kills additionally pay normal per-kill gold/XP.

**D6 · Boss killability.** Bosses never carry `fly` / `armoured` /
`magic_resist` — a hard wall for one weapon path would make a quest
uncompletable by a third of players. Body/bite traits only (`hulking`,
`savage`, …). Lint enforces it.

**D7 · Quest state.** `p["quest"]` on the doc, sibling of `p["encounter"]`:
`{floor, place, difficulty, path_len, step, met, fled, state:
out|at_boss|returning, started_ts, last_ts}`. Survives dawn (unlike
contracts), survives logout. `state.ensure_current` bumps doc version and
heals old docs. Not queryable — fine for Labs; a projection column only if
admin needs it later.

**D8 · Death voids the quest.** `combat._death` gains one line: clear
`p["quest"]` (energy already spent stays spent — the expedition failed).
Death already teleports to town/floor 0, which would otherwise strand an
"on the path" flag.

**D9 · The way back.** `met` counts encounters resolved outbound. "Turn
back" enters `returning` with `met` fights to clear; each may be fought or
fled with the existing `run` mechanics (flee chance, grab damage on fail).
**Fled monsters hunt:** each outbound flee is remembered (`fled` list) and
that same creature re-ambushes on the return path — first fight back, no
flee option on the re-ambush. "Might get hunted" is literal, not just flee
damage. Reaching the gate clears the quest as *abandoned* — no prize, no
refund.

**D10 · The hour away.** Lazy, like everything: on the first quest touch
with `now - last_ts ≥ 60 min`, roll one surprise (50/50 good/bad), apply,
show it as the card's headline. Good: merchant's gift (a potion or oil
charges) with the blessing line; health mushroom (HP → full). Bad: scorpion
sting (HP × 0.6, floor 1); a gnawed pack (small carried-gold loss). Never
kills, never touches energy, never repeats (stamp `last_ts`). The
merchant's gift can be **gear** — a sword one tier at-or-below the floor's
band ("gave a sword and blessed you"), weighted rare next to potions/oil.

**D11 · Map art.** A **model-painted 1-bit map** per floor, the banner
pipeline (`tools/generate_banners.py`) map-shaped: Gemini paints a
high-angle aerial view — sculpted 3D volumes with lit faces and cast
shadows, never flat icons or line drawings; **territory scale** (roy,
2026-08-26): the map shows ~1000 acres, a whole district from altitude —
forests as canopy masses (not trees), a mountain range (not a slope), a
river artery, massive field systems; landmark buildings stay small,
drawn ON TOP of the terrain the way map landmarks are, each catching
light with its own shadow; the gate at the very center;
terrain running past all four edges (the floor is far bigger than the map);
each place of interest composed into the scene; **the gate is the
elevator** — a colossal lattice pylon at the map's center, cables rising
out of the top edge toward the floor above — then forced to spec: crop
4:3, downscale to **640×480 native**, gamma to ink-on-black, Bayer 8×8
ordered dither, exactly two states, ink `--art`. The scene is dithered,
the UI is typography: **every menu option is a marker chip on the map** —
`[n] NAME` (one/two words), gold = quest, hover inverts, selected =
reverse-video bright, and each chip carries a **one-line tooltip** saying
what the place holds (quests spell difficulty in words — "difficulty:
hard", no bars — plus what to expect and the loot); chips carry `data-opt`
like every other row. No separate option list below the map. Floor 1's generator is
`mock-map/map_gen.py` (+ `raw_map.png`); graduates to
`tools/generate_maps.py` when floors 2+ come. Delivered as a `Scene.map`
asset rendered by `render.py` / `pane.py`.

**D12 · Names.** Canon spelling is **Roothollow** (not Rothhollow).
"The fields" on the map means the floor's wilds; beware the existing
Roothollow PvP location also named `fields` (`core.py:1398`) — the quest
code never reuses that key.

---

## 4. Difficulty tuning (the back-tracking curve)

Anchors, floor 1 (warden = ATK 15 / DEF 3 / HP 70):

| Quest | Boss ≈ | Meant for |
|---|---|---|
| ▮ easy | ATK 12 / HP 39 + 3-fight path, no healer | the floor's own hunter, slightly brave |
| ▮▮ medium | warden-grade + 5-fight path | a player who has beaten Brackjaw |
| ▮▮▮ hard | ATK 19 / HP 119 + 7-fight path | a climber from floors above, riding back down |

Rule of thumb to hold across floors: **hard(N) ≈ comfortable for a player
whose fields-farm floor is N+4.** Verified per floor with the sim harness
before enabling that floor's maps.

---

## 5. Open questions

1. Sleep mid-quest — allowed on the path (rough, 1.5×) or only at camp?
   Leaning: allowed; it feeds the hour-away system naturally.
2. Repeatable quests — once per world-day? Once per frontier-era? Leaning:
   repeatable with a per-quest daily lock (`p["daily"]`).
3. Do flares fire from a quest path (a dying quester broadcasting)?
   Leaning: yes later, out of scope for v1.
4. Quest completion as a shared happening (`ascent_happenings`) — yes, cheap.
5. Marker art on mobile widths — the mock answers layout; verify at 360 px.

---

## 6. Rollout

1. **v1 (this plan):** Labs `floormap`, floor 1 only — map card, 3 quests,
   expedition loop, hour-away, prizes. `level001-plan/plan.md`.
2. **v2:** floors 2-10 (places blocks + maps), tuning pass on the ladder.
3. **v3:** floors 11+ blocked on the lore/YAML re-sequencing debt
   (shipped floors ≥ 11 still run the old biome order — see
   `world-lore.md` §8); maps must wait for re-sequenced floors.
4. **Graduate:** flip default on, delete the labs branch, delete the key —
   the labs contract's promotion path.
