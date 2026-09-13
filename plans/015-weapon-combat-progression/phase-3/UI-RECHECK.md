# Browser corrections after frozen0.114.0

Evidence: `/private/tmp/ascent-phase3-browser/001-phase3/findings.md` and screenshots03–06. The natural web player cleared the first group with no grants:50→82 gold,0→4 XP,80→78 HP and2 energy paid. Reload did not duplicate loot. The browser agent paused at this safe result scene; fresh Luna is in town and BaselineAsh is unchanged.

Correct the observed issues before continuing phase3:

1. Sort owned card payloads by selected deck cell, then grade/family/level/identity for other weapons. JSONB object order must not reorder the displayed deck.
2. Give group buttons their own vertical label/hint layout, remove inherited dot leaders and duplicate numeric brackets, and preserve click/keyboard/plain-number behavior. Forge buttons get explicit keyboard choice numbers.
3. Include every preview member's name/type/reach/stats and pending haul in the plain-text scene consumed by Luna, matching the web card.
4. Replace candidate hunt/deep map chip costs with “1 per enemy” and a free-preview explanation. Candidate meter tooltips must state saved surplus XP and per-enemy/gather energy, and describe the current death policy accurately.
5. Use the existing floor landscape banner at each gathering site; retain place names and the already-authored site text.

No combat, RNG, prices, grants or settlement changes are intended. Verify targeted rendering/core/map/pane tests and full suite follow-up, then restart the same QA launchers preserving state. Resume the same browser evidence run; recheck desktop/390px, a numbered combat reply, and ask Luna to describe the remaining group.

Rollback: this patch changes presentation and ordering only. Revert its recorded plugin commit and re-vendor/restart the same QA processes; preserve all player documents. A source hash change requires a new simulation run/replay comparison before claiming identical recorded output. The underlying0.114.0 group readers stay installed.

## Implemented correction checkpoint

Plugin d49adf1 (0.114.1) implemented the six presentation/text changes above. Its full suite caught a public-avatar regression caused by tooltip variable scope;7a00177 (0.114.2) fixes that separate read-only renderer. The latest full plugin run is1481 passed,8 known legacy failures,4 skipped,1 expected failure in32.37s. Focused map/renderer/group tests passed91 checks plus the new roster/ordering contract; public-avatar/renderer/group checks passed39. Simulator62 and HTTP8 checks passed on0.114.1; a matched0.114.2 smoke is running. No tuning or reward law changed.

QA has been restarted with0.114.2, same progressed databases, and tenant `ascent-change-phase3` for the separate natural Luna character. BaselineAsh remains under `ascent-change-baseline`. Current owned process IDs are recorded in the local `pids.json`; do not assume an older recorded PID still identifies a QA process. Browser resumes from the pending first Luna enemy and the web camp, not from reset characters.

Exact presentation rollback: `git -C plugin-linear-ascent revert 7a00177 d49adf1`, then `bash worldd/tools/vendor_game.sh` and restart the same owned QA launchers. It retains0.114.0 group/collection readers and all earned state. This rollback is distinct from reversing the original group-engine migration.

## P3-005 — stale standing combat advice (pre-execution)

Browser evidence09 records Luna saying a Cover shot doubles damage and a blade can reach from Cover. Source review on13 September found `_GUIDE_RULES` in plugin.py explicitly instructing the obsolete cover-shot double, old single-weapon start, flat fight energy and outdated fixed prices/death loss; `_SHARED_RULES` also hardcodes the old first training fee. Group technique hints currently repeat only their names, omitting the real20% bonus. This is a guidance contract defect, not evidence to change the resolver.

Correct the standing instructions to obtain facts from the current scene/character data rather than a second rules table. Explain independent reach/affinity for collection battles and preserve old-player behavior by reading the scene. Put each family technique's exact description in its current action hint and include current gap/reach requirements in the scene text. A request to explain combat may receive the requested short explanation rather than being suppressed by the one-line flavor rule.

Verification: shared tool payload/scene tests and focused group rendering checks, full plugin suite (separately identify established legacy failures), frozen-source simulator outcome comparison. Restart owned QA Luna as tool registration changes, preserve accounts/fixtures, then repeat the actual explanatory question in the existing conversation and finish the ongoing walkthrough. No gold, damage, energy, prices, loot or RNG changes.

Rollback: revert the recorded guidance-only plugin commit, vendor and restart the same owned QA processes; preserve all progressed state. Restart procedure remains the QA ROLLBACK.md. This note is committed before the code change.

