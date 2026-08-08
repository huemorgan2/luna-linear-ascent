# 002 Phase C — remaining 22 reels: lore swaps, evicted redesign, staging retries

## Goal
Every floor-1–10 encounter id has a passing reel (board 37/59 → 59/59 target,
realistically +12–18). User signed off 2026-08-08 ("carry on and try to work in
parallel make subagents work on it - for the texts use fabel") — floor-YAML
lore edits are now authorized. Text authored by Fable subagents.

## Steps
1. **Lore swaps (9 slugs, floor YAMLs):** glare_moth, grave_moth, beacon_moth,
   hornet_swarm→field mouse, coolant_crab→pale cave salamander,
   drift_eel+wire_eel→blind cave-fish, night_hawk→non-avian,
   windfall_crow→non-avian (moved from structural group — avian reveals are
   wording-proof). One Fable agent owns all YAML edits; only `was:`/`lore:` of
   those encounters change. No winged/avian species, no cat tokens.
2. **Evicted-beat redesign (template):** replace the melt-to-empty ending
   (0/21) with an ending that works WITH the corpse prior (e.g. collapse into
   visibly-empty clothes/ash the wind takes). Fable agent drafts; I apply.
   Affects lamp_eater, lamptree_wight, miner_husk, windfall_wight,
   flicker_wight, muster_wight, wrongmade_evicted.
3. **Staging subs (template):** reveal stated only at the dissolve beat,
   absolute size cues, structural smallness, no-other-people clause for
   banner_wolf, timing pad for bailer_kobold. Targets: rabid_boar,
   shadow_wolf, pylon_adder, shellback_tortoise, silk_broodling, vault_weaver,
   banner_wolf, native_freed, bailer_kobold. Fable agent drafts; I apply.
4. **Floor landscapes (user, 2026-08-08):** every remaining reel's scene gets a
   short clause grounding it in its floor zone's landscape (from zone/arrival
   YAML prose) — the original renders omitted the floor scenery by mistake.
5. **Contrast grade (user, 2026-08-08):** videos more contrasted, characters a
   shade darker than the scene, strong silhouette separation — added once at
   template level for all remaining renders.
6. Byte-cap check (≤4096 after folding) after every template edit.
7. Render + judge in parallel waves: one subagent per slug, synchronous
   renders, 16-row sheet, 6-rule checklist, max 3 paid takes per slug.

## Verification
Per slug: judge sheet passes the 6-rule checklist (species, size, fight shape,
color channel-diff, quiet ending). Board recount at end. Worst-case spend
~23 slugs × 3 × $0.64 ≈ $44.

## Rollback
YAMLs and template: `git checkout -- <file>` in the plugin-linear-ascent
submodule (this phase starts from clean commit c3c37c5). Renders additive;
prior passing gifs recoverable from git.

## Execution status (2026-08-08)

Complete. Board 51/59 floor-1–10 encounter reels passing (was 37/59 at phase
start). Submodule commit 02040b1: template (landscapes + contrast grade +
retry subs), floor YAMLs 001–010 lore swaps, 90 passing gifs. Spend this
phase ≈ $57 (89 paid takes); cumulative 002 ≈ $117.

Passing this phase: glare_moth, grave_moth, beacon_moth, night_hawk,
windfall_crow, banner_wolf, lane_boar, flicker_wight, drift_eel, shadow_wolf,
coolant_crab, native_freed (accepted on judged take 3 — every mechanical rule
passed; rabbit body ~16% of defender height, only ear-tips at knee line) +
earlier-wave passes.

Parked 11 mercy slugs (failing takes deliberately left uncommitted, fail
families in memory grok-mercy-reel-lessons): hornet_swarm + rabid_boar + shellback +
vault_weaver + silk_broodling (reveal-size / early-spawn), pylon_adder
(mouth-escape 3/3), bailer_kobold (archer draw-hold 3/3 + dark-scene
grayscale), lamptree_wight (lore-seeded third figures + dark scene),
wire_eel, windfall_wight, muster_wight (arrow-stretch at impact — systematic;
next idea: thrown weapon or closer framing). These need scene/lore redesign,
not more takes.

Incident: parallel session (006-ship) stashed this phase's uncommitted work
as stash@{0}; recovered via `git stash apply` + direct `git show
'stash@{0}:tools/generate_event_gifs.py'` extraction (apply silently skipped
that file). Stash entry left intact for the parallel session.
