# Phase4 browser002 — 2026-09-13

Actual Playwright Chromium browser, real preserved Luna conversation, and three declared /play fixtures. Run approximately10:46–10:56 UTC. No engine/source edits, service restarts, existing-player grants/resets, pytest substitutes, or production changes. Evidence is local and excludes authentication values.

**Discovery is partial: Ordinary100 is recognized, but the exact query still fails to show five other payloads until an explicit refresh. Action-limit discipline FAILS (existing P3-008 recurrence, phase7-owned). The listed frozen-engine combat checks PASS. This is not whole-phase completion.**

## Environment and provenance

- Repository `/Users/roy/Documents/my-projects-docs/ascent-change-everything`, branch `change_everything`. Root at preflight `eadbc551ab1345ea33fbd04c8c5607d470ccc39a`; root at freeze `b9cad73cc4762d007fa8aec3e311a04d69f9b179` (main's concurrent work). Plugin remained `56e1d86faca1298401de6e50ac25d6823502f75d`,0.115.1. Final worldd health10:55:52 UTC reported0.115.1, DB ready. This role made no repository change.
- worldd8860, Luna8898; preserved PostgreSQL17 databases on5433. Port5432 and main's separate8862 late-site run were not accessed.
- Preserved Luna conversation `60d7a0a6-1771-4b5e-a105-3d9364325c7f`, natural identity `ascent-change-phase3:owner` / Phase3Luna.
- Three NEW web rows only: `phase4fire002`, `phase4arcane002`, `phase4poison002`. Creation fails on collision. Each starts with declared gold200, current-time energy25, HP80, level1, Common crafted deck plus retained starter collection, explicitly declared training/ammo/materials. See `fixture-declarations-before-insert.json` and `create_fixtures.py`.
- Setup used real `state.new_player`, collection migration/mint, quiver enrollment, `bestiary.rolled_member`, `groups.open_group`, and `core.current_scene`. Monster stats/specimens/rewards were actual rolled roster records. Arrival gaps were explicitly seeded legal distances. Arcane's RNG counter1007 was selected to expose an accepted rank0 miss. No simulated action determined the verdict; every combat action was a real browser click.
- Current-time initialization was used; no Jan1 prepared-save helper. Fixture ledgers contain the observed enemy-start/kill records, with no later login gold correction or reset.

## Verdicts

| Scenario / gate | Result | Evidence |
|---|---|---|
| Exact same-chat arrow query | **PARTIAL; exact gate FAIL P4-002** | Recognizes Ordinary100, improving on blanket denial; two stale `read` calls, zero current ascent calls, omits five types. Screenshot02; Luna exports. |
| Explicit current-data recovery | PASS | Character+scene refreshed; all six stocks/effects/prices answered. Screenshot03. |
| Bounded natural route | **FAIL P4-004 / P3-008** | Existing phase7-owned cap issue recurs: two turns each made5 choices under a4-action cap. Screenshot06; exact choices/timestamps in logical-failures.md. |
| Natural earned gold and actual Forge purchase | PASS | One legacy normalfloor1 group only; +35gold/+4XP/2energy, HP unchanged. One20 Common Arcane bundle cost10gold, ledger139. |
| Natural free-preview Arcane select/leave | NOT RUN | Main froze further natural choices after purchase/travel; stopped at floor1 camp s141. |
| Fire Power impact and later Magic burn | PASS | Tortoise19→14 on5 resisted Power; no first-action burn tick. Following Guard and Ramguard actions each tick2Magic, then burn expires. Screenshots08–10; fire state snapshots. |
| Push→bow normal next action | PASS | Ramguard atContact→Far; pursuit skipped; next Hawkeye shot legal. No extra energy for the same enemy. Screenshots10–11. |
| Arcane Magic resistance popup | PASS | Accepted Arcane hit4Magic against Magic×0.45; distinct pixel Magic shield above lamp-eater. Screenshot14. Power popup in11 stays on defeated tortoise tile, not next defender. |
| Normal/mobile reduced-motion feedback and reread | PASS | New reduced-motion hit shows static Magic-resisted5 badge on390px. Same-state reload does not change resources or replay the old popup. Screenshots18,20; event IDs and DB snapshots. |
| Free selection, invalid, miss, empty stock | PASS | Free selection leaves combat turn, cooldowns, energy, HP, wear and stock unchanged. Stale shot refused; unreachable blades refused atNear and againstAir atContact. Miss consumes1arrow/1condition; empty Arcane refuses despite Ordinary8. Manual Ordinary selection restores bow. Screenshots12–15,25–26,28. |
| Poison→switch/source/final tick | PASS | Viper direct12 applies poison without tick. Bow7+poison1, bowmiss+poison1, bow7+finalpoison1. Boar dies; activeweapon remainsbow but last damage source and kill_path are originalblade; effect expires. Screenshots16–17,19,21; poison snapshots. |
| Varying later arrivals | PASS | Actual second enemies retain Near (Rust hound), Contact (Air Lamp newt), Cover (Grey wolf); all unstarted atstop. Screenshots11,21,24. |
| Three cells, six choices, materials and Arrows drawers | PASS | Three explicit instances; six free arrow controls; actual drawer shows Wood6/RawMetal2, all eight material types/grade frames, six payload descriptions/stocks, current bow payload. Screenshots04,07,22–23,28. |
| Committed collection inspection | PASS, limited | Inspecting unselected owned blade exposes no replacement action and says weapons remain committed. Three deck IDs unchanged, pending group/clocks unchanged. Full S04 pack/profile/trade/multiple-tab replacement matrix is not claimed. |

27 screenshots were saved and visually read. Early popup screenshots intentionally capture normal animation before typewriter narration finishes; paired text and DB evidence preserve the complete state. Real web actions completed in well under3seconds; exact request/response timestamps are in `browser-actions.json`. Luna turn timings are separate and include model generation and its stale-result retrieval.

## Preserved stop state

| Player | Scene / pending state | Resources |
|---|---|---|
| Phase3Luna | floor1 camp, s141; no active group; Arcane not yet selected |33gold,17XP,58HP,3energy atstop; Hawkeye+1 condition1299/1332; Ordinary100, Arcane20; materials0; owned axe/pick unchanged|
| phase4fire002 | group:1, enemy2 Rust hound29HP, Near, unstarted; turn4, Ramguard cooldown2; Arcane selected free |200gold,3XP,77HP,24energy;13gold pending|
| phase4arcane002 | group:1, enemy2 Lamp newt36HP, AirContact, unstarted; turn5; Ordinary selected free after Arcane emptied |200gold,11XP,64HP,24energy;27gold pending|
| phase4poison002 | group:1, enemy2 Grey wolf18HP, Cover, unstarted; turn4; first enemy's poison expired and kill credited toblade |200gold,2XP,74HP,24energy;19gold pending|

All pending hauls/groups remain valid. No cleanup, escape, second enemy start, or earned-state restore was performed atstop. `protected-existing-row-check.json` proves all8 preexisting non-natural rows retain identical document hashes, including BaselineAsh's identity and all phase3 webfixtures. Browser sessions were closed after evidence capture.

## Remaining / handoff

1. Fix and rerun exact first-query current-data discovery. Phase7 already owns P3-008 cap enforcement; main calls for a deterministic tool-call guard and both cap cases should be rerun there. Do not erase this evidence or repeat natural combat without new authorization.
2. Natural20Arcane are bought but the next free-preview selection/leave step remains pending because main explicitly froze natural choices.
3. Main owns site/niche measurements, later-site play, Gate resource-site naming, and wiki gates. No claim about their result is made here.
4. This run covers the requested phase4 combat/drawer cases, not the entire S04/S05/S07/S12/S15 suite: no full shield/death/energy rerun, all mastery/immunity/control exhaustion permutations, pack/profile/trade lock matrix, or later-grade material progression claim.

Primary audit files: `logical-failures.md`, `luna-turn-actions.json`, `luna-allowlisted-messages.json`, `browser-actions.json`, `fixture-declarations-before-insert.json`, allowlisted before/after JSON snapshots, and screenshot PNG/TXT pairs. No secret/auth file belongs in a repository or publishable evidence bundle.
