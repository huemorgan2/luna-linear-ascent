# Phase 4 — Full arsenal, bestiary and routes

## Goal

Expand the working group loop to all 16 families / 64 grade variants and 425 authored creatures, with meaningful unequal niches, readable images/traits, valid sources and a matching generated wiki.

## Steps

1. Port approved family/grade/source/art records from wiki model revision089.3 into canonical runtime definitions. Extend lint/schema checks for distinct images, material/icon/frame mapping, grades, +0–20, probabilities and source gates. Preserve the original creature roster and neighboring variant/biome identities.
2. Implement all seven effects and six arrow payloads, source snapshots, exact timing, immunities, cooldown carry-over, control resistance and condition-dependent stats. Avoid double old/new type multipliers, double exhaustion and percent-max-HP boss damage. Preserve the resolved channel/cause for resistance popups across ordinary/arcane/fire arrows, damage ticks and Spell dispersal; the icon follows the actual resisted component, not the weapon family or defender badge.
3. Author groups/trails over floors1–100 using real local creature IDs. Candidate ranges: 2 on1–3; 2–3 on4–10; 2–4 on11–25; 3–4 on26–50; 3–5 on51–75; 3–6 on76–100. Keep shorter later routes. Do not multiply count by old full-monster threat/payout blindly.
4. Configure group arrival gaps and durable/fragile/fast roles. Ordinary and deep mode use one energy per begun enemy; deep danger, specimen mix and each rarity premium remain separate. No hidden deck-dependent counter-spawning or free preview rerolls.
5. Wire per-enemy independent material grades and categorical item rolls with actual family/carrier weights, source-specific +level/condition and Forge crafting at grade transitions. Update all reward, pawn, storage, trade/gift and equipment consumers.
6. Generate wiki/art payloads from the runtime definitions, with full creature parameters, individual/group conditional odds, deck coverage, acquisition and Forge recipes. Mark any unreleased settings as proposed. Audit avatars/3D weapons and fallback images so grade selection does not revert to one drawing.
7. Prove each family has a useful tested context; document blind spots and cost. Do not require equal win rates. Two-active-enemy waves remain an optional future prototype outside the release gate.

## Verification

Run content lint and `python3 worldd/tools/gen_wiki.py --check` after the generator reads runtime definitions; add exact distribution tests for caps/no-drop/family weights and integer/rounding tests for statuses. S04/S05/S07/S12 verify contrasting decks, push→bow/escape, poison→switch, repeated stun resistance, source gates25→26/50→51/75→76, paid Legendary+6 versus dropped+0/10%, all425 IDs/images and floor-slider changes. Review a coverage table per family/route and group duration/action distributions. Required full engine/service/simulator suites follow targeted tests.

All commands are future implementation verification, not actions performed by this planning revision. New test/tool interfaces named conceptually must be implemented and their actual commands recorded before use. Never point worldd tests at production. See [scenario index](../DOJO-SCENARIOS.md).

## Rollback

Revert candidate content/effect/art/wiki commits in QA in reverse order while retaining state compatibility. Pin the prior content/rules revision for already-started groups and outstanding quotes; never reinterpret pending loot with a different probability table. Keep newly owned item records readable and reconcile any necessary conversion through receipts.

For each implementation commit, record its exact SHA and the reverse-order `git revert` sequence before starting the next phase. Data-changing operations require their tested compensating commands and receipt IDs before execution. Keep all new-format data readable.

## Operational notes

Follow the [parent plan](../PLAN.md) and its ownership map. No new production rules during phases2–7. Run targeted checks before full relevant suites; preserve existing work and source-pinned evidence. A real browser/Luna walkthrough is required before reporting an implementation phase complete.

## Execution status

In progress,13 September2026. Plugin8b26030/0.115.0 completed the candidate effect/arrow/mastery rules, varied arrivals and all8 resource sites. The wiki now generates425 creatures,64 distinct weapon drawings,1344 upgrade states,3400 specimen/mode drop records and8sites directly from the game. Full worldd suite233passed (269.43seconds); initial plugin1534passed with8pre-existing failures,4skips,1xfail. Wiki model7passed and Python5passed. Actual desktop and390px browser checks show floor-dependent creature images, distinct grade art and working visible grade/hunt selectors, with no horizontal overflow or console error. Curated browser evidence and remaining coverage follow before closure.

The first0.115.0 Luna arrow question failed (P4-001): no tools, then denial even after an explicit refresh returned the quiver. Plugin56e1d86/0.115.1 adds a visible owned-arrow drawer, resolved per-bow selection, six exact payloads/quotes and current-data coaching.54focused and1535full plugin tests pass; the same8legacy failures remain phase7 work. QA restart/recheck pending at this checkpoint; preserve natural character and all earlier fixtures.

The first opening simulation aborted because its disposable readiness setup retained the new quiver-shop view. Plan971d160 records reproduction before correction.17focused/65full simulator tests pass after the fix;8players×10days completed in20.9167seconds on4workers. Median readyfloor8, only1player reaches10 at8days: pacing still misses the reviewed goal. Source-pinned results and limitations are in simulation/verification/008. This is not phase5 tuning or100-floor evidence.

Rollback before the next phase: root integration changes can be reverted from their recorded checkpoint, regenerating vendor/wiki from the matching plugin. Plugin56e1d86 may be reverted for the discovery-only presentation/coaching, while retaining8b26030 readers for already-owned arrows/effects and existing pinned group readers. Never overwrite earned documents with QA snapshots. Required remaining phase4 gates: corrected Luna discovery, real effects/late-site play, and measured family/site niches. No production deployment or whole-plan completion claim.

Checkpoint e44998d/0.115.2: actual slow speed now governs pursuit/withdrawal/escape/display; all8sites appear by name/material at the Gate. Dedicated ascent_arrows opens a current, free drawer and returns all6payloads.67focused plugin checks and1539full pass (same8trackedfailures); wiki5Python+7JS checks and65simulator checks pass. Source and vendor match. Durable QA databases snapshotted and owned8860/8862/8898 restarted with unchanged players. First-query recheck in progress.

Prepared experiments009 cover11,776two-enemy fights,512unhoned site/hunttrips,512honedcomparisons and complementary Ramguard/Frostbind/Runestring/passive cases. All16families have a demonstrated conditional damage/control/HP/action niche; no equal-win-rate requirement imposed. Site returns exceed matching hunting across8targets with prepared honeddefenses; floor25/45/55deathrates remain poor and are phase5preparation/policy findings, not hidden. Natural10dayopeningstillmissespacing.

Dojo0067 preserves browser002 failures and passing combat/material/arrow evidence. Separatefloor80 realbrowser secured10Threads via6paidattempts and one extraction receipt, reloadstable. CorrectedGate hint fits390px with zerooverflow. ExactLuna discovery and final wiki screenshot review remain before phase4closure. Rollback plugin e44998d with matching vendor/wiki; preserve owned materials/arrows, pinned combatv1 groups and original failed evidence.

Implementation gate passed13September2026, e44998d: first-query freshdata/all6payloads and separate actualdrawer, natural freepreview/Arcane/exit, actualslowmovement/escape, Gate/mobile/wiki and all16family niches verified. Dojo0068 contains the correction evidence;0067 retains failures. Main judged actualscreenshots and resource snapshots. No claim of completeLunaUI/actioncap/migration or all100floorpacing; those explicit phases remain open. Phase5 may now implement committedaa3c579policyplan. Reverseorder rollback of discoveryonly: rootfa3e16c vendor/wiki thenplugine44998d (retain0.115readers andearnedstates).