P3-005 implementation: plugin3f8d2b2/version0.114.3,32 focused checks passed; full1482passed/8 established legacy failures/4skipped/1xfail in38.62s. QA health confirms0.114.3. Matching eight-player ten-day run20260913T070656Z-cd6a13b3 has the identical semantic digest fef26f696cf2b69be63d64210ff8fac4bffd3bc2f2bf5bbe2b3168132e6536fc; the guidance patch changes no progression outcome. Browser explanatory recheck pending. Guidance rollback: `git -C plugin-linear-ascent revert 3f8d2b2`, re-vendor and restart only owned QA processes.

## P3-006 —390px generic option hints (pre-execution)

Main opened the real QA /play page with cached Chromium at390×844, separate declared `web:phase3mobile` fixture. Screenshot /private/tmp/ascent-phase3-mobile/01-camp.png shows Drowned Copse and Bog-Iron Field tool requirements clipped to the right; .opt .hint is forced to white-space:nowrap and its row cannot fit the new descriptive hints. The group-specific buttons already wrap without overflow (312px action grid,151px button content/scroll width). This is a separate presentation defect; the native Safari functional pass continues on0.114.3.

Fix only candidate collection-scene generic option rows at narrow widths: key/label first line, wrapping hint below; remove the dot leader for these rows. Preserve labels, action IDs, number selection, keyboard handling and old-player row behavior. Give native group button content a consistent top alignment. Verify actual390px camp/gather/selected collection, Forge grade/catalog and battle screenshots with no clipped text; rerun existing rendering tests and full plugin gate before freezing. No new economic grants to natural players.

Rollback: revert the recorded CSS/marker plugin commit, vendor and restart ownedQA; preserve all player state and fixtures. Browser fixture setup/cleanup is documented before writes in /private/tmp/ascent-change-qa/MOBILE-CHECK.md. Temporary session cookies are excluded from repository/evidence.

## P3-005 follow-up / P3-007 route discovery — pre-execution

The0.114.3 exact-question recheck still repeats prior false reach advice without refreshing the scene. After explicit refresh it correctly identifies blade reach but treats named Cover as outside numerical distance2–3. Screenshot22 establishes ambiguous numbered-gap guidance. Screenshot27 records denying a gathering route from town; source sheet.py exposes collection but no resource-site directory. Only already-arrived camp options disclose the sites. These are remaining advice/discovery defects, not reasons to alter combat math.

Add named Far/Cover and exact numerical mapping to authoritative group hints/text, and a current action-specific reach sentence for every selected weapon. Require scene refresh for questions about current monsters/actions; allow requested explanations in the tool's top-level description as well as its returned instructions. Expose available gathering sites from engine definitions on the character sheet and selected material quotes, with floor/tool/resource and entry action; named-location requests must consult those records before denying access. Keep node navigation through current legal options; do not hardcode a sequence that bypasses locks.

Verify tool payload/character-sheet/group contracts, then re-ask the exact question without a leading correction and request Drowned Copse from town in the same Luna conversation. Prior failures remain recorded. Rollback is guidance/discovery commit revert, vendor/restartownedQA preserving state. Include this fix with the next frozen build rather than restart for each wording edit.

The0.114.5 full service run found the existing baked-wiki equality check stale after the candidate version bump. `test_089_wiki.py` compares the entire generated payload, including gameVersion and versioned assetURLs. Re-run the existing generator now and its four wiki checks; the full candidate-rule wiki rewrite remains phase4. This updates the current legacy-data/proposed-model build stamp only, not claims that the old research model is the new resolver. Rollback is regenerate after reverting the version or revert the data.json-only commit. The service-wide failure and successful targeted recheck must both be recorded.

Combined checkpoint: plugin e029396/0.114.5 (includes c062bee material/mobile patch) passed1512 plugin checks, with8 established legacy failures,4skips and1xfail in102.78s.70 focused contracts and6 candidateCPU/replay checks passed. The immutable ten-day run20260913T072311Z-0fc0d4bc source79692d78ed522316ae518f5e0c30677945cb2a811c826ff55bb3e71574d7c95d replays both captured traces exactly (1055 and2313actions). Its milestones,counters,timelines and owned resources match0.114.4; the stored scene text/route metadata differs, so semantic state hashes correctly differ. Evidence lives in simulation/verification/007. The initial0.114.5 full-plugin attempt was interrupted while a missing camp-hint edit was added; only the completed full-final log supplies the1512pass count.

QA restarted with preserved databases and0.114.5. Browser rechecks resume from naturalLuna's floor3camp; no grants/reset. Main's independent390px fixture persists for mobile verification. Guidance rollback: revert e029396 before c062bee if reversing both; preserve all new-format state and rewards.
