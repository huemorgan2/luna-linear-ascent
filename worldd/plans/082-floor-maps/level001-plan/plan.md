# 082 · level001 — the Fencerows, mapped

## Goal

Floor 1 gets the floor-map experiment end to end: a Labs toggle (`floormap`,
floor 1 only) that replaces the Lamplit Steading menu with a 1-bit map of the
Fencerows carrying the gate, the camp, the fields, Brackjaw's keep and the
three places of interest — each with a working quest (accept → paid path →
boss → prize → walk home), including the no-Roothollow lockout, the watched
way back, resume-after-leaving, and the hour-away surprise. Measurable: all
three quests completable in play, full worldd + plugin suites at baseline,
dojo scenarios below all PASS.

## The three quests (from `vision/lore/floors/floor_001.md`)

| # | Place | Quest | Diff | ⚡ | Path | Boss |
|---|---|---|---|---|---|---|
| 1 | **Mother Ditch** | *The Thing in the Sluice-Arch* | ▮ easy | 8 | 3 fights | **The Sluice Maw** — the something big that dens in the sluice-arch; a drowned, bloated marsh-thing (wrongmade; hulking, sturdy). ≈ ATK 12 / HP 39 |
| 2 | **The Burnt Steading** | *The Hearth-Shard* | ▮▮ medium | 15 | 5 fights | **The Char-Troll** — a troll denned in the black timbers, its goblin band (pressed stragglers) walking the path ahead of it. ≈ warden-grade: ATK 15 / HP 70 |
| 3 | **Fairstone Green** | *The Fair-Day Wyrm* | ▮▮▮ hard | 22 | 7 fights | **The Fair-Day Wyrm** — a young drake coiled on the market cross where the fair once stood. Worse than Brackjaw: ≈ ATK 19 / HP 119 |

Narrative payoffs follow the lore seeds: the shard relit under the
threshold-stone, the fair-green won back, the fords of the ditch made safe.

Path encounter tables: the floor's full roster including `ember_shade`
(deep-tier); weights by difficulty — easy ≈ {feeble/lean 70, peers 25,
ember_shade 5}, medium ≈ {40, 45, 15}, hard ≈ {20, 50, 30}, no rubber band
on hard, alpha specimen odds doubled on hard.

Prizes (derived, floor 1): easy ◈ ≈ 130 + 2 medgel · medium ◈ ≈ 290 + trauma
kit · hard ◈ ≈ 640 + a **tier-2 gear piece** + trollblood tonic. XP = gold
// 2 everywhere. Path kills pay normal per-kill gold/XP on top.

## Phasing (roy, 2026-08-26)

**Phase-1 ships the map WITHOUT quests** — the places and actions the game
already has, labs-isolated (`floormap` / "Floor maps", floor 1). Cost-on-chip
rule: a marker whose click has a real cost wears it on the chip in the cost's
color (HUNT `1 ⚡`); Brackjaw's chip does not (his keep screen prices the
swing). Map art is territory-scale: ~1000 acres, forests not trees, a
mountain range, massive field systems; landmark buildings drawn small ON TOP
of the terrain, map-style. See `phase-1/PLAN.md`. The quest content below is
phase-2+.

## Steps

All engine edits land in `plugin-linear-ascent/plugin_linear_ascent/` and are
**vendor-synced** into `worldd/vendor/plugin_linear_ascent/` (both places, as
always). Commit the plan before executing.

1. **economy.py** — `COST_QUEST = {1: 8, 2: 15, 3: 22}`,
   `QUEST_PATH_LEN = {1: 3, 2: 5, 3: 7}`, `quest_boss_stats(floor, d)`,
   `quest_gold/xp(floor, d)`, `quest_prize(floor, d)`,
   `QUEST_AWAY_MIN = 60`, surprise table.
2. **content/floors/floor_001.yaml** — add `places:` block (3 entries:
   id, name, prose, quest_title, difficulty, boss{id,name,prose,kind,traits}).
   No numbers (lint enforces).
3. **content/schema.py** — `Place` dataclass, loader, lint: exactly 3 places
   where present, one per difficulty, boss traits exclude
   fly/armoured/magic_resist, prose caps.
