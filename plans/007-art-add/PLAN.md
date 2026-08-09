# 007 art-add — fix misfit + missing floor visuals

## Problem (evidence, 2026-08-09)

User report: "in many cases there is a butterfly — the video is a rat and
there is no image — and a lot of mixed-up art — missing items all around,
especially floors 6/7."

Full audit run 2026-08-09 (this folder's two lists are its output):
- Inventory script over all 100 floor YAMLs: 425 encounters, 543 portrait
  PNGs — **zero missing files**; local == committed == vendored == live.
- Visual judgment of all 59 floor 1–10 encounters (contact sheet per
  encounter: portrait + 8 reel frames; one viewer agent per floor).
- Result: **10 portraits show the wrong species**, 1 reel reveals the
  wrong animal outright (hornet_swarm → bear), 3–4 more reels are
  species-weak, 3 encounters play a generic fallback reel. Floors 11–100
  have no reels at all (by design — legacy schema, no `kind:` field).

"No image" in the user report = wrong-species portrait (a moth standing in
for a rat reads as no/broken art), not absent files.

## Root cause

Phase C (plan 002) lore swaps renamed encounters in the floor YAMLs
(`name`/`was`/`lore`/`prose` all updated) but portraits are keyed by the
unchanged encounter `id` and were **never regenerated** — they still show
the id's original species (grave_moth id → moth art, "Grave-rat" lore).
The reel gaps are the already-known phase-C parked slugs plus the
by-design generic fallbacks.

Regeneration is safe-by-construction: `tools/generate_creatures.py`
builds prompts from the YAML `name` + `prose`, both verified updated for
all 10 misfit slugs — rerunning the generator on those slugs produces the
correct species with no prompt hand-editing.

## The lists (the agent's work queue)

- **[MISFIT-VISUALS.md](MISFIT-VISUALS.md)** — assets that exist but show
  the wrong thing. P0 = 10 portraits + hornet_swarm reel. P1 = 3 wrong-
  species reels. P2 = polish.
- **[MISSING-VISUALS.md](MISSING-VISUALS.md)** — assets that don't exist:
  3 own-reel gaps (generic fallback plays), plus the floors 11–100 no-reel
  backlog (decision item, NOT in scope here).

## Fix — phases

### Phase 1 — regenerate the 10 misfit portraits (P0)
- **Goal**: all 10 P0 portraits depict the YAML species; verified visually.
- **Steps**: in `plugin-linear-ascent/`:
  1. `set -a; source ~/Documents/Luna/luna/.env; set +a` (LUNA_GEMINI_API_KEY)
  2. `uv run --project ../luna python tools/generate_creatures.py \
     grave_moth glare_moth beacon_moth night_hawk windfall_crow \
     coolant_crab cinder_wolf ember_shade windfall_haunt hornet_swarm`
  3. Regenerate audit contact sheets for the 10 slugs; viewer-agent (or
     human) judgment: portrait species == `name`/`was` species.
  4. Take count > 1 allowed — regenerate individual slugs until species
     is unambiguous. Keep raws in `content/art/creatures/raw/`.
- **Verification**: per-slug species verdict YES ×10; pixel sanity
  (std ≥ 15 on L channel); plugin tests still pass
  (`uv run --project ../luna python -m pytest tests`).
- **Rollback**: `git checkout -- content/art/creatures/<slug>_320x112.png`
  (all 10 are tracked files).

### Phase 2 — reels: misfits, gaps, and quality (P0/P1) — REVISED 2026-08-09

User go + new art direction (2026-08-09): "fix all issues and missing
visuals until the 10th floor … the freed animations are not the best.
some turn the animal from itself into itself. the freed animals need to
look smaller and real. mice are not giants … render the animations not
as real — render them as drawing shaded animations, then turn them to
1 bit."

Three standing rules for every take, on top of the phase-C checklist:
1. **Drawn, not photoreal.** New mercy prefix: hand-drawn shaded
   animation (bold ink outlines, flat shading planes) instead of the
   photoreal MERCY_PREFIX; the 1-bit Bayer pass keys off drawn shapes,
   not photographic noise. Prefix stays compact (grok 4096-byte cap).
2. **Reveal is SMALL and REAL.** The freed animal must read tiny next
   to the defender (cup-hands / bootprint blocking subs applied to all
   freed slugs) — a revealed mouse is mouse-sized, full stop.
3. **No self-into-self.** The monster phase must read monstrous —
   clearly bigger/wronger than the reveal; a reel where the fought
   animal already looks like the revealed animal FAILS.

Work list, take cap 3 per slug (~$0.64/take), judge every take:
- Batch A (misfit + missing): hornet_swarm_freed, wire_eel_freed,
  drift_eel_freed, greywell_ogre_fall, lamptree_wight_evicted,
  rabid_boar_freed, pylon_adder_freed, muster_wight_evicted.
- Batch B (quality re-rolls flagged by the audit): mire_boar_freed +
  guano_vole_freed (self-into-self — monster renders small),
  blind_shoal_freed (fish floats mid-air), wick_owl_freed (duck-like
  owlet), reed_adder_freed + ash_adder_freed (legged lizard mid-reel),
  bunting_kite_freed (draconic), silk_broodling_freed (illegible
  reveal).
- Pilot first: 2 slugs in the drawn style, judged, style tuned, then
  the batches.

### Phase 2 (original scope, superseded by above)
- **Goal**: hornet_swarm_freed reveals mice (not a bear); wire_eel_freed
  reveals a fish; drift_eel_freed reads lamprey/eel; greywell_ogre_fall
  figure has ogre bulk. Own reels for rabid_boar_freed + pylon_adder_freed
  so a boar/snake stop revealing a small dog.
- **Steps**: grok pipeline per slug (~$0.64/take, cap 3 takes/slug then
  park): `uv run --project ../luna python tools/generate_event_gifs.py
  <slug>_<verb> --backend grok --force`; judge with the 16-row sheet +
  6-rule checklist (phase-C scratchpad `judge_sheet.py`). Lore-redesign
  notes for the historically parked slugs are in
  `plans/002-floor10-reel-completion/phase-c/PLAN.md` (fail families —
  don't repeat wording that already failed 3/3).
- **Verification**: judged PASS per slug; `_event_art()` resolves the own
  reel (audit script `reel=own`).
- **Rollback**: delete the new gif → fallback resumes; or
  `git checkout --` for replaced tracked gifs.

### Phase 3 — P2 polish (optional, budget-permitting)
Items listed in MISFIT-VISUALS.md §P2. Skip freely; none are
player-blocking. Re-judge anything touched.

### Phase 4 — ship
- Bump version.py + luna-plugin.toml, plugin tests, commit/push (gh
  huemorgan2), vendor via `worldd/tools/vendor_game.sh`, parent commit,
  push, verify `/health` `game` field (manual Render deploy if stale),
  package + publish to marketplace, verify index version + sha256.
- **COORDINATE FIRST**: the parallel session has unshipped 0.58.0 work
  (kill-bar rebalance) and an unpushed plugin commit (e14a8df). Check
  `git ls-remote` + live index version immediately before choosing the
  version number. Never leave a publish retry loop unattended.
- **Rollback**: revert vendor commit + redeploy (worldd); marketplace
  versions are immutable — roll forward with a new version number.

## Verification (whole plan)
Re-run the audit inventory + viewer-agent pass over floors 1–10: expected
end state = 0 portrait mismatches, 0 wrong-species reveals in own reels,
generic fallback count ≤ 1 (muster_wight only, if still parked).

## Execution status — Phase 1 (2026-08-09)

DONE. All 10 P0 portraits regenerated and committed (plugin 17a2255).
- 8/10 passed on take 1 (rat, newt, vole, shrew, dormouse, salamander,
  jackal, thorn-wight). windfall_haunt needed take 2 (take 1 showed a
  figure carrying the light; take 2 is a handless drifting lantern —
  exact lore). hornet_swarm: take 2 regressed to a single kaiju-beast;
  kept take 1 (boiling dark carpet, reconstructed losslessly from the
  audit flatten — ink 44% matches generator log).
- Plugin tests: 978 passed, 1 skipped, 2 FAILED — both failures
  reproduce on clean HEAD (parallel session's in-flight 044 state:
  test_026 getaway-blood, test_multiplayer strike-join); NOT caused by
  this change (art-only, 0 code lines).
- NOT pushed: local plugin main carries 2 unpushed parallel-session
  commits (0d46577, 4971eee — their plan 044 "image-first kill reels,
  floor 6 stills"); remote main is dcf5172 (diverged). Pushing would
  publish their WIP. Push + vendor + ship deferred to Phase 4
  coordination.
- COORDINATION FLAG: parallel session's plan 044 is building kill
  reels/stills for floor 6 — overlaps Phase 2 of this plan. Reconcile
  before spending grok budget on floor-6+ reels.

## Execution status — Phase 2 (2026-08-09)

DONE. All 16 floor 1–10 mercy reels regenerated in the drawn style
(`--style drawn`, plugin tool commit 0d01c0c; anchors + reels commit
2adf4f9) and judged frame-by-frame on the final 1-bit gif (new
scratchpad `gif_sheet.py` — judge what survives the Bayer pass, not the
raw mp4). 16/16 PASS against the three standing rules. NOT pushed
(parallel session's unpushed commits still on local main — Phase 4).

Take ledger (25 grok takes ≈ $16):
- **Take-1 pass (9)**: hornet_swarm (pilot), mire_boar (pilot),
  rabid_boar, pylon_adder, lamptree_wight, drift_eel, reed_adder,
  ash_adder, bunting_kite*. (*t1 kept but gif rebuilt at 71 frames —
  frame 0 held a double-monster; dropped the frame instead of spending
  a re-roll.)
- **Take-2 pass (5)**: blind_shoal + muster_wight (t1 static
  arrow-line → forced sword melee), silk_broodling (t1 near-black
  final hold), greywell_ogre (t1 opening-frame bow glitch),
  guano_vole (t1 monster rendered true-animal-size → `_MERCY_BULK`).
- **Take-3 pass (2)**: wire_eel + wick_owl (t2 persistent shell —
  monster survives the burst and stands beside the reveal →
  `_MERCY_VANISH`). Both at the cap; nothing parked.
- muster_wight had failed 3/3 in phase C — the drawn style + forced
  melee got it through on take 2. Generic-fallback trio (muster_wight,
  pylon_adder, rabid_boar) now have own reels.

New fail families discovered + their standing fixes (in the tool, so
future floors inherit them):
- **Persistent shell** → `_MERCY_VANISH` anchor (shell VANISHES
  COMPLETELY at the burst).
- **Small monster / self-into-self** → `_MERCY_BULK` anchor (monster
  TOWERS over the defender until the burst).
- **Arrow-line stretch** (archer strike renders as a static line) →
  `_MERCY_FORCE_MELEE` set, kind-guarded so evicted templates keep
  their own beat.
- Drawn-mode scrub: color anchors stripped, photoreal motion closer
  swapped for "weighty drawn motion", wire_eel white-fish reveal given
  ink edges (invisible on pale ground otherwise).

Byte discipline: drawn prefix held to 247 B; all 16 prompts verified
≤ 4096 UTF-8 bytes post-em-dash-fold; 0 overs at generation time.

Plugin tests after commit: 978 passed, 1 skipped, 2 failed
(7.32 s). The 2 known failures reproduce on
clean HEAD (parallel session's in-flight state: test_026 getaway-blood,
test_multiplayer strike-join) — pre-existing, not from this change.

Phase 3 (P2 polish) — largely absorbed: every P2 reel row (reed_adder,
ash_adder, bunting_kite, blind_shoal, silk_broodling, wick_owl) was
regenerated and passed in Phase 2. Remaining P2 items are portraits
(lamp_eater canon pick, lane_wolf, bunting_kite portrait) — optional,
untouched. Phase 4 (ship) still blocked on parallel-session
coordination.

## Operational notes
- Gemini key for portraits and grok key for reels both come from
  `~/Documents/Luna/luna/.env` — never committed; secret-scan before
  every commit.
- The luna-linear-ascent checkout is SHARED with a parallel Cursor
  session: check `git status`/HEAD right before every commit; commit
  narrowly (only your paths).
- Marketplace upload sets latest_version unconditionally — re-check the
  live index in the same breath as any publish.
- Floors 11–100 reels are a scope decision for the user, not this plan.
