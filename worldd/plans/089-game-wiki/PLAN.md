# 089 — game wiki and the full floor bestiary

## Problem, evidence and timeline

On 12 September 2026 the user identified that the Combat Atlas floor slider rescales the same eight placeholder pictures. The current game has 425 encounter IDs across 100 floors, with 425 distinct image hashes and no missing encounter art. The independent atlas also uses Geist, several text sizes, Lucide icons and short dropdowns; the game website already specifies IBM VGA 16px and supplies pixel icon masks.

## Root cause

The research prototype used an eight-entry illustrative array rather than the authored floor rosters. Its UI was built separately from the game website. No `/wiki` route exists.

## Emergency mitigation

None needed; the prototype is a reference artifact, not game state.

## Goal and scope

Serve the atlas as the game's public `/wiki`, with all 425 authored creatures on their actual floors, named geography/lore, species-specific current stats and distinct images. Each existing species has one fixed proposed defensive profile (at most three variants permitted if added later); no random reassignment or universal reskins. Preserve the proposed weapon/effect/progression/movement/shield/warden reference, label proposals clearly, and retain live combat behavior. Use game pixel icons, IBM VGA at 16px everywhere, and visible options whenever there are six or fewer choices. The 16-family weapon selector stays a dropdown.

## Steps

1. Work from current origin/main in an isolated checkout; avoid unrelated dirty work and preserve the already released map changes. Commit this plan and browser scenarios before implementation.
2. Build a reproducible wiki data generator from the vendored content/schema, economy and icon modules, plus the existing research's proposed model. Validate unique images, all floor placements and the three-profile limit. Keep proposed profiles in an explicit reviewable mapping.
3. Add standalone HTML/CSS/JavaScript under `worldd/static/site/wiki/`, mount `/wiki` through the existing site router and link it from the homepage. Reuse `/static/laart` and the website font. No new package/runtime service or game data writes.
4. Verify routes/content/math with targeted tests, then run the full worldd suite using its disposable local test database. Walk the wiki through a real browser at desktop and phone sizes, checking floors 1/3/25/50/80/100, short option groups, long weapon dropdown, all grade/upgrade endpoints, icons and computed text size. Because this changes only a public reference endpoint that the plugin does not call, the relevant first-user action is opening `/wiki`; no combat state or Luna tools change.
5. Push the reviewed changes, explicitly deploy through Render, verify the exact `/wiki` revision and `/health`, and record results. Preserve the existing game/version; do not claim combat balance has shipped.

## Verification scenarios

See `worldd/tests/089-game-wiki/walkthrough.md`. Data tests must cover every floor and every encounter, not only the screenshots. Matchup and shield calculators retain the verified proposal. Creature stats must equal current per-species engine stats and be labeled current. Proposed affinity colors are a separate presentation layer.

## Rollback

Before commit, restore `worldd/app/site.py` and `worldd/static/site/index.html` from baseline `12f5fc5` and remove only the new wiki directory, generator and wiki tests. After commit, revert this plan's implementation commit (recorded in execution status), push and redeploy. No database rollback is required. For immediate hosting rollback, redeploy the previously live commit `2f18569` through Render; never modify the database or other branches' working copies.

## Operational notes

The wiki is public game documentation. Draft combat values must remain visibly distinguished from the current roster and stats. Regenerate data whenever content or economy changes. The website inherits the checked-in generated bundle on every deployment. No new animal images are needed: each of the 425 existing creatures already has unique art. Tinting uses the same CSS-mask treatment as in-game banners and keeps image geometry intact.

## Execution status

Plan and loot scope committed before their respective implementation. Public wiki, generated425-creature data,64 source settings and research note implemented. Targeted Python3/3 and Node5/5 checks pass; full worldd suite223/223 passes after initializing the pinned plugin submodule. Desktop1440×960 and phone390×844 browser scenarios passed. Implementation693d4f7 pushed to main and explicitly deployed: dep-daik2p5g1s2s73flpv10, live2026-09-12T12:15:34Z. Public homepage Wiki link, revision089.1, all425/64 rows, Floor80 deep odds and Legendary source details verified in the browser. Render /health is ok:true,db:true,game0.112.0; served data.json matches the checked-in bytes. All phases complete. Rollback implementation with `git revert 693d4f7` followed by push and explicit Render deploy; no database change exists. See `dojo/results/0065-089-game-wiki-2026-09-12/summary.md`.

## Scope addition — user follow-up before implementation of loot controls

Add a full, image-bearing loot/settings section for all 425 hunt creatures and every floor, including each creature's current parameters and separate proposed material/weapon rarity probabilities. Show normal versus deep hunting and specimen effects explicitly. Percentages must distinguish independent material rolls from a single categorical weapon drop; show no-weapon probability. Retain nonzero but very rare early Epic finds. Reuse the earlier material progression knots, and expose all new coefficients as draft settings.

Acquisition settings are per weapon family and source: shop starting levels Common0/Rare2/Epic4/Legendary6, full durability; hunt drops start at0 with Common40%/Rare30%/Epic20%/Legendary10% remaining durability. Shop unlocks at the starting-level gate, so Legendary+6 unlocks at floor84 rather than importing floor84 stats into floor76. Initial shop price includes the grade's acquisition and upgrade charges through the delivered level; do not charge upgrades twice. Show actual starting attack, durability, floor, price, source/eligible monster count and weight for all64 grade variants. Data settings must be editable in the checked-in model and validated by tests.

Deep hunts increase high-grade material and weapon odds; species and specimen factors remain unequal. Explain whether a modifier changes encounter selection, rarity chance, bundle yield or wear. No proposed loot or acquisition setting changes live game drops in this documentation phase. Add browser checks for probabilities changing by floor/hunting mode, 64 acquisition rows and Legendary shop+6 versus drop+0/10% durability.

## Follow-up phase — preserve a reachable grade transition

Post-release source review identified a design gap: Rare+2/Epic+4/Legendary+6 shop gates at28/57/84 would leave new-grade entrants dependent on very rare weapon drops. The existing +0 gold/material recipe needs an explicit source in the settings, rather than an ambiguous acquisition reference. No live economy has changed.

Goal: every grade has a visible Forge-crafted +0/full-condition route at its original floor1/26/51/76, with gold and paired material requirements. Keep shop starting ranks and drop conditions unchanged. Add explicit per-family craft settings, source columns, dossier costs and research guidance. Verify all64 entries, the four transition gates, browser source detail and the full suite. Redeploy the static revision and verify it.

Rollback: revert only this follow-up implementation commit and redeploy693d4f7. No database state or live mechanic changes. Execution status: plan recorded before follow-up edits; verification pending.