4. **engine/labs.py** — register `Feature("floormap", …,
   floors=frozenset({1}))`; tip in `tips.py` (`labs_toggle_floormap`).
5. **engine/quest.py** (new module, labs-isolation contract: deletable) —
   accept (spend ⚡, init `p["quest"]`), path step (0 ⚡ encounters via
   `combat.start_encounter`), boss step, turn-back/returning logic (`met`
   fights, flee allowed), completion + prize payout, abandonment at the
   gate, hour-away roll (lazy off `last_ts`).
6. **engine/core.py seams** — in `_build_scene`/`_gate_town_scene`: when
   `labs.enabled(p, "floormap", fl.floor)` render the map scene; while
   `p["quest"]` is live suppress `town/gate/heal/stew` options and route
   `quest_*` option ids to `engine/quest.py`. `combat._death`: clear
   `p["quest"]`. `combat._victory`: notify quest step.
7. **engine/state.py** — doc version bump; `ensure_current` heals missing
   `quest` key (None).
8. **Scene/render/pane** — `Scene.map` field (+ serialize round-trip),
   `render.py` emits the 640×480 1-bit PNG (`image-rendering: pixelated`)
   with an HTML overlay where **every option is a `[n] NAME` marker chip**
   (gold = quest, hover invert, reverse-video selected, `data-opt`) with a
   one-line tooltip — what the place holds, difficulty in words, no bars;
   no option list below the map. `pane.py` CSS for the map block. Floor-1 art:
   Gemini aerial paint → dither via `../mock-map/map_gen.py` (graduates to
   `tools/generate_maps.py` for floors 2+); layout from
   `../mock-map/index.html`.
9. **Vendor sync** — copy plugin → `worldd/vendor/`, plugin pointer update.
10. **Dojo scenarios** — write `luna/dojo/tests/082-floor-maps/` (below).

## Verification

- Targeted: new `tests/test_082_floormap.py` (plugin) — labs off ⇒ scene
  byte-identical to today; accept spends exactly COST_QUEST and refuses when
  short (refusal string, no partial spend); path fights spend 0 ⚡; town/gate
  rows absent mid-quest; turn-back queues exactly `met` fights; resume across
  save/load; hour-away fires once at ≥ 60 min and never drops HP below 1;
  death clears the quest; hard boss stats > `warden_stats(1)`; prizes match
  the derived numbers; lint rejects a numeric key and a `fly` boss.
- Full suites: `worldd` pytest (baseline 215/0) and plugin pytest — at or
  under baseline failures (0).
- Dojo (mandatory before reporting complete), scenarios in
  `luna/dojo/tests/082-floor-maps/`:
  1. *map-replaces-menu* — toggle labs on, floor 1 shows the map, every old
     action reachable from it; toggle off restores the list.
  2. *easy-quest-clean-run* — accept Sluice Maw at full bar, 8 ⚡ gone at
     accept, 3 fights + boss with no further ⚡, prize paid, walk home.
  3. *no-way-home* — mid-quest: no Roothollow/gate/healer rows anywhere;
     turn back, count the return fights = outbound fights; flee one and
     verify the hurt path.
  4. *the-hour-away* — start a quest, idle 61+ min (clock-shim), return:
     exactly one surprise, HP never 0, quest resumes at the same step.
  5. *death-on-the-path* — die to the wyrm: standard death cascade, quest
     gone, town, no refund.
- Numbers, not adjectives, in the results folder per dojo rules.

## Rollback

- Labs toggle off restores the old menu per player instantly (the seam
  guard) — that is the live mitigation.
- Full revert: delete `engine/quest.py`, drop the `floormap` key from
  `labs.py`, revert the `core.py`/`combat.py`/`scene.py`/`render.py` seam
  edits and the `places:` block, revert the doc-version bump (the healed
  `quest: None` key is inert on old code), vendor re-sync. One commit revert;
  no migration, no data to unwind (stale `p["quest"]`/`p["labs"]["floormap"]`
  keys are ignored by design, mirroring the arena graduation precedent).
