# 089 wiki walkthrough — 12 September 2026

Environment: isolated checkout based on origin/main12f5fc5, plan commits512486a/f5d18ae; local worldd at127.0.0.1:8609, game0.112.0, wiki089.1. Browser: Codex in-app browser controlled through CUA's Playwright API. Desktop1440×960 and phone390×844. Disposable PostgreSQL16 at127.0.0.1:55442; no production player was used.

First user action for this public reference is opening the website's `/wiki`. This does not change any plugin tool, game action or session endpoint. The relevant browser walkthrough is the website; no Luna combat-playthrough claim is made.

| Scenario | Verdict | Evidence |
|---|---|---|
| Full roster and changing floor art | PASS | Floors1/3/25/50/80/100 change authored names, environments and images. Floor3 has Marsh adder; Floor100 has the assembled court/King's shadow/living regalia/mirror witness. All425 IDs and image hashes validated against current content. |
| Game typography and controls | PASS | Computed font VGA on all inspected text, size16px. Only dropdowns:16 weapon families and101 floor options. Game-generated pixel masks; rarity frames gray/teal/violet/gold. |
| All grade/level endpoints | PASS | Four grades at+0/+20; neutral reference validated across100 floors. Source selection synchronizes both grade controls and opens Forge. |
| Tactical preview | PASS | Runestring vs AirPower gives88 ordinary-arrow damage versus32 arcane damage. Ramguard cannot reach Air (0). |
| Shield and distance | PASS | Incoming100,armor200,shield300,wall enabled: armor50,shield25,HP25,wear25. Shove creates Far gap; next bow shot leaves Near. |
| Warden overlap illustration | PASS | One player makes no progress against healing;50 players win in22.5 seconds. Explicitly a toy, not Floor100's stats. |
| Full loot/settings roster | PASS |425 rows initially; Floor80 has4. Deep excludes2 feeble creatures. Remount common normal/deep Legendary weapon0.05618571%/0.22474286%; deep alpha0.50567143%. Search, parameter view and per-family dossier work. |
| All weapon sources | PASS |64 rows. Legendary Ramguard shop+6,4798/4798,Floor84; drop+0,449/4486 (10%),discovery50/equip76.206 eligible creature sources for Legendary,425 for other grades. |
| Phone | PASS |390px document width at390px viewport, no horizontal page overflow; dossier352px wide and scrollable. Frame controls, bestiary and modal remain readable at16px. |
| Public production route and homepage link | PASS | Clicked homepage Wiki link at linearascent.net. Revision089.1 loaded425 creature rows/64 weapon rows. Floor80 deep remount odds0.22474286% and Legendary Ramguard source settings match local. Console0 errors. |

## Automated verification

- Worldd suite:223 passed in83.36s.
- Targeted route/data/progression tests:3 passed; all100 floors and425 creatures covered.
- Node model checks:5 passed, covering3400 creature/mode/specimen outcomes,2304 loadout combinations and5400 shield allocations.
- Reproducible data check: current; no missing creature/weapon art. All441 creature/weapon image URLs returned HTTP200 locally. Browser console recorded0 errors. No game state writes.

## Regressions and corrections

The initial suite had222 passing/1 failure because this isolated checkout lacked the plugin submodule's source map. Initialized its exact pinned commit92c86b6 and reran the full suite:223 passing. Two initial new assertions incorrectly treated base acquisition as an upgrade charge and expected attack to rise on legacy hold floors; corrected the assertions, preserving the verified economy. Review found and fixed grade control synchronization after a source-table click, and moved loot probabilities ahead of the wide parameter table. All are resolved.

Screenshot evidence was captured and inspected in the task's browser tool output; see `screenshots/README.md`. Browser artifacts are inline, not invented local PNGs.

## Production release

Implementation693d4f7, Render deployment dep-daik2p5g1s2s73flpv10, live2026-09-12T12:15:34Z. Game remains0.112.0. `/wiki` HTTP200; `/health` ok:true,db:true; generated data bytes match the source bundle. The custom-domain page was verified through the real browser (a plain urllib request to that hostname received403; the Render origin returned200). Public UI behaved correctly. No unresolved regressions.

## Crafting follow-up — revision089.2

A post-release design review found that deferring higher-level shop stock left a gap at grade entry. Exposed the existing +0 gold/material recipe as a full-condition Forge crafting source for all64 entries at floors1/26/51/76. Browser PASS: Legendary Ramguard crafts at76,+0,4486/4486 END,19,193,000,429 gold,20 Mythic Threads and80 Shard Matter. Shop+6 and drop+0/10% remain distinct. Full suite223 passed in85.53s; Node5/5, targeted Python3/3, generator-current check pass. Follow-up PASS in production:80d18ee, deployment dep-daik90p594qs7393qsl0, live2026-09-12T12:29:02Z. Browser confirms089.2,425 creatures,64 weapons and the full three-source dossier. HTTP200,health ok:true/db:true and identical baked data verified. Game version stays0.112.0. No live gameplay settings changed. Disposable QA database container stopped after verification.
