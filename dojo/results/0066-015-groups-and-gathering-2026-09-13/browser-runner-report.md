# Phase3 bounded browser report — 0.114.5

**Core first-natural-upgrade gate: PASS; CLOSED by main after personal review of the natural +1, reconnect and mobile evidence.** Main curated and committed the underlying phase3 evidence at root **1dac285**. Two Luna guidance findings remain filed for phase7/4 follow-up: **P3-008** (gather-count overrun) and **P3-009** (trait omission/false absence claim). This bounded phase3 assignment is finished; the broad game and every planned scenario are not declared complete.

Final handoff: QA remains frozen on **0.114.5 / plugin e029396**, with matching vendor. Main has begun separate phase4 local source edits. No additional browser actions, source tests or server restarts were performed for this handoff. Root1dac285 is the later evidence-curation checkpoint; the source hashes below record what was actually exercised.

Run date:2026-09-13. Same natural players, real Luna conversation, fixtures and result folder throughout all main-agent-requested pauses. No source edits, restart, fixture recreation, earned-player reset, personal grants or clock advance during this slice. Servers remain running.

## Source, environment and preserved servers

- Frozen plugin **0.114.5 / e029396395b9ddb90d7f00379ae5f947c105b9e1**. Plugin worktree clean at final check.
- Root at slice start: **8e90245bfd66ac212396b23a2d2d32613af56978**. Main committed integration/wiki/plans during the run; root at report check: **c181fbafa61b2fc4a6a97717c39e73bdeebc8eee**. All **147** audited plugin/vendor Python/JSON/YAML files match and remained byte-for-byte unchanged during this slice. [Final hashes](/private/tmp/ascent-phase3-browser/001-phase3/source-parity-final-01145.json).
- QA **worldd PID53642,127.0.0.1:8860**; **Luna PID53643,127.0.0.1:8898**. Both started2026-09-13 10:23:58 local /07:23:58UTC by main. Final health/page checks200.
- Ruleset collection-v1; DBs `ascent_change_everything` and `luna_change_everything`; Redis14. Avoided main's test/local-backend DBs and other processes.
- Actual Luna checkout `/Users/roy/Documents/my-projects-docs/luna`, real Claude Sonnet4.5 provider/login/conversation. Natural tenant/player `ascent-change-phase3:owner`, conversation `60d7a0a6-1771-4b5e-a105-3d9364325c7f`, title **hunt a monster group**.

Preserved launcher commands (keys loaded locally without printing values):

```sh
/Users/roy/Documents/my-projects-docs/luna-linear-ascent/worldd/.venv/bin/python /private/tmp/ascent-change-qa/serve-worldd.py
/Users/roy/Documents/my-projects-docs/luna/.venv/bin/python /private/tmp/ascent-change-qa/serve-luna.py
```

Actual processes execute uvicorn `app.main:app --app-dir /private/tmp/ascent-change-everything/worldd --host 127.0.0.1 --port 8860` and `luna_serve:app --app-dir /Users/roy/Documents/my-projects-docs/luna --host 127.0.0.1 --port 8898`. Owned PIDs also recorded in `/private/tmp/ascent-change-qa/pids.json`.

## Current rerun results

