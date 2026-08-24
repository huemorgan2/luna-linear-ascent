# 0050 — 078 zero-latency clicks (dojo run)

- **Date:** 2026-08-24
- **Scenario:** `plugin-linear-ascent/tests/078-zero-latency-clicks/01-snappy-clicks.md`
- **Environment:** local worldd :8600 (`app.main:app --reload`), game 0.102.0,
  Postgres 16 on :5434, world seeded to **10,517 playing players**
  (`tools/seed_scale.py 10000`; cleaned after the run)
- **Player:** existing browser account `Perf3D1787593265`, mid-game, floor 2–4

## Verdict: PASS

| Check | Budget | Measured | Result |
|---|---|---|---|
| Non-lift click → painted card | < 300 ms | 16 acts: 19–133 ms, p50 ≈ 36 ms | PASS |
| Act response on the wire | < 30 KB | 5.0–17.4 KB (gzip) | PASS |
| Inline base64 raster art in fragments | zero | 0 of 16 acts carried `data:image/png|gif` | PASS |
| Art from `/static/laart` cached on repeat | no re-download | 2 repeat shop loops: 3/3 art hits from browser cache, 0 downloads | PASS |
| `Cache-Control` on art | immutable, 1 y | `public, max-age=31536000, immutable` | PASS |
| Console / network failures | zero | 0 failed requests (`responseStatus >= 400`) | PASS |
| Live-feeling world at scale | tiles, counts, presence | town grid full (21 tiles + "MORE 452 PLAYERS"), floor 2 "16 camps within the hour", gate tiles | PASS |
| Fight flow | meters move, options replace | hunt → close_in (hp 96→80 after the exchange) → run → floor card | PASS |

## Server-side proof at 10,517 players

`tools/bench_act.py` (100 mixed acts, in-process ASGI, full path):

| Scale | p50 | p95 | max | payload p50 |
|---|---|---|---|---|
| 891 players (pre-seed) | 7.8 ms | 9.4 ms | 9.9 ms | 6.9 KB |
| 10,517 players | 6.3 ms | 8.2 ms | 9.3 ms | 6.9 KB |

Latency is **flat with 11× the players** — the projections + snapshot
architecture holds. Snapshot rebuild at 10k costs 270–500 ms but runs in a
background task at most once per 10 s (stale-while-revalidate); warm
`inject_world` is 2–4 ms / 13 queries.

`EXPLAIN (ANALYZE)` at 10.5k — no Seq Scan on any per-click query:

- roster: `ix_players_playing_roster`, 0.24 ms
- census: index-only `ix_players_playing_floor`, 2.2 ms
- presence: bitmap `ix_players_playing_updated`, 2.0 ms
- name lookup: `ix_players_playing_name`, 0.02 ms
- leaderboard (Score tab, on demand, not per click): seq scan 6.4 ms —
  acceptable; noted for a future ordering index if the Score tab ever heats up

## Screenshots

| File | What it shows |
|---|---|
| `01-roothollow-square.png` | Square card, 1-bit town banner from static URL, COLLECT/PLAN tiles |
| `02-forge.png` | Forge card, weapon art (static URLs), no broken masks |
| `03-floor2-lampfall.png` | Floor 2 arrival card, banner + tinted keep art, presence line |
| `04-fight-shellback.png` | Fight card, full stat readout, meters |
| `05-stone-of-names-profile.png` | Seeded player profile, portrait + meters + social actions |

## Observations (not regressions)

1. **Decoded act payloads can reach ~684 KB** (forge/town with a full room
   grid) though only 17 KB rides the wire: 268 procedurally generated
   `data:image/svg+xml` URLs (1-bit tile/portrait masks) repeat per tile and
   gzip 40:1. Paint stays fast. Candidate future win: dedupe repeated SVG
   masks into shared defs or class-based CSS.
2. Seeded docs show odd HP scales on the Stone (`320/16702`) — an artifact of
   the synthetic seed docs, not the game.
3. The "second browser, second account" cross-visibility check is covered by
   the suite (`test_web_play` multi-account contracts) and by this run seeing
   other accounts' tiles (gate: Aldo, Fleet, Seen, Showup) — no separate
   browser was driven.

## Multi-turn invariants

- Old-scene options: every act sent `scene_id`; no stale-option acceptance seen.
- Meters moved only on the fight exchange; menu hops left them untouched.
- No ghost cards; each act's card replaced the previous cleanly.
