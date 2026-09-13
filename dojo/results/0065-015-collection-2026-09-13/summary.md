# Phase 2 browser QA — PASSED (essential delegated gate)

Completed 2026-09-13. Final plugin **0.113.5 / a2608b3ca5b130b9af6e74bf0e8588b88f359a23**; root **9cb56465acdc58e092419c9a745523148937ae27** plus frozen vendor fixes. Full source hashes and restart UTC times: `source-manifest-final.json`. No game/source/plan edits by this QA role. Evidence directory: `/private/tmp/ascent-phase2-browser/001-phase2`.

**No remaining blocker to the essential delegated phase-2 browser gate.** This is evidence for state/collection/School/retry behavior, not a claim that the entire game or phase-7 lifecycle matrix is complete. Earlier failures remain documented below with their rerun outcomes.

## Environment and actual play

Real Luna checkout/runtime with Claude Sonnet 4.5, existing owner `testowner`, existing character BaselineAsh, existing **First Conversation** (`fd4d441b-f48b-4ee6-9de0-19bac6281845`). Safari native browser was used until IAB became available; final query/image used IAB. Conversation export contains24 user messages/39 actual tool calls cumulatively, including baseline; phase2 adds7 user messages/8 tool calls. No fabricated LLM/tool turns.

QA isolation: worldd `127.0.0.1:8860`, Luna `127.0.0.1:8898`; Postgres DBs `ascent_change_everything` and `luna_change_everything`; RedisDB14. Main test DBs and all other QA servers were untouched. Worldd uses `ASCENT_RULESET=collection-v1`, build vendor; Luna image-set symlinks use current plugin and actual chat UI.

## Essential cases

| Case | Result and concrete observation | Evidence |
|---|---|---|
| Legacy conversion | PASS. Slots1→3. Rusted Sword instance `bf947a8284b2fa38d42e2a8723e13351`,5 weapon ATK,1295/1300 condition. Gold45/bank25/XP2/blade2 and armor/shield preserved. | `00-preconversion.json`, `01-converted.json`, `09-final.json`, screenshot04 |
| Reload/no second refund | PASS for this legacy player. Repeated scenes/reloads/server refreshes retained balances and exactly one `slot_refund` row:gold0/XP0. He owned no purchased extra slot, so positive refund amounts are not covered by this browser run. | `03-before-1132.json`, `09-final.json` |
| Exact query after correction, from School | PASS on0.113.5. With current context refreshed and BaselineAsh at School, typed exactly **show me my weapon collection** once. Luna called `ascent_choose` with option6 and opened the collection, then replied “Just the one sword — slots 2 and 3 are open.” | `20-school-final-dom.txt`, `21-final-query-dom.txt`, screenshots20/21, `conversation.json` |
| Real bare-number input | PASS on0.113.2. Typed4 for visible Return to collection. Real `ascent_choose` unassigned the sword while retaining its instance. Subsequent real Luna turn restored it to slot1 and visited School. | screenshot15, `conversation.json`, `09-final.json` |
| Artwork/card and HUD clicks | PASS after0.113.3. Direct web Rare artwork click selected Rare; occupied slot2 selected the second Common copy; WEAPON COLLECTION heading opened collection. Final0.113.5 Luna artwork click also persisted selected Rusted Sword ID and displayed slot-assignment scene in DB. | screenshots17/18, `07-1133-clicks.json`, `09-final.json` (selected ID and scene options), final logs |
| Distinct-copy selection | PASS. Two Common Vipers occupied different cells with IDs `8eddb4bf7a538e6414998dc6b9369d3f` and `f2fdb8a9c4dd892457d248bd5f908ac7`. Attempt to put the same copy in another cell refused: “That weapon is already in your deck”. | screenshots07/08, `04-fixture-deck.json` |
| Image fix | PASS on0.113.5 in actual Luna. Rusted Sword now visibly renders; DOM confirms complete=true,naturalWidth100,naturalHeight160, corrected URL `/api/p/plugin-linear-ascent/art/weapons/large/rusted_sword_100x160.png?v=0.113.5`. | screenshot21, `21-final-image.json` |
| Grade art/frames | PASS visually. Common/Rare/Epic/Legendary use distinct drawings and neutral/blue/purple/gold frames. Fixture stats are synthetic high-floor/grade values, not normal-player economy findings. | screenshots06/19 |
| School | PASS for offers. Real BaselineAsh School has blade/bow/staff training, three always-available battle slots, and no carry-slot purchases. Bow/staff rank1 each20XP+8gold; blade rank3 costs104XP+24gold. Available2XP/45gold cannot buy any lesson. Conditional paid-lesson check therefore not applicable; no purchase or delta claimed. | screenshots16/20, `20-school-final-dom.txt`, `09-final.json` |
| Double-click Deposit half | PASS for actual browser gesture. Displayed550 double-clicked once;1100carried/0bank→550/550; exactly one deposit ledger row gold-550. Server recorded one POST/play/api/act at05:48:42UTC. Browser suppressed a second request, so this is not proof of a two-request backend replay. | screenshots10/11, `05-before-deposit.json`, `06-after-doubleclick.json`, `worldd.log` |
|390px collection | PASS visually at exact390x844 IAB viewport. Three slots and readable two-column cards; expected vertical scroll. Temporary viewport reset. | `screenshots/19-collection-390px.png`, `19-390px-dom.txt` |

Screenshot numbers above map to exact filenames in the manifest below.

## Failures discovered and reruns

