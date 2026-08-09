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

### Phase 2 — wrong-species reels (P0/P1)
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
