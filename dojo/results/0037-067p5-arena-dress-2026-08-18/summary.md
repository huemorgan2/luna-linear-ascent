# DOJO 0037 — 067 phase 5: the arena card redressed

- Date: 2026-08-18
- Plugin: release/0.92.0 = db35540 (0.91.0) + be0ab82/bd8d191 (phase 5) — the exact tree vendored into worldd; worldd: arena3d.js ?v=2 (uncommitted at run time)
- Environment: worldd local `uvicorn app.main:app --port 8778`, ASCENT_GAME_PATH=release worktree, postgres localhost:5434/ascent_world, Chromium (playwright 1.50, swiftshader GL), viewport 420×900; `desktop/` holds 1440 and 420 stills of the regular vs arena card (archer, warrior)
- Account: dojo477907
- Result: **26/26 PASS**

| check | verdict | evidence |
|---|---|---|
| S1 signup | PASS | 200 dojo477907 |
| S1 seed floor 6 | PASS | seeded web:dojo477907 floor=6 class=warrior level=8 hp=400 held=['rusted_sword'] |
| S2 flask on the bar, reads "labs", off | PASS | {"labsTxt":"labs","on":false} |
| S2 floor 6 town shows hunt | PASS | hunt,hunt_deep,keep,talk,gate,town |
| S3 floor 6, labs off: regular encounter (no data-arena, no tiles) | PASS | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| S4 Labs card opens | PASS | LABSThe LabsThings being tried. Turn one on to test it.Experiments. Each one is off until you switch it on, and off again the moment you switch it off — nothing |
| S4 arena row off → ON | PASS | 1Arena — turn-based 3D fights — offswitch on · flo → 1Arena — turn-based 3D fights — ONswitch off · flo |
| S4 flask reads "labs on" | PASS | {"on":true,"txt":"labs on","dataLabs":"arena"} |
| V DB labs.arena = true | PASS | "{\"arena\": true}" |
| S5 opener: data-arena, close-up kept, no 3D yet | PASS | {"arena":true,"a3d":false,"img":false} |
| S5 opener tiles: icon + [n] LABEL + [i] | PASS | [{"opt":"close_in","txt":"1 CLOSE IN","dis":false,"ico":true,"info":true},{"opt":"stand","txt":"2 STAND","dis":false,"ico":true,"info":true},{"opt":"run","txt": |
| S6 3D stage 320x300 canvas in the arena banner | PASS | [320,300,394,369] |
| S6 tiles held while beats play, then released | PASS | {"busyEarly":true,"settled":155,"tiles":[false,false,false,false]} |
| S6 first round settles < 8 s | PASS | 6084 ms |
| S6 HP bars both sides | PASS | me:354/354 foe:53/53 |
| S6 log lines revealed (none pending) after beats | PASS | ["dojo477907 closes the gap.","Guano vole hits dojo477907 for 21 damage — 33 blocked by DEF."] |
| S7 floats seen: MISS / -N HP / BLOCKED | PASS | foe\|-21 HP  \|\|  blocked\|BLOCKED 33  \|\|  \|-11 HP  \|\|  foe\|-69 HP  \|\|  blocked\|BLOCKED 12  \|\|  \|-19 HP  \|\|  foe\|-61 HP  \|\|  \|-15 HP  \|\|  f |
| S7 canvas persisted across turns (not rebuilt) | PASS | rounds=5 |
| S7 fight reached an end | PASS | phase=victory rounds=5 |
| S8 log accumulates | PASS | 2 lines |
| S9 labs on, floor 5 hunt offered | PASS | {"on":true,"opts":["hunt","hunt_deep","keep","talk","gate","town"]} |
| S9 floor 5 with labs on: regular encounter | PASS | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| S10 seed resets flag: flask off | PASS | labs |
| S10 floor 6 with arena off: regular encounter | PASS | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| V no console errors / page errors | PASS |  |
| V no 4xx/5xx from /play/api | PASS |  |

## What changed on the card (roy's production feedback)

- Both stat sheets are the regular fight's ANSI slab: VGA face, black, `HP ▓▓▓░ n/m` + `ATK n   DEF n   SPEED n` (HP green/gold/red, ATK gold, SPEED aether); climber top-left, foe under it right-aligned. See `desktop/arena-settled-1440.png`, `desktop/arena-settled-420.png`.
- Tiles ride INSIDE the stage along its bottom edge, the item's own 30×48 art (bow = the bow, arrows = the arrows) scaled with the scene, pixelated; `[n] LABEL`, `[i]`. Nothing under the stage but the log.
- No profile / faction strip under a live fight.
- Floats: 3 s travel, full ink for the first 500 ms; a second float over the same head sits beside the first (BLOCKED next to −N HP: `desktop/arena-settled-420.png`).

## Regressions

none
