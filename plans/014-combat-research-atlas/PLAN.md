# Combat research and visual atlas

## Problem and evidence

The 11 September 2026 weapon research proposed only three weapon families across four grades. The follow-up requests more tactical families, orthogonal flying/ground and Common/Power/Magic monster traits, arrow damage conversion, partial shield protection, statuses, movement, and a readable visual reference. Inspection finds that shield wall explicitly prevents all damage, while ordinary defense already has a 25% chip rule. Flight is currently one mutually exclusive monster type; poison and slow arrows already exist, while fire arrows are an immediate damage multiplier.

## Root cause

The first proposal reduced catalog breadth before defining new combat decisions. Existing type and effect schemas cannot directly express flying Power/Magic combinations, and shield wall takes a separate zero-damage path.

## Emergency mitigation

None. No game behavior will change in this task.

## Goal and scope

Produce a short but specific research plan with monster, weapon, status, and progression tables. Build a separate HTML reference site with those definitions, interactive matchup/defense/progression examples, current-versus-proposed labels, and source links. Preserve the prior material and continuously healing warden direction. Mining remains a separate project.

## Execution steps

1. Commit this plan before site implementation. Leave unrelated working-tree and index changes alone.
2. Record the short design proposal under `research/combat-atlas/PLAN.md`; use explicit assumptions where statements conflict. Catalogue current formulas with source references.
3. Initialize the independent Site checkout at `research/combat-atlas/site/`, author shared data, build the visual atlas, reuse existing repository art, and copy the short plan into downloadable site content.
4. Check model arithmetic and representative interactions; build the complete site. Perform the site-specific browser walkthrough below. This is a reference artifact, not an implemented game plan; live Luna combat cannot verify proposed mechanics that do not exist yet.
5. Publish the completed site privately through Sites, verify final deployment status, and append execution results here.

## Verification / dojo scenario

**Preconditions:** Site is running from this task's checkout with proposed data, no live game connection.

**Scenario:** Open the atlas in a real browser. Change monster type and weapon/arrow selection; inspect the damage result and source badges. Open a weapon's details. Exercise shield controls at low/high defense. Inspect upgrade levels 0 and 20 for all grades. Navigate at desktop and narrow viewport sizes.

**Expected:** Controls and tables use the same data. Common/Power/Magic and Ground/Air are distinct. Colored symbols have text labels. A shield always leaks damage on a landed ordinary hit; stronger defense blocks more and wears by the blocked share. Level/grade changes update exact cost/material/stat values. Proposed results are clearly labeled. All content remains readable.

**Fail conditions:** Stale calculator values; a zero-damage shield result for a landed hit; missing/unreadable content; mixed current/proposed values; keyboard-inaccessible controls; broken assets; any live-game mutation.

**Verify:** Record checked interactions, arithmetic results, screenshots, build/deployment results, and limitations in `research/combat-atlas/VALIDATION.md`. Future runtime implementation still needs its own committed phases and actual Luna gameplay dojo.

## Rollback

Before publication: remove only the new `research/combat-atlas/` artifact tree and revert this plan's own commit. After publication: retain source and use the Site's deployment history/access controls to withdraw or replace the reference; do not alter the game service. No game database, active warden, player inventory, or vendored engine is changed.

## Operational notes

The Site is an isolated repository for publishing. Only that source is uploaded; no surrounding project, account state, secrets, or live player data belongs in the archive. Secret-pattern scan before each commit. Keep a private audience unless requested otherwise.

## Execution status

Plan recorded; implementation not started.
