# 0039 — 067 phase 6: arena HUD named + aligned, kind icons, tiles on every live card — 2026-08-18

- Environment: local worldd (uvicorn :8778, postgres 5434) on plugin main working tree (0.94.0, 067 phase 6), Playwright Chromium (swiftshader), viewport 420×900 with 1440 captures.
- Plugin: main @ acb43b3 + phase-6 working tree (committed right after this run). Root: dc894f9. luna dojo: walkthrough.mjs extended (S11/S12).
- Scenario: `luna/dojo/tests/labs-arena` (33 checks: 26 phase-5 + S11×6 + S12).
- Result: **33/33 PASS**. Two earlier runs: 32/33 (S6 settle 12.1 s under load — flake, passed 7.2 s and 5.2 s on re-runs), 33/33.
- Regressions: none.

## Checks
| verdict | check | detail |
|---|---|---|
| PASS | S1 signup | 200 dojo992313 |
| PASS | S1 seed floor 6 | seeded web:dojo992313 floor=6 class=warrior level=8 hp=400 held=['rusted_sword'] |
| PASS | S2 flask on the bar, reads "labs", off | {"labsTxt":"labs","on":false} |
| PASS | S2 floor 6 town shows hunt | hunt,hunt_deep,keep,talk,gate,town |
| PASS | S3 floor 6, labs off: regular encounter (no data-arena, no tiles) | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| PASS | S4 Labs card opens | LABSThe LabsThings being tried. Turn one on to test it.Experiments. Each one is off until you switch it on, an |
| PASS | S4 arena row off → ON | 1Arena — turn-based 3D fights — offswitch on · flo → 1Arena — turn-based 3D fights — ONswitch off · flo |
| PASS | S4 flask reads "labs on" | {"on":true,"txt":"labs on","dataLabs":"arena"} |
| PASS | V DB labs.arena = true | "{\"arena\": true}" |
| PASS | S5 opener: data-arena, close-up kept, no 3D yet | {"arena":true,"a3d":false,"img":false} |
| PASS | S5 opener tiles: icon + [n] LABEL + [i] | [{"opt":"close_in","txt":"1 CLOSE IN","dis":false,"ico":true,"info":true},{"opt":"stand","txt":"2 STAND","dis" |
| PASS | S6 3D stage 320x300 canvas in the arena banner | [320,300,394,369] |
| PASS | S6 tiles held while beats play, then released | {"busyEarly":true,"settled":152,"tiles":[false,false,false,false]} |
| PASS | S6 first round settles < 8 s | 5411 ms |
| PASS | S6 HP bars both sides | me:354/354 foe:21/21 |
| PASS | S6 log lines revealed (none pending) after beats | ["dojo992313 closes the gap.","Guano vole hits dojo992313 for 20 damage — 33 blocked by DEF."] |
| PASS | S11 HUD: two named slabs, both top-aligned a half line down, left/right | {"names":["DOJO992313","GUANO VOLE"],"slabs":[{"cls":"astat me","top":8,"left":0,"right":218},{"cls":"astat fo |
| PASS | S11 HUD: climber gear line (weapon + guard glyphs) | gear=3 |
| PASS | S11 HUD: foe kind icons match the foe (flying/armoured/MR/bulwark) | {"foe":{"flying":false,"armoured":true,"resist_pct":0,"bulwark":false},"kinds":["Armoured — the DEF is plate;  |
| PASS | S11 tiles inside the stage, visible, art as <img> | [{"opt":"attack","img":true,"inside":true,"h":88,"op":"1"},{"opt":"stand","img":true,"inside":true,"h":88,"op" |
| PASS | S11 nothing renders under the stage but the log | below=0 |
| PASS | S11 desktop 1440: slabs still one row, tiles still inside | {"slabs":[{"cls":"astat me","top":8,"left":0,"right":582},{"cls":"astat foe","top":8,"left":570,"right":0}],"i |
| PASS | S7 floats seen: MISS / -N HP / BLOCKED | foe/-20 HP  //  blocked/BLOCKED 33  //  /-11 HP  //  foe/-39 HP  //  blocked/BLOCKED 12  //  /-16 HP |
| PASS | S7 canvas persisted across turns (not rebuilt) | rounds=3 |
| PASS | S7 fight reached an end | phase=victory rounds=3 |
| PASS | S8 log accumulates | 2 lines |
| PASS | S12 end card: tiles inside the stage, HUD named, nothing under | {"phase":"victory","tiles":[["hunt",true],["hunt_deep",true],["stew",true],["heal",true],["keep",true],["talk" |
| PASS | S9 labs on, floor 5 hunt offered | {"on":true,"opts":["hunt","hunt_deep","keep","talk","gate","town"]} |
| PASS | S9 floor 5 with labs on: regular encounter | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| PASS | S10 seed resets flag: flask off | labs |
| PASS | S10 floor 6 with arena off: regular encounter | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| PASS | V no console errors / page errors |  |
| PASS | V no 4xx/5xx from /play/api |  |

## Captures
07-stage-settled.png / 08-stage-settled-1440.png — round card: named slabs one row at the top, gear line, foe kind icon, tiles inside the stage.
10-fight-end.png / 11-fight-end-1440.png — end card: HUD kept, the gate-town menu as tiles inside the stage, nothing under it but the log.
