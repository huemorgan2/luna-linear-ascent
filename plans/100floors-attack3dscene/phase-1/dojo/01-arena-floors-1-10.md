# 100floors phase 1 — Arena on floors 1–10, no Labs toggle

## Preconditions
- Local stack: worldd serving `/play` (dojo-0046 recipe, `:8600`), Postgres
  up, phase-1 build (plugin pointer + vendor + `backgrounds300/` assets).
- Account A: a fresh climber on floor 1 who has NEVER opened Labs.
- Account B: a climber whose `unlocked_floor` ≥ 11 (seed via DB or admin).
- A browser with WebGL enabled.

## Scenario
1. As A, open `/play`, hunt on floor 1, and pick a fight. Screenshot the
   opener card (the close-up).
2. Take the first strike. From then on watch each round: player beat, then
   creature beat. Screenshot mid-round.
3. Open the action tiles; note the weapon tile (blade/bow/staff face) and
   the move tiles. Play at least three rounds, including one distance move.
4. Win (or lose) the fight; screenshot the end card.
5. Open Labs from the profile flask. Record what experiments are listed.
6. As A, climb (or seed) to floor 8 and fight once; screenshot one round.
7. As B (floor ≥ 11), fight once; screenshot one round.
8. In the DB, note A's `p["labs"]` value before and after all fights.

## Expected behavior
- On floors 1–10 the fight becomes the 3D arena after the first strike —
  a 320-wide canvas stage with an animated backdrop behind the fighters
  (NOT a flat black void), floating damage numbers, and the same numbers
  in the text log underneath, in the same order.
- The whole fight resolves with the same rules as before: HP totals in the
  HUD match the log arithmetic exactly.
- The Labs card lists only "Figure — 3D climber in the profile". No arena
  row, no way to switch the arena off.
- Floor ≥ 11 fights are the unchanged classic 2D card (no `.a3d` canvas).
- A fight completes a full round within ~3 s of the choice landing; the
  page never stalls waiting for assets (warming happens on the opener).

## Fail conditions
- A black or missing backdrop on any floor-1–10 fight (asset gap or a bad
  sheet) — file per-id, do not fix mid-run.
- Numbers on the stage that differ from the text log, beats out of order,
  or a round that plays the creature before the player without cause.
- An arena row still visible in Labs, or a player doc gaining/holding a
  `labs.arena` key from any action in this run.
- The 3D stage appearing on floor ≥ 11, or WebGL errors in the console.
- Raw JSON, a dead canvas over a working fight, or the 2D GIF flow on a
  floor-1–10 fight when WebGL is healthy.

## Verify
- DOM: fight cards on floors 1–10 carry `data-arena` and mount
  `canvas.a3d`; floor ≥ 11 cards carry no `data-arena`.
- DB: A's and B's player docs unchanged in `labs` (figure3d aside);
  fight outcomes (HP, gold, tally) consistent with the logs.
- Server log: no 5xx on `/play/api/*` during the fights; static requests
  for `backgrounds300/<id>.png` return 200 (no 404s) for every fought id.
- Timing: note seconds from option click to the round's last beat for one
  round per floor tested; flag anything over ~10 s.