1. **Luna denied collection existed** on0.113.0, despite HUD (screenshot02). The first exact-query retry on0.113.2 still answered from stale chat without a tool (screenshot12). Explicit current-scene refresh corrected the denial (screenshot13). Final0.113.5 exact query from School with refreshed context **passed**, opening the collection through option6. This result covers the preserved conversation after correction; it does not claim every fresh or stale conversation will always route correctly.
2. **Collection artwork/HUD buttons were inert** through0.113.2. Numbered rows worked; read-only inspection found `wireOptions` omitted `wc-item`, `wc-slot`, `wc-link`. Main fixed shared selector in0.113.3. Actual artwork,occupied-cell,and heading click reruns **passed**. No QA source patch.
3. **Legacy Rusted Sword image blank in symlinked Luna** (screenshot04). Main fixed canonical realpath URL generation. Final0.113.5 DOM and screenshot21 **pass**.
4. **Synthetic empty-deck fixture triggered old starter apology**: visible Pocket it action refused while100gold appeared (screenshot05; fixture1000→1100). Main reported0.113.5 candidate-only guard and coded regression. No new fixture was created to rerun this lifecycle edge after the final guard; retain as a discovered issue fixed in source with coded verification, not an independently repeated browser pass. Positive compensation/broad asset movement belongs to the phase-7 plan and was outside this delegated phase-2 scope.

## Fixture disclosure

Only new local web account `QACollectionFixture` / player `qacollectionfixture`. Created via local signup, then inserted its new player into the actual QA DB using `collection.mint`:two Common Vipers,one Rare,one Epic,one Legendary,source shop. Explicit grants1000gold and floor100 unlock for grade visibility; empty initial deck. `fixture-grants.json` records every ID/stat and the grant; `qa_fixture_grant` ledger records the setup. No real/player-earned data used or overwritten. The old apology added100gold before the deposit test, making its observed starting balance1100. Final550/550 remains preserved.

BaselineAsh final state: gold45,bank25,XP2,training blade2/bow0/staff0, original gear, deck[RustedSwordID,null,null], selectedRustedSwordID, collection open. HP recovered from75 to80 during elapsed time; no combat or lesson performed in this phase2 run. Sword remains1295/1300. Exactly one zero refund receipt.

## Timing, limitations, and phase-7 scope

Final query user timestamp `2026-09-13 06:00:11.001409+00:00`, tool call `2026-09-13 06:01:52.265711+00:00`, tool result `2026-09-13 06:01:53.559729+00:00`, assistant `2026-09-13 06:01:56.751047+00:00`: **105.75seconds user→answer**. Main reported load averages290/203/118; final restart and browser/commands were slow, and Luna briefly displayed network-error retries during startup. Treat these as measurements under extreme shared host load, not normal latency. No unrelated process was stopped. The final server action returned a valid collection and final answer.

No positive extra-slot refund fixture, broad shop/pawn/pack/delivery/compensation lifecycle, group combat, Forge upgrades, gathering, death or day advancement/interest wait in this bounded run. Phase-7 coverage is planned scope, not a user deferral. Full coded suites belong to main and are not claimed as run by QA.

Earlier phase1 timeout/offline-after-committed-action, plain-Chat pane visibility, and below-fold meters remain documented at `/private/tmp/ascent-baseline-browser/001-baseline/summary.md`; this run does not claim those general issues fixed. On final collection screen the legacy art and slots are visible; lower choices/meters require scrolling. After the final interruption IAB handle became unavailable and native Safari inspection timed out; saved screenshot21/DOM plus final DB verify the completed query/image/artwork action. No further broad browser work attempted.

## Servers preserved and exact launch commands

Final owned PIDs: **worldd34825**, **Luna34826** (authoritative `/private/tmp/ascent-change-qa/pids.json`). Final health observed0.113.5,db=true. Only this QA's PIDs were restarted. Original prior servers and DBs were preserved.

```sh
/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/.venv/bin/python /private/tmp/ascent-change-qa/serve-worldd.py >> /private/tmp/ascent-change-qa/worldd.log 2>&1
/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/.venv/bin/python /private/tmp/ascent-change-qa/serve-luna.py >> /private/tmp/ascent-change-qa/luna.log 2>&1
```

Actual launch used Python `subprocess.Popen(start_new_session=True)`,cwd`/private/tmp/ascent-change-qa`; launchers exec the specified worldd and actual Luna venvs. Worldd port8860,Luna8898. Allowlisted env and local-only credentials are loaded privately; values never printed. Rollback is `/private/tmp/ascent-change-qa/ROLLBACK.md` (stop only owned PIDs; preserve progressed QA data). Launchers,pids,logs remain in QA directory. Evidence exports redact secret values.

## Exact screenshot paths

- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/01-first-query.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/02-collection-open.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/03-collection-1131.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/04-selected-legacy.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/05-fixture-delivery-refusal.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/06-fixture-grade-grid.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/07-duplicate-refused.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/08-two-common-copies.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/09-fixture-school.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/10-vault-before-doubleclick.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/11-vault-after-doubleclick.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/12-exact-query-1132.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/13-explicit-refresh-correction.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/14-narrowest-native-window.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/15-luna-bare-number.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/16-luna-school.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/17-web-art-click-1133.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/18-web-slot-click-1133.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/19-collection-390px.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/20-school-final.png`
- `/private/tmp/ascent-phase2-browser/001-phase2/screenshots/21-final-luna-collection.png`
