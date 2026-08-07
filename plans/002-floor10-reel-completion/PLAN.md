# 002 — Complete all kill-reels for floors 1–10

## Problem
The 038 mercy fleet run (2026-08-07) judged all 62 mercy slugs on Grok Imagine 1.5:
30 passed + warden_fall, 32 parked. 29 of the parked slugs are floor-1–10
encounters, so floors 2–10 are incomplete (floor 1 is done; floor 8 lacks only
ash_adder; floors 6 and 9 are worst at 5 parked each). Evidence: per-take judge
sheets and the fleet gallery from the 038 run; park reasons recorded per slug.

## Root cause (per fail family)
1. Insect/moth reveals render as winged-cat chimeras (12+ fails, wording-proof).
2. Bird reveals render adult/dog-scale (1 pass in ~10 bird takes: cinder_vulture
   chick).
3. Snake reveals render with legs (reed_adder passed, ash/pylon did not).
4. Boar reveals drift to adult size on some scenes.
5. Pale scenes render grayscale despite the photoreal-color prefix.
6. Crowd lore words ("muster", "parade", work-gang prose) spawn background
   armies; some scenes duplicate the creature in frame 0.
7. Evicted dissolves sometimes leave a corpse/skull instead of the black-liquid
   drain.
8. drift_eel, coolant_crab, guano_vole were judged BEFORE the v6 template fixes
   (spring-back dodge, orb removed from melee) and failed on exactly those
   defects — they never had a fair v6 roll.

## Fix — three phases, cheapest first

### Phase A — template overrides + re-rolls (no lore changes, ~13 slugs)
- Species-anatomy overrides in `_load_mercy_jobs()`
  (plugin-linear-ascent/tools/generate_event_gifs.py): SNAKE legless-coil
  clause, BIRD newly-hatched-chick clause (ordered before the moth branch —
  night_hawk is a "moth-hunting nightjar"), piglet loaf-of-bread size anchor.
- Re-roll under v6: drift_eel, coolant_crab, guano_vole, ash_adder, lane_boar,
  wick_owl (wave 1); then pylon_adder, rabid_boar, windfall_crow, night_hawk,
  bunting_kite, shadow_wolf (wave 2), informed by wave-1 verdicts.
- Max 3 takes per slug, ~$0.64/take → worst case ~$23 for both waves.

### Phase B — scene rewrites (no lore changes, ~12 slugs)
Duplicate/crowd slugs get explicit empty-world wording; pale scenes get
concrete color anchors; evicted beats get a "nothing solid remains" clause.
Targets: shellback_tortoise, wire_eel, silk_broodling, vault_weaver,
guano_vole (if wave 1 fails), lamp_eater, lamptree_wight, bailer_kobold,
miner_husk, windfall_wight, flicker_wight, muster_wight, banner_wolf,
courier_hound, plus generics (native, pressed_fall, wrongmade).

### Phase C — reveal-animal lore swaps (needs user sign-off)
glare_moth, grave_moth, beacon_moth, hornet_swarm cannot render as insects.
Proposal table goes to the user before any floor-YAML edit.

## Verification
Per slug: judge sheet (16-row color frame sheet from the raw mp4) passes the
6-rule shape-specific checklist; species and scale of the reveal correct;
color confirmed by channel diff for pale scenes. Floor is "complete" when
every encounter id in its YAML has a passing reel. Re-run byte-cap check
(≤4096 UTF-8 bytes after folding) after every template edit — current max
3930.

## Rollback
Template edits: `git checkout -- tools/generate_event_gifs.py` in the
plugin-linear-ascent submodule. Renders are additive files under
content/art/events/ — restore any regressed slug's previous mp4/gif from git.
Floor YAMLs untouched until Phase C sign-off.

## Execution status (2026-08-08, Phases A+B complete)

**7 new PASSES** (floors 1–10 board 30/59 → 37/59): ash_adder (floor 8 now
6/6), lane_boar, wick_owl, bunting_kite, guano_vole, courier_hound,
pressed_fall (generic). ~$60 spent, ~94 paid takes, max 3 per slug per set.

**Phase A/B findings, each confirmed across 3-take sets:**
- De-catting works: stripping every cat token from the spider prompts took
  feline chimeras from 6/6 to 0/6. Species contamination was prompt-induced;
  spiders need no lore swap (silk_broodling, vault_weaver still fail on size).
- Evicted beat unrenderable as worded: melt-to-empty ending failed 21/21
  takes (6 wights + generic) — always a corpse, skeleton, or standing ink
  pool. Fall beats pass because a fallen body IS their required end state.
- "DESERTED" wording fully suppressed muster_wight's background armies.
- Explicit color anchors near-100% reliable (banner_wolf chroma 1.4 → 63-82).
- Reveal-size anchoring is the universal unsolved problem: apple, palm,
  loaf, and boot anchors all ignored (reveals 5-10x oversize); size similes
  literalize as props (flying loaf 2x); pre-stated reveal animals spawn
  early beside the monster; GIANT-defender framing draws scale-reference
  humans even with the human comparison removed.

**Parked → Phase C decision list (22):** moths×3 + hornet_swarm +
coolant_crab + drift_eel + wire_eel (species lore swaps); night_hawk
(non-avian reveal needed); windfall_crow, rabid_boar, shadow_wolf,
pylon_adder, shellback_tortoise, silk_broodling, vault_weaver, banner_wolf,
native_freed (structural staging redesign — size/figure control);
bailer_kobold (scene timing pad); lamp_eater, lamptree_wight, miner_husk,
windfall_wight, flicker_wight, muster_wight, wrongmade_evicted (evicted-beat
redesign).

## Operational notes
- Grok renders via `generate_event_gifs.py <slug> --backend grok --force`,
  env from ~/Documents/Luna/luna/.env. 30s retry on API error does not count
  as a take.
- Raw color mp4 is the master; 320×112 1-bit gif auto-derived in the same run.
- luna submodule is a parallel session's lane — untouched.
