# 085 — standard floor maps, floors 1–10, and an opaque elevator

Status: planned, 2026-09-09. Execution starts only after this plan and its browser scenarios are committed. Workflow: `.cursor/skills/devprocess/SKILL.md` and root `CLAUDE.md`.

## Problem and evidence

Roy requested maps for floors 1–10 as the standard experience, removed from Labs; instant place explanations and number-key support; and a fully black elevator backdrop so the next place cannot be seen during the ride. Roy explicitly requested a durable design/implementation plan before execution.

- `engine/floormap.py` has one layout and `content/art/maps/` one finished asset: `map_001_492x369.png`.
- `engine/labs.py` restricts `floormap` to floor 1 and per-player opt-in.
- `render.py::_map_html` already draws numbered HTML markers and immediate CSS tooltips. Marker positions and tooltip widths need review at phone sizes before expanding.
- `pane.py` correctly matches number keys to displayed `.key` / `.mknum` digits (082 phase-1h).
- `pane.py` uses `#liftlay {background:#000000cc; opacity:0}` and fades it in after mounting the destination. Only the GIF's `.car` rectangle is opaque. The rest of the destination is deliberately visible through the overlay, and fade-in exposes it further.
- Floors 1–10 have their own playable setting and NPC data. Floor 10 uses a milestone boss: its marker must route the actual live keep option and say GNARL, not KING.

Timeline: 082 phases 1–1h (Aug 26–27) refined floor 1 through small-door, tone, shading, and keyboard fixes. Sept 9 audit confirmed maps stop at floor 1. This plan preserves those lessons and graduates the feature.

## Root cause

Maps were intentionally a one-floor experiment, with art/layout production left unfinished. The elevator backdrop follows an earlier requirement for a translucent dimmer; the new requirement is an opaque loader for the entire view, not only the animation rectangle.

## Emergency mitigation already taken

None. This work changes presentation and feature eligibility; no player-state migration is needed. Existing Labs flags can remain inert in stored documents.

## Locked design contract

1. **Territory scale.** High aerial/oblique view of an entire district, approximately the same visual scale as floor 1. Forests are canopy masses; settlements are many tiny roofs; fields are whole systems; mountains are ranges. Terrain extends past all four image edges. No horizon/picture-postcard framing or isolated floating diorama.
2. **Consistent proportions.** Ordinary trees, roofs, doors, carts and people are tiny. A gate pylon or castle is monumental because its entrance/windows are small relative to its walls, with tiny surrounding vegetation establishing scale. A door must never resemble the whole building. Underground floors show vast cavern/galleries with the same district-scale reading, not a close-up mine entrance.
3. **Designed 1-bit gradients.** Follow `plugin-linear-ascent/vision/1bit-images.md`: the model designs the dither as art. Strong directional light, fully shaded terrain volumes, deep cast shadows, broad readable gradient fields, subdued micro-texture. Avoid flat outline maps, grey photographic speckle, pale mountains and burned-white ground.
4. **Preserve the accepted floor-1 pipeline.** Floor 1 remains byte-identical. New maps target the same 492×369 grid, 4:3 ratio, pixelated display, and two output colors: opaque black and `(217,217,211)`. Start from the accepted grid-enforcement recipe: crop, LANCZOS, unsharp radius 1.2 / percent 180 / threshold 2, autocontrast cutoff 1, gamma 1.15, highlight ceiling 0.85, Bayer 8×8. These are the baseline, not permission to hide a poor source with filters. Record any justified per-image adjustment.
5. **Measured visual checks.** Floor-1 calibration: overall ink ~50.8%, near-solid-white 8×8 blocks ~0%, mountain shadows retained. New floors may be darker where fiction requires; do not force every floor to the same histogram. Inspect full maps at native size and enlarged nearest-neighbor, with label overlays at desktop and phone sizes. Reject any map whose important terrain loses volume or whose door/tree proportions read incorrectly.
6. **Art and text stay separate.** No generated lettering, markers, borders, legends, watermarks or compass decoration in bitmap assets. Keep floor-1 HTML chip font, size, bracketed numbers, colors, cost icons, hover inversion and placement grammar.
7. **Place explanations.** Short floor-specific prose on every map marker; immediate hover and keyboard-focus reveal, no animation delay. Keep descriptions readable over an opaque tooltip background and inside the viewport. Include action/cost meaning where useful; avoid implementation language.
8. **Input and accessibility.** Clicking/tapping an action performs the existing action exactly once. Number keys match the number printed on its chip, including mixed map markers and residual rows; do not capture typing in input fields. Tab focus identifies markers and exposes explanations. Keep useful accessible names/descriptions. Touch controls must remain directly usable without a required hover step.
9. **All existing actions remain reachable.** Map the camp, gate, Roothollow return, keep, hunt and conditional deep hunt. Unmapped conditional options (healing, stew, items, assistance) retain ordinary rows. Do not invent quest buttons or change energy costs. The three-per-floor expedition system is outside this request.
10. **Geography and navigation.** Use the current floor 1–10 YAML/lore context, keeping the gate, local settlement, nearby hunting country and distant danger coherent. Returning to Roothollow means descending the lift, not claiming a second Roothollow exists on each floor. Check marker anchors against the final generated art rather than assuming the model hit requested coordinates.
11. **Graduation.** Floors 1–10 always use maps for normal floor/camp scenes regardless of missing, false or true legacy `labs.floormap`. Remove the registry entry and its tip; higher unmapped floors retain their existing menu. NPC conversation, combat, keep and other non-map cards retain their own presentation.
12. **Elevator blackout.** Cover the full viewport with solid black immediately when the transition starts, with no destination flash or fade-in. Keep the existing ascent/descent GIF, nonce restart and duration. The destination can load underneath but only becomes visible at the end reveal. Prevent clicks/number keys from activating the hidden destination during the ride. Restore input after completion; cleanly replace/cancel overlays when needed. Boot, reload, peek, refused travel and same-place actions must not replay a ride.

