# DOJO 0036 — 067 labs-arena

- Date: 2026-08-18
- Root commit: 0b9ef6d (+ uncommitted phase-3 hold-tiles fix, phase-4 sheet regen at run time); plugin: 3080333
- Environment: worldd local `uvicorn app.main:app --port 8778`, live plugin via ASCENT_GAME_PATH, postgres localhost:5434/ascent_world, Chromium (playwright 1.50, swiftshader GL), viewport 420×900
- Account: dojo249670
- Result: **26/26 PASS**

| check | verdict | evidence |
|---|---|---|
| S1 signup | PASS | 200 dojo249670 |
| S1 seed floor 6 | PASS | seeded web:dojo249670 floor=6 class=warrior level=8 hp=400 held=['rusted_sword'] |
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
| S6 tiles held while beats play, then released | PASS | {"busyEarly":true,"settled":158,"tiles":[false,false,false,false]} |
| S6 first round settles < 8 s | PASS | 4998 ms |
| S6 HP bars both sides | PASS | me:354/354 foe:286/286 |
| S6 log lines revealed (none pending) after beats | PASS | ["dojo249670 closes the gap.","Vault boar hits dojo249670 for 31 damage — 44 blocked by DEF."] |
| S7 floats seen: MISS / -N HP / BLOCKED | PASS | foe/-31 HP  //  blocked/BLOCKED 44  //  /-13 HP  //  foe/-84 HP  //  blocked/BLOCKED 12  //  /-18 HP  //  foe/-47 HP  //  /-10 HP  //  foe/-66 HP  //  foe/-78 H |
| S7 canvas persisted across turns (not rebuilt) | PASS | rounds=7 |
| S7 fight reached an end | PASS | phase=death rounds=7 |
| S8 log accumulates | PASS | 3 lines |
| S9 labs on, floor 5 hunt offered | PASS | {"on":true,"opts":["hunt","hunt_deep","keep","talk","gate","town"]} |
| S9 floor 5 with labs on: regular encounter | PASS | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| S10 seed resets flag: flask off | PASS | labs |
| S10 floor 6 with arena off: regular encounter | PASS | {"arena":false,"tiles":0,"opts":["close_in","stand","run","shield_wall"]} |
| V no console errors / page errors | PASS |  |
| V no 4xx/5xx from /play/api | PASS |  |

Floats observed during the fight: foe|-31 HP; blocked|BLOCKED 44; |-13 HP; foe|-84 HP; blocked|BLOCKED 12; |-18 HP; foe|-47 HP; |-10 HP; foe|-66 HP; foe|-78 HP; |-9 HP; foe|-63 HP; foe|-37 HP

## Screenshots
01 bar off · 02 floor-6 regular (labs off) · 03/04 Labs card off/on · 05 opener (close-up + tiles) · 06 first strike (3D stage) · 07 settled · 08 mid-fight · 09 fight end · 10 floor 5 regular with labs on · 11 floor 6 regular after switch-off

## Regressions / findings
- Run 1 (before fix): tiles were not held from the moment the card landed — the hold started only after build/attach; a click in that gap could double-act. Fixed in arena3d.js (`holdTiles` at mount, `releaseTiles` in `finally`, which also guarantees the log shows and tiles come back if GL/rig fails).
- Run 1: 6 of 14 arena backgrounds came back letterboxed (Gemini drew a cinematic strip inside the square) — the stage showed black bands top and bottom. Prompt hardened (no letterbox / bars / border), 6 stills regenerated, all 14 sheets rebuilt.
- Console: only /favicon.ico 404s (pre-existing, filtered).
- Not exercised in this run: MISS jitter (blade rank 6, no miss rolled in 7 rounds), open-distance walk-back (never offered — the boar kept close), victory banish (the climber died in round 7 both runs — level 8 vs floor 6 is a losing seed; the death path (`beatMeDie`) ran instead).

## Supplementary runs (`fight-more.mjs`, same server)
| run | class / level | rounds | end | floats | console errors |
|---|---|---|---|---|---|
| x-archer | archer L22 | 2 | victory (banish + freed native) | MISS (jitter, screenshot x-archer-miss.png), −359 HP | 0 |
| x-warrior13 | warrior L13 | 2 | victory | foe −22 HP, BLOCKED 51 ×2, −67 HP | 0 |
| x-sorcerer13 | sorcerer L13 | 1 | victory (grave-rat freed) | −38 HP (magic, fly sign halves it — log line matches) | 0 |

Covered by the four runs together: opener → first strike, blade / bow / staff strikes, MISS, −N HP both ways, BLOCKED, DODGE, death, victory + banish + freed native, canvas persistence, Labs on/off, floors 5 vs 6.
Still not exercised in-browser: open-distance walk-back (never offered in these fights — the engine only offers it under range/gear conditions); covered by the phase-3 unit path only.
