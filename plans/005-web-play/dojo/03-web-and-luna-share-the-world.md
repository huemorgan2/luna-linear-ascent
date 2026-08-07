# 03 — the web and Luna climb the same tower

## Preconditions

- Production live. One fresh web account; one throwaway Luna-style
  tenant enrolled via `/v1/enroll` + HMAC (the probe pattern from
  [[scene-vs-render-split]]).

## Scenario

1. Web: sign up, reach ROOTHOLLOW. Record the homepage/status world
   line (day, climbers, frontier, Warden %) and the in-game gate's
   floor list.
2. Probe: enroll a tenant, walk the same character flow via signed
   `/v1/scene`/`/v1/act`. Record the world facts its scenes state.
3. Web: open SCORE; probe: `POST /v1/leaderboard`.
4. Web: open COMMUNITY → factions list; probe: `/v1/faction/list`.

## Expected behavior

- Both surfaces report the SAME world: same world day, same frontier
  floor, same Warden and its HP band, within one turn of drift.
- The leaderboard is one list — the web player and the probe's player
  both on it, same ordering from both sides.
- The faction list is identical from both surfaces.

## Fail conditions

- Different frontier/Warden numbers on web vs probe (web accidentally
  sharded into its own world).
- Web players missing from the HMAC leaderboard or vice versa.
- Faction created on one surface invisible on the other.

## Verify

- DB: exactly one `ascent_world` row backing both reads (no
  tenant-scoped world rows for `web`).
- worldd logs: probe and web session hit the same handlers
  (`run_scene`/`run_act`) — no web-only code path for world state.
