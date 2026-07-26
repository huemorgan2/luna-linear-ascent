# Dojo 0007 — Forced multiplayer, shared Warden, Morning Crier (2026-07-26)

Live browser playthrough of plan 007 against a local worldd (port 8600,
test Postgres on 5434) with a QA Luna on 8765. Player A ("Dojo",
tenant qa007) played through the real chat UI with Playwright; Player B
("Brynn", tenant-a) played through a scripted HMAC client
(`/tmp/ascent_b_driver.py`).

## Scenario 1 — mandatory world: PASS
- Fresh tenant, no character: the intro card (LINEAR ASCENT title banner
  + storyline) → race → class → name, all served by worldd.
  `01-intro-title-storyline.png`
- Env override (`LUNA_ASCENT_WORLDD_URL` + secret + tenant) connects at
  boot; auto-enroll against an env URL without a secret now also works
  (fix committed this run).
- Offline "lift is down" scene not re-tested live (would have killed the
  worldd other sessions share); covered by unit test.

## Scenario 2 — one shared Warden per floor: PASS
- Frontier keep showed the ONE world Brackjaw: HP 280/280 (4× solo),
  "One Warden for the whole world" copy, Strike 3⚡ / Withdraw.
  `02-shared-warden-pool.png`
- Dojo's strike: −6 HP pool, 13 counter-damage, 3⚡ spent; persisted in
  `ascent_world.warden:1` with Dojo credited.
- Brynn (other tenant) saw the same reduced pool and "blades against
  it: Dojo".
- Kill (HP lowered by test lever, Brynn finished): frontier 1→2 for
  everyone, happening + Stone entry name both strikers, Dojo's stale
  strike click resolved to "has already fallen", his reward share
  (+96 xp, +◈128) landed, and his next session got the queued fall
  report card.
- Floor 1 keep (now below frontier) reverted to the solo echo fight;
  floor 2 keep spawned the fresh shared Sedgeback (372/372).

## Scenario 3 — Morning Crier: PASS
- With `news_day` rewound, the next session-start scene was the Crier:
  day count, frontier floor, census (166 climbers — top/bottom/your
  floor), warden status gossip, and level-gated advancement advice.
  `03-morning-crier.png`
- Not delivered twice the same day; card clicks never interrupt it
  (delivery is session-start only, by design).

## Bugs found & fixed this run
1. `runtime.ensure_world` always enrolled against the production URL —
   QA override honored now (plugin commit d68be38).
2. After your own first strike the card still said "no blade has touched
   it yet" — striker now appears optimistically (same commit).

## Notes / leftovers
- "1 floor stand open" grammar nit at the tower gate (pre-existing).
- Crier census "0 on floor 2 with you" excludes the player themself;
  reads slightly odd when you're alone on the floor.
- Historical duplicate tenants in the QA world DB came from the stale
  Jul-24 worldd that was still holding port 8600 at session start; the
  new server + vault idempotency behaved correctly once it was killed.
- The running worldd was NOT restarted after the vendor sync (a parallel
  008 session is actively using it); the striker-display fix is unit-
  tested and will be live on next restart.