| Case | Verdict | Evidence and observed behavior |
|---|---|---|
|Exact roster question at new free preview|PASS for roster/reach; separate trait issue below|Repeated exact “Describe the remaining monsters in this group, including their types, reach, and condition. Do not attack yet.” Two Marsh adders, correct stats, Far(2), bow/staff reach and blade Contact requirement. Used the immediately preceding actual preview result; no extra tool call on the explanation turn. [28 screenshot](/private/tmp/ascent-phase3-browser/001-phase3/28-luna-exact-roster-01145.png),[exact trace](/private/tmp/ascent-phase3-browser/001-phase3/28-exact-query-trace.json).|
|Preview then exit free|PASS|group:9 remained uncommitted, no enemy_start/energy receipt, no gold/XP/HP/wear change. Snapshots20–22. No additional ordinary group was fought in0.114.5.|
|Natural Drowned Copse discovery/tool route|PASS; P3-007 resolved in this instructed route|Luna left preview, entered site, bought35gold Wood axe there and began new expedition in4 game actions. Gold259→224. [29](/private/tmp/ascent-phase3-browser/001-phase3/29-luna-natural-axe-expedition.png),snapshot22.|
|New gathering yield|PASS|New expedition records yield_amount2; six Wood from9 attempts (6empty,3yield), then2RawMetal from1attempt. No ambush,10energy charged,10tool wear total. [30b](/private/tmp/ascent-phase3-browser/001-phase3/30b-natural-pending-wood4.png),[33](/private/tmp/ascent-phase3-browser/001-phase3/33-natural-metal2-pending.png),snapshots23–25.|
|Natural safe extraction and second tool route|PASS|Wood secured once; Bog-Iron entry/pickaxe45gold/begin in exactly3actions; one requested metal attempt made exactly1action; second haul extracted once. Gold224→179; both materials secured before Forge. [31](/private/tmp/ascent-phase3-browser/001-phase3/31-natural-wood-extracted.png),[32](/private/tmp/ascent-phase3-browser/001-phase3/32-natural-bog-iron-ready.png),snapshot26.|
|Natural Forge +1 / actual artwork click|PASS|Clicked Hawkeye artwork, inspected exact affordable quote, clicked upgrade6. Same canonical ID upgraded once;179→8gold,Wood6→0,RawMetal2→0. [35 quote](/private/tmp/ascent-phase3-browser/001-phase3/35-natural-affordable-hawkeye-quote.png),[36 upgraded card](/private/tmp/ascent-phase3-browser/001-phase3/36-natural-hawkeye-plus1.png),snapshot27.|
|Read/reconnect after upgrade|PASS|Reload retained +1. Actual ascent_character returned current balances, materials, stats and resource-site routes. Only last_seen changed; ledger and gameplay state unchanged. [37 reconnect](/private/tmp/ascent-phase3-browser/001-phase3/37-natural-plus1-reconnect.png),[38 read](/private/tmp/ascent-phase3-browser/001-phase3/38-natural-plus1-authoritative-read.png),[read trace](/private/tmp/ascent-phase3-browser/001-phase3/38-character-read-trace.json),snapshot28.|
|Overall six-action cap per asked turn|PASS, with narrower-count FAIL|Nine intentional0.114.5 turns; game-action counts1,0,4,6,4,3,1,4,0. Actual narrower two-gather limit failed as P3-008. Two additional direct UI clicks inspected/upgraded the bow.|
|390px|PASS, MAIN-REPORTED|Main's settled screenshots09/10/11 show camp/gather/battle:332px options,151px battle, no overflow; wrapped tooltips,3cells fit. Main returned its separate fixture free to camp and closed context. These are main's captures, not this role's Safari screenshots. P3-006 resolved by main's rerun.|

P3-005's previous reach failure is corrected in28. The preview tool text explicitly says Cover shot adds20% at Far(2)/Cover(3), bonus applies here. The exact question's reply did not discuss the technique bonus, so no separate claim of a newly tested freeform bonus explanation.

## Exact natural outcome and cost

Final read/DB checkpoint **2026-09-13T07:36:01.911803+00:00**:

| Property | Final value |
|---|---|
|Player / scene|Phase3Luna, s122, town Forge collection, floor0, frontier3|
|Gold / bank|**8 /0**|
|XP / reserve|**13 /0**; level1; training blade2,bow1,staff0|
|HP|**58/80**|
|Energy|**1/25 displayed**; stored1.146876300740744, with normal real-time regeneration active|
|Materials|**0Wood,0RawMetal** after purchase|
|Tools|Wood axe91/100;Iron pickaxe119/120|
|Upgraded weapon|**Hawkeye Longbow Common+1**, ID`ca244e21392326f61e3672473bf2b992`|
|Weapon stats|ATK9→11;condition1272/1300→**1304/1332**, retaining28points of wear|
|Other starter weapons|BreachCleaver+0,1170/1170;EmberStaff+0,1293/1300;deck IDs unchanged|
|Pending state|No group,expedition or unbanked haul|

The natural opening spans0.114.0–0.114.5. Earlier earned state included **7ordinary group clears**,223gold gross,33XP, and the paid School bow lesson (**14gold+20XP**,rank0→1). The0.114.5 continuation began with259gold,13XP,58HP and no tools/materials. It spent35+45gold on tools and171gold on the upgrade: **259−35−45−171=8**. No further gold or XP was earned during this gathering-only continuation.

Drowned Copse rolled empty,empty,empty,empty,yield,yield,empty,empty,yield; all3yields gave2Wood. Bog-Iron's first attempt gave2RawMetal. Two extraction receipts and one upgrade receipt. Tool purchase through upgrade took **5m19.8s** (07:28:55.049→07:34:14.880UTC). First query through upgrade took **52m55.7s**, including main-requested pauses, build changes and QA inspections; this is not a measure of uninterrupted player time. No manual clock change, waiting for a refill, personal energy/gold/XP/material grant or extra hunting was used for the0.114.5 finish.

The only natural-access fixture was the earlier explicitly declared **QA world frontier1→3**. It enabled access to the authored sites; natural personal resources were earned. This result proves this preserved player's first upgrade path, not the distribution of fresh-player outcomes or unassisted discovery from town.

## Open Luna guidance findings

**P3-008 — count overrun, FAIL.** Requested at most2additional gathers then extraction. Luna made **3gathers (+1 over request), then1extraction:4game actions total**, still within the overarching6-action cap. Attempts6→9,axe94→91,energy5.09368→2.11636,4pendingWood→6secured. Exact request/timestamps/tool arguments: [31-gather-count-overrun-trace.json](/private/tmp/ascent-phase3-browser/001-phase3/31-gather-count-overrun-trace.json). Subsequent metal request used exactly1gather; this does not erase the failed2-gather limit. Main should address narrower action-count tracking. No repair or repeated test by this role.