## Floor art briefs

| Floor | Setting | Territory and landmark language |
|---|---|---|
| 1 | The Fencerows / Lamplit Steading / Brackjaw | Preserve the accepted map and marker composition. |
| 2 | The Rustwater Adit / Lampfall / Rustmaw | A whole iron-water mountain mining district; branching rail lines, tiny mining settlement, enormous cut ridges and a distant fortified mine keep. |
| 3 | The Drowned Pasture / Weirsend / Sedgeback | Broad flooded field systems, submerged hedge lines, raised settlement islands, river/sluice network, fortified high ground. |
| 4 | The Lightless Glade / Lanternroot / Palegleam | Huge dark forest canopy, distinct clearings and winding paths; tiny camp clustered by the gate, remote keep across the wood. |
| 5 | The Flooded Mine / Pumpstead / Sumplock | Vast terraced cavern mine with connected dark reservoirs, abandoned galleries, monumental pump works and a keep above drowned workings. |
| 6 | The Threshold Dark / Lastlight / Duskspin | Cavern country with the last lit terrace, distant rock masses, chasms and large silk-draped vaults; terrain gradients remain legible in darkness. |
| 7 | The Orchard Rows / Cider Cross / Applewrath | Miles of orchard planting visible as large patterned blocks, lanes, fermentation ponds and clustered farm roofs, with the keep beyond the rows. |
| 8 | The Ashline / Greywell / Cinderhide | Broad ash dune ridges, dark burned groves, secret-water settlement, long paths through dune shadows, massive remote keep. |
| 9 | The Beacon Field / Pylon Rest / Glarefang | Vast moor and signal-pylon network; designed light pools and long shadows crossing heath, tiny settlement and distant keep. |
| 10 | The Kingsfield / Bannerline / Gnarl | Great muster-meadow with regiment-scale banner/camp patterns, roads and fortifications; the Goblin King's monumental fortress and tiny entrances. |

## Phased execution

1. **Production canary:** capture baseline, preserve reference, store prompts and a repeatable conversion pipeline, generate/review floor 2. [phase-1/PLAN.md](phase-1/PLAN.md)
2. **Nine-map set:** generate floors 3–10 using the validated recipe; record assets, anchor coordinates, native/mobile visual review. [phase-2/PLAN.md](phase-2/PLAN.md)
3. **Game integration:** standard maps, instant explanations, responsive chips, keyboard support and opaque elevator; targeted checks and vendor sync. [phase-3/PLAN.md](phase-3/PLAN.md)
4. **Acceptance and release:** full suites, browser scenarios, live conversation verification, scoped commits, explicit deployment and post-deploy checks. [phase-4/PLAN.md](phase-4/PLAN.md)

After each phase, append execution status with evidence, reread remaining phases and amend assumptions before proceeding. No image fleet before the floor-2 canary is inspected.

## Verification

Browser scenarios are committed first under `worldd/tests/085-floor-maps-standard/`. Results: `dojo/results/0062-085-floor-maps-standard-2026-09-09/` (or next available ID if occupied).

The first likely player query is **“show me floor 2”** from an eligible QA character, followed by the bare displayed number for the map's GATE action. Verify both direct web play and the Luna conversation consumer when available; do not substitute renderer-only checks for a live walkthrough.

Acceptance includes all ten maps, absence of the Labs toggle, legacy-flag independence, floor-11 fallback, milestone floor 10, non-map camp conversations, marker costs and conditional actions, instant hover/focus explanations, mobile overlap/clipping, number keys, opaque ascent/descent/return rides and first-frame/final reveal behavior. Full tests must have no new failures; pre-existing failures are reproduced and recorded separately rather than relabeled green.

## Operational notes and rollback

- Branch `codex/085-floor-maps-standard` in parent and plugin repos. The plan/test suffix is shared; `codex/` follows workspace branch policy.
- Plan and scenarios are committed before implementation. Commit plugin changes first, then the parent vendor and submodule pointer. Preserve unrelated dirty admin/feedback, Luna and research work; stage only this task's paths/hunks.
- Compare plugin package and vendor before `worldd/tools/vendor_game.sh`; never overwrite unexplained vendor-only work. Both copies must ship the same code/assets/version.
- Built-in image generation is the default; one call per map, with floor 1 as style reference. Save prompts and copy selected sources/outputs into project storage; no project reference may depend on the temporary location returned by generation. Grid enforcement is the existing map pipeline specified above.
- No player data deletion or migration. Legacy stored flags are harmless.
- Deployment: push the reviewed release, run `worldd/tools/deploy.sh`, poll to live, verify version and static assets, then exercise the production route. If a required external dependency is unavailable, record the exact unfinished step rather than claiming complete.
- Rollback: revert this plan's implementation commits (plugin first and parent vendor/pointer together), deploy the resulting release. Additive unused map files can stay. Restore the previous Labs registry/gate and elevator behavior through the revert; no player-state rollback is necessary.

## Execution status

Planning only. No implementation or generated maps yet.
