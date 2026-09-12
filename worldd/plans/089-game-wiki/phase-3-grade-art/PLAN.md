# Phase3 — four distinct drawings per weapon family

## Problem and evidence

12 September2026: the user reports Common/Rare/Epic/Legendary weapons show identical images. `model.json` has one `art` slug per family; `gen_wiki.py` generates one `image`; arsenal, Forge, source table and details all read it. Frames differ but the weapon never does. The shipped catalog contains85 distinct large weapon portraits, suitable for most of the required64 assignments; only one conventional hammer portrait exists.

## Root cause

Rarity was modeled in stats and frames without a grade-specific art mapping.

## Goal

Every one of16 weapon families displays four genuinely different drawings (64 distinct assignments), visible in monochrome. All grade-dependent surfaces agree. A weapon's detail panel shows the four designs side by side, so comparison is immediate. Common looks rough/simple, Rare professionally forged, Epic elaborate/charged, Legendary exceptional. No new combat, acquisition or economy rules.

## Steps

1. Commit this phase and its browser scenario before edits. Reuse the existing wiki checkout/branch on latest main; preserve unrelated original-workspace changes.
2. Audit the existing sprites. Use explicit per-grade asset and visual-description records; preserve each family's recognizable role. Generate three missing maul sprites with the built-in image tool and save its original outputs plus prompts in this workspace. Keep source art untouched.
3. Resolve grade images in the generator and every renderer: arsenal, Forge, source table, detail portrait and a four-grade comparison. Add readable alt text. Bump wiki revision and regenerate the bundle.
4. Validate all64 asset files, per-family/global uniqueness, image silhouettes, old-image fallback removal, and unchanged numeric model. Run targeted then full suite. Walk a blade, bow, staff and maul through all grades in the browser; inspect the source table, details, Forge and phone comparison.
5. Commit, push, explicitly deploy on the existing game host, and verify the published revision and actual grade changes. Record execution results.

## Verification

First user action: open `/wiki#arsenal`, choose a weapon and switch Common/Rare/Epic/Legendary. Four weapon drawings must change, even with color ignored. Open its detail and inspect all four together. Forge and each acquisition row must select the same grade's drawing. Phone390px must keep all four designs accessible without page overflow. Existing settings/calculation tests still pass; this is a public reference-only visual change, so no Luna/game action is changed or claimed tested.

## Rollback

Before commit restore edited tracked files from7063488 and remove only new phase-owned asset files. After commit revert the recorded art implementation commit and explicitly redeploy. Original art and player state require no restoration.

## Operational notes

Canonical existing art is the vendored game's portraits. New mauls are wiki-owned proposal assets for eventual game adoption. Their original generated files are copied into the project; never depend on a temporary image-generation path. Presentation changes must not alter acquisition levels, durability, prices, loot or damage formulas.

## Execution status

Implemented and locally verified. 64 distinct PNG drawings and 64 normalized alpha silhouettes; all grade-dependent surfaces share the same lookup. Four targeted Python tests, six Node tests and the full224-test worldd suite pass. All mechanics and acquisition data compare equal to7063488 after excluding revision and art fields. Browser scenario14 passed at desktop and390px; report: `dojo/results/0066-089-weapon-grade-art-2026-09-12/summary.md`. Publication verification pending.
