# 039 the climb pays — production dojo walkthrough (2026-08-08, v0.52.0)

Production at https://linearascent.net — `/health` → `{"ok":true,"api":1,"game":"0.52.0","db":true}`
after deploy `dep-d9rg9tegekts739q8hhg` (srv-d9ha3csvikkc73ff5rg0). Commits: plugin
`aac7330` (0.52.0 bump; phases 1–3 in `27220c0` and earlier), outer `b4ef031` (vendor +
worldd). worldd suite 130 passed before deploy.

Two fresh accounts in isolated browser contexts (chrome-devtools MCP, `/me` → `{username:null}`
verified before each signup): **Deepfell** (human warrior, context dojo039a) for the floor-6
work, **Lowpath** (human archer, context dojo039b) for floor-1 pays and the no-deep floors.
Production grants every fresh account the world frontier (floor 6 open, `game.py:78`), so
both could reach floor 6 at level 1.

## Verdicts

| check | verdict | evidence |
|---|---|---|
| footer serves shipped version | PASS | site footer v0.52.0; /health game 0.52.0 |
| floor <4 town offers HUNT only, no deep | PASS | floor-3 Weirsend options: "Hunt the wilds ⚡1", stew, healer, keep, talk, return — no deep (shot 01) |
| floor-6 town offers both, priced | PASS | Lastlight: "1 Hunt the wilds ⚡1" + "2 Hunt deep — off the lit paths ⚡2 · harder, richer" (shot 02) |
| normal hunt costs 1⚡ | PASS | Lowpath meter 24→19 over 5 floor-1 hunts; Deepfell floor-6 normals 24→23→22 |
| deep hunt costs 2⚡ | PASS | 9 deep hunts, meter pairs 21→19, 19→17, 17→15, 15→13, 13→11, 11→9, 9→7, 7→5, 5→3 — every tick exactly 2 |
| deep opener names the deep | PASS | "You leave the lit paths. What finds you out here was never hunted thin." on the fight card (shot 03); seen on 8 of 9 draws (9th: capture raced the reel, not a content miss) |
| deep excludes prey/runts/feeble | PASS | 9 deep draws: Cave broodling ×4 (ATK 66–79), Sentinel spider ×2 (ATK 85–102), Vault boar ×2 (HP 339/242), Silk-wrapped husk ×1 — no feeble/frail tags, no prey species |
| deep is harder in ATK/speed, not a HP wall | PASS | deep ATKs 26–102 vs floor-6 normal base 22; deep HP 82–339 vs normal alpha Vault boar's 484 — the scary axis is ATK |
| floor-6 normal roster floor-shaped | PASS | normal draws: Vault boar (alpha, ATK 26/DEF 18/HP 484), Guano vole (ATK 9/DEF 18/HP 50) — floor-6 statline base (22/18/110) with specimen spread, no floor-1-grade pay animals |
| floor-1 pay unchanged baseline | PASS | Lowpath floor-1 kills: +3 gold (hedgerow rat), +12 gold +4 xp (grey wolf) |
| death flow | PASS | Lowpath: died to feral boar — gold halved 67→33, woke in Roothollow HP 1/52. Deepfell: 2 deep deaths (flee-fail vs ATK-66 broodlings) — "You wake at the foot of the Stone… Dying in the Ascent means waking in Roothollow." gold 50→25→12 across the two |
| deep refusal short of 2⚡ | PASS | at exactly 1⚡ the deep click bounced: "The deep wants ⚡ 2 in hand — you're short. One point returns every 45 minutes." — energy stayed 1, no fight started (shot 04) |
| console clean | PASS | list_console_messages after full run: no messages |

## Deviation from the scenario (documented)

The scenario's steps 3–4 call for an **at-level** floor-6 account (level ≥6, tier gear) to
measure kill pay against sim p10–p90. No privileged seeding path was available: `render ssh`
and Render-token reads were denied by policy, and `render psql` is blocked by the DB IP
allowlist. In-session leveling to L6 (677 xp) is impossible on fresh-account energy (24⚡,
45 min regen). The at-level claims — kill-pay bands, EV ladder, death rates — are covered
instead by sim039 against the real engine (N=600/class, 34,200 fights: normal EV 13.1→112.7
floors 1–10, deep/norm ratios 1.22–1.45, deep death 2.2–25.1%, both acceptance gates PASS)
plus the 21 unit tests in `test_039_climb_pays.py`. The live walkthrough verifies everything
observable at level 1: option gating, prices, energy ledger, roster composition, prime
statlines, openers, refusal, and death flow.

Incidental finds, not regressions: fresh accounts inherit the world frontier (floor 6 open at
level 1 — pre-existing `game.py:78` behaviour, makes the deep a level-1 death trap by player
choice); a cross-player assist line paid Deepfell +1 assist +2 gold on a floor-1 rat that
Lowpath had wounded — multiplayer working as designed.

## Screenshots

- `01-floor3-town-no-deep.png` — Weirsend, hunt ⚡1, no deep option
- `02-floor6-town-both-options.png` — Lastlight, both hunts with ⚡ prices
- `03-floor6-deep-card-opener.png` — deep fight card with the lit-paths opener (Cave broodling ATK 66)
- `04-deep-refusal-1-energy.png` — refusal card at 1⚡, energy intact
