# Misfit visuals — assets that exist but show the WRONG thing

Audit date 2026-08-09, plugin commit 5291d81 (0.57.1). Method: contact
sheet per encounter (portrait + 8 reel frames), one viewer agent per
floor, all 59 floor 1–10 encounters judged. Sheets archived in session
scratchpad `audit_sheets/f<floor>_<id>.png`.

File locations (plugin repo `plugin-linear-ascent/`):
- Portrait: `content/art/creatures/<id>_320x112.png`
- Reel:     `content/art/events/<id>_<verb>_320x112.gif`
  (verb by kind: native→freed, pressed→fall, wrongmade→evicted)

Regen commands (run from `plugin-linear-ascent/`, luna/.env sourced):
- Portrait: `uv run --project ../luna python tools/generate_creatures.py <id>`
  (prompt auto-built from YAML name+prose — all rows below verified to
  have updated prose, so no YAML edits needed)
- Reel: `uv run --project ../luna python tools/generate_event_gifs.py <id>_<verb> --backend grok --force`

---

## P0 — wrong-species PORTRAITS (10) — regenerate portrait

| # | Floor | id | Display name / was | Portrait shows (WRONG) | Reel status |
|---|---|---|---|---|---|
| 1 | 6 | grave_moth | Grave-rat — pallid rat-pup | moth | reel correct (rat) |
| 2 | 4 | glare_moth | Lamp newt — glade-newt | moth | reel correct (newt) |
| 3 | 9 | beacon_moth | Glare vole — heath-vole | moth | reel correct (vole) |
| 4 | 9 | night_hawk | Night-shrew — dusk-hunting shrew | hawk/bird | reel correct (shrew) |
| 5 | 7 | windfall_crow | Windfall dormouse — fat dormouse | crow flock | reel correct (dormouse) |
| 6 | 5 | coolant_crab | Sump-crawler — pale cave salamander | crab | reel correct (salamander) |
| 7 | 8 | cinder_wolf | Ashline jackal — dune scavenger | bulky grey wolf | reel correct (lean jackal) |
| 8 | 1 | ember_shade | Hedge-wight — undead humanoid | ember quadruped beast | reel correct (humanoid wight) |
| 9 | 3 | windfall_haunt | Drowned lantern — handless drifting light | fleshy ogre brute | reel correct (lantern-wisp) |
| 10 | 7 | hornet_swarm | Mouse-tide — carpet of mice | hornet | **reel ALSO wrong — see P0-R below** |

Acceptance per row: new portrait unambiguously depicts the display-name
species; 1-bit style consistent with neighbors; verified by fresh contact
sheet + viewer judgment.

## P0-R — wrong-species REEL (1) — regenerate reel

| Floor | asset | Expected | Actually shows |
|---|---|---|---|
| 7 | hornet_swarm_freed_320x112.gif | monster dissolves → reveals mice ("Mouse-tide", was: a single field mouse) | shaggy beast disperses into a HORNET swarm, final reveal is a BEAR — no mouse anywhere |

Historically parked in phase C (reveal-size fail family) — redesign the
scene wording, don't re-roll the same prompt.

## P1 — species-weak / wrong REELS (3) — regenerate reel

| Floor | asset | Expected | Problem |
|---|---|---|---|
| 3 | wire_eel_freed_320x112.gif | Fence-wire pike — reveal a blind white FISH | reveal is a legged lizard/crocodile; wire-serpent monster ok, reveal species wrong |
| 5 | drift_eel_freed_320x112.gif | Sump lamprey — eel/lamprey shape | reel creature is a chunky ordinary carp/perch; f10 frame reads garbled |
| 8 | greywell_ogre_fall_320x112.gif | Dune ogre — hulking giant falls | fighting figure is human-sized, no ogre bulk; also holds bow in f0 then hammer later |

## P2 — polish (optional; none player-blocking)

| Floor | asset | Note |
|---|---|---|
| 3 | reed_adder_freed.gif | mid-reel monster has legs (reads lizard); final snake reveal correct — acceptable, redo only if budget allows |
| 8 | ash_adder_freed.gif | same pattern as reed_adder (lizard mid-reel, snake reveal correct) |
| 10 | bunting_kite portrait + reel | both read draconic/theropod, not a kite (bird of prey); consistent with each other, weak vs lore; reveal bird looks fowl-like |
| 5 | blind_shoal portrait + reel | shows ONE fish; lore says a shoal |
| 4 | lamp_eater portrait vs reel | portrait = giant mound-beast, reel = slender skeletal humanoid; both plausible wrongmade but different designs — pick one canon |
| 6 | silk_broodling_freed.gif | final small-spider reveal almost too tiny to read |
| 4 | wick_owl_freed.gif | revealed owlet reads duck-like |
| 1 | lane_wolf portrait | reads feral wolf; lore says sheepdog ("The last pack") — reveal in reel is correctly a dog |
| 4 | glade_stag_freed.gif | f51 transitional frame is a shaggy blob (transformation moment) — accept as-is |

## Known-parked overlap (context, no new action here)

Phase C parked 11 slugs for reel-quality reasons (see
`plans/002-floor10-reel-completion/phase-c/PLAN.md`): hornet_swarm,
rabid_boar, shellback_tortoise, vault_weaver, silk_broodling,
pylon_adder, bailer_kobold, lamptree_wight, wire_eel, windfall_wight,
muster_wight. This audit independently re-flagged hornet_swarm, wire_eel,
lamptree_wight (see MISSING-VISUALS — its committed reel shows only a
tree, no wight) and the generic-fallback trio. The committed takes for
shellback_tortoise, vault_weaver, bailer_kobold, windfall_wight passed
this audit's species check — they stay parked for polish, not species.
