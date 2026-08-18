# 0040 — 067 phase 7: tiles as the pack's cells, HUD lines on black, 20-cell bars — 2026-08-18

- Environment: local worldd (uvicorn :8778, postgres 5434) on plugin main working tree (0.95.0), Playwright Chromium (swiftshader), viewport 420×900 with 1440 captures.
- Scenario: `luna/dojo/tests/labs-arena` (33 checks). Result: **33/33 PASS**. First run 31/33 — S5/S11 selectors still expected `<img>` art and a 0px HUD margin; updated to the phase-7 markup (`.picon`, ≤12px margin), re-run 33/33. Regressions: none.

## Checks
| verdict | check | detail |
|---|---|---|
| PASS | S1 signup | 200 dojo152455 |
| PASS | S1 seed floor 6 | seeded web:dojo152455 floor=6 class=warrior level=8 hp=400 held=['rusted_sword'] |
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
| PASS | S6 first round settles < 8 s | 4523 ms |
| PASS | S6 HP bars both sides | me:354/354 foe:38/38 |
| PASS | S6 log lines revealed (none pending) after beats | ["dojo152455 closes the gap.","Guano vole hits dojo152455 for 18 damage — 30 blocked by DEF."] |
| PASS | S11 HUD: two named slabs, both top-aligned a half line down, left/right | {"names":["DOJO152455","GUANO VOLE"],"slabs":[{"cls":"astat me","top":8,"left":8,"right":194},{"cls":"astat fo |
| PASS | S11 HUD: climber gear line (weapon + guard glyphs) | gear=3 |
| PASS | S11 HUD: foe kind icons match the foe (flying/armoured/MR/bulwark) | {"foe":{"flying":false,"armoured":true,"resist_pct":0,"bulwark":false},"kinds":["Armoured — the DEF is plate;  |
| PASS | S11 tiles inside the stage, visible, pack-style .picon art | [{"opt":"attack","img":true,"inside":true,"h":78,"op":"1"},{"opt":"stand","img":true,"inside":true,"h":78,"op" |
| PASS | S11 nothing renders under the stage but the log | below=0 |
| PASS | S11 desktop 1440: slabs still one row, tiles still inside | {"slabs":[{"cls":"astat me","top":8,"left":8,"right":494},{"cls":"astat foe","top":8,"left":510,"right":8}],"i |
| PASS | S7 floats seen: MISS / -N HP / BLOCKED | foe/-18 HP  //  blocked/BLOCKED 30  //  /-21 HP  //  foe/-42 HP  //  blocked/BLOCKED 12  //  /-14 HP  //  foe/ |
| PASS | S7 canvas persisted across turns (not rebuilt) | rounds=4 |
| PASS | S7 fight reached an end | phase=victory rounds=4 |
| PASS | S8 log accumulates | 2 lines |
| PASS | S12 end card: tiles inside the stage, HUD named, nothing under | {"phase":"victory","tiles":[["hunt",true],["hunt_deep",true],["stew",true],["heal",true],["keep",true],["talk" |
| PASS | S9 labs on, floor 5 hunt offered | {"on":true,"opts":["hunt","hunt_deep","keep","talk","gate","town"]} |
| PASS | S9 floor 5 with labs on: regular encounter | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| PASS | S10 seed resets flag: flask off | labs |
| PASS | S10 floor 6 with arena off: regular encounter | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| PASS | V no console errors / page errors |  |
| PASS | V no 4xx/5xx from /play/api |  |

## Captures
07/08 stage-settled (420/1440) — HUD lines on black only, 20-cell bars, one line of pack-style tiles half a line up.
10/11 fight-end (420/1440) — the end card's menu as the same tiles.