**P3-009 — trait omission and unsupported absence claim, FAIL.** Both previewed Marsh adders were runt specimens with **frail+feeble**:2labels per enemy,**4stored labels across2enemies**. Luna named **0/4** and said “Both adders are ground beasts with soft defenses and no special traits.” The actual scene_text omitted those trait labels; DB retained them. Keep this separate from corrected reach. [Trait evidence](/private/tmp/ascent-phase3-browser/001-phase3/28-trait-omission-evidence.json),[screenshot28](/private/tmp/ascent-phase3-browser/001-phase3/28-luna-exact-roster-01145.png). Main should expose specimen traits and avoid asserting absent traits from omitted fields. No repair or rerun by this role.

## Earlier completed evidence retained

These bounded checks remain source-specific passes from0.114.0–0.114.3 and were not repeated after main's instruction:

- Fresh exact first query, authored3weapon opening, real Luna multi-turn numeric choice, actual card click, current-scene read and reconnect. Screens01,03,09/10.
- Natural web two-enemy clear:gold50→82,XP0→4,HP80→78,2energy;single settlement/read. Screens05/06/08. Collection ordering and group button rendering fixes passed desktop in10/11.
- Paid natural School lesson:243→229gold,23→3XP,bow0→1;no slot purchase. Natural floor3group then229→259gold,+10XP,no material drops.
- Declared5-enemy/2energy fixture:2funded+3exhausted,full settlement once. Five-energy retreat after2kills retained XP and secured resources, lost only pending haul. Screens12–15.
- Declared resistance/partial-shield fixture:Magic-resisted4damage;shield leaked26then27HP,wore1000→998. Pending fixture combat preserved. Screens16/17.
- Declared old-rule gathering ambush/zero-energy extraction/reload/HTTP retry, fixture Forge upgrade/double-click and new catalog instance. Screens18–26; supplemental23HTTP JSON. Old4Wood haul was1gather+1drop+2ambush bonus, not a new four-unit ordinary drop.

Exact source table, older verdict details, fixture grants and remaining broad coverage: [0.114.3 checkpoint](/private/tmp/ascent-phase3-browser/001-phase3/summary-checkpoint-01143.md),[findings](/private/tmp/ascent-phase3-browser/001-phase3/findings.md),and`fixtures/`.

## Preservation, limits and evidence

**BaselineAsh's entire row remains exactly unchanged** from00-before-identity, including timestamp. Phase3Sprout,Energy2,Energy5,Shield andGather rows remain exactly unchanged from the0.114.5 starting snapshot. No earlier pending group/fixture reset; Phase3Shield intentionally remains in combat with27HP. [Final checks](/private/tmp/ascent-phase3-browser/001-phase3/final-checks-01145.json),[full final snapshot](/private/tmp/ascent-phase3-browser/001-phase3/snapshots/28-final-natural-read-reconnect.json).

Main reported exact0.114.5 plugin1512pass/8known legacy failures; worldd231pass with only stale wiki stamp, then all4targeted wiki checks passed after generator refresh; replay traces1055/2313bothtrue. These are main's coded checks, not suites rerun by this browser role. Main subsequently reviewed the settled mobile captures, curated the evidence at root1dac285 and closed the core phase3 gate; broad game completion remains outside this verdict.

No additional broad scenarios: complete death/rescue/Stone matrix; every status/control/affinity; broken-tool extraction; remote stale deck writes; all lifecycle/compensation/asset movement cases; all recipes/grades; natural new ordinary-monster bundle payout. The0.114.5 preview exposes bundle definitions but no new ordinary kill/drop was executed. Those limits remain explicit; no claim of full plan completion or user deferral.

The entire real phase3 conversation contains25user turns/143tool calls. This includes one unintended unrelated clipboard message (“Save crop…”), which called memory.remember and caused no game action. Subsequent input was AX-verified before Send. The intentional0.114.5 slice contains **9user turns/29tool calls**, including23ascent_choose actions and the final read. [Slice transcript](/private/tmp/ascent-phase3-browser/001-phase3/natural-01145-conversation.json),[whole phase3 transcript](/private/tmp/ascent-phase3-browser/001-phase3/phase3-conversation-only.json),[natural ledger](/private/tmp/ascent-phase3-browser/001-phase3/natural-final-ledger.json).

All screenshot paths28–38 referenced above are under **/private/tmp/ascent-phase3-browser/001-phase3/** and were visually inspected. Earlier01/03/04/05/06 reside in its`screenshots/`subdirectory;07–27 reside at the run root. Old failures and source-specific screenshots remain intact. Main-agent-requested pauses are attributed to main, not the user.
