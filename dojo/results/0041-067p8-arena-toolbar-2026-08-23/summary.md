# Dojo run 0041 — 067 phase 8: toolbar under a 320×160 stage, regular menu around the fight

- **Date:** 2026-08-23
- **Scenario:** `luna/dojo/tests/labs-arena/walkthrough.mjs` (phase-8 expectations)
- **Environment:** local uvicorn :8778, postgres :5434, `ASCENT_GAME_PATH` → working-tree plugin (0.96.0), Chromium 1228 headless (SwiftShader), viewport 420×1100 + a 1440 desktop check
- **Code under test (pre-commit):** plugin-linear-ascent working tree on b264449 + phase-8 edits (render.py, version 0.96.0); walkthrough on 87d3f92 + phase-8 edits; worldd arena3d.js unchanged (?v=3)

## Verdict

**34/34 PASS** (final run). Two earlier runs failed checks and both failures were real findings, fixed and re-run — not retried away:

| Run | Score | Failure | Disposition |
|---|---|---|---|
| 1 | 33/34 | S6 settle 8392 ms (full pytest suite in parallel) | initially read as load flake |
| 2 | 33/34 | S6 settle 8995 ms, no load | flake theory dead → root-caused |
| 3 | 32/34 | S6 9804 ms; **S11 foe slab wrapped** (Vault boar, top:85) | both root-caused, fixed below |
| 4 (final) | **34/34** | — | S6 = 5200 ms with the honest clock |

## Findings

1. **S6 measured itself.** The serial `Date.now()-t1` budget included the harness's own fixed 3.8 s of float-watching plus a screenshot write. A timestamped probe put the real first-round settle at **4.3 s** (round card 725 ms, canvas 732 ms, beats done 4328 ms). Fix: the walkthrough now clocks settle with a busy-watcher running in parallel with the float watching. Final measured settle: **5200 ms < 8 s**.
2. **Foe HUD slab wrap (latent, phase-7 design).** The HP line is 31ch of `pre` (20 blocks + numbers). At 12px on a 394 px stage, two slabs + 4 px gap = 388 px > the 382 px row — a 3-digit-HP foe (Vault boar 286/286) wrapped the foe slab under the climber's. Content-random: 2-digit foes fit, which is why runs 1–2 passed. Fix: `@container (max-width: 440px)` tier — 10 px slabs, 10 px kind icons. Browser-verified at 420 with forced `1000/1000` in both bars: slabs stay on one top line (170+170 px in 382 px), screenshot `captures/`.

## Checks (final run)

All 34 PASS — see `results.json` for the full table with evidence. Phase-8 specifics:

- S5 opener: regular menu rows, **no tiles** — `{"tiles":0,"opts":["close_in","stand","run","shield_wall"]}`
- S11 toolbar UNDER the stage, 30 px pack boxes, labels + ATK beneath — gap 6 px, not in banner
- S11 stage is a 160 band — 394×198 rendered (w:h ≈ 2:1), nothing between toolbar and log
- S11 desktop 1440: slabs one row, toolbar under the stage
- S12 end card: regular menu rows + profile, no tiles, HUD still named
- S12 victory: XP/GOLD tally over the scene (`awin` opacity 1), said once (`tallies` = 1)
- S6 first round settles in 5200 ms; tiles held during beats, released after (settled 210 ms after watch)
- V: no console/page errors, no 4xx/5xx from /play/api, DB labs flag round-trips

## Tests alongside

- Targeted: `tests/test_067_arena.py tests/test_067_labs.py` — **19 passed**.
- Full plugin suite: **6 failed, 1296 passed** — the identical pre-existing six (test_008_pace×2, test_013_combat_feel, test_017_damage_types, test_017_death_relics, test_kill3d); no regressions.

## Captures

`captures/` holds the reviewed stills: `p8-*` 1440 round/victory, `p8m2-*` 420 round/victory (post tally-shrink), `p8v-*` 1440 victory (level-20 warrior), `p8m-*` 420 pre-shrink (the oversized tally that prompted the container-query fix). Walkthrough's own numbered screenshots (final run) sit beside this file.
