# 005 — web play: sign up on the site, climb in the browser

## Problem

linearascent.net (plan 003) has a front door — signup/login with
old-days accounts (`ascent_accounts`, session cookie `ascent_session`)
— but the door opens into nothing. The only way to actually play is
through Luna: marketplace plugin + a Luna install enrolled as a tenant.
A visitor who signs up on the website cannot climb.

**Goal: the game is 100% playable on the web.** Signup → play, same
world as every Luna climber, nothing to install.

Evidence of the gap (2026-08-02, worldd `main.py`):
- Play endpoints (`/v1/scene`, `/v1/act`) accept only HMAC tenant
  auth (`auth.py`) — web sessions can't reach them.
- `site.py` ends at `/me`; there is no `/play` route.

## Root cause (why this is small, not big)

Everything below the surface already exists; this plan is plumbing,
not construction:

1. **The interface exists.** `pane.py` (shipped in the plugin, vendored
   into worldd) is a complete self-contained HTML app — GAME / SCORE /
   COMMUNITY tabs, pixel-identical card grammar (`SCENE_CSS`,
   `render_scene_fragment`), faction desk included. Its only Luna
   couplings are three parameters: the API base path
   (`/api/p/plugin-linear-ascent`), Bearer-token auth via the
   `luna-auth` postMessage dance, and Luna-side proxy routes.
2. **The server logic exists.** `game.run_scene` / `run_act` compute
   turns for any `(tenant, player)`; every pane endpoint the Luna
   proxy forwards (`/v1/leaderboard`, `/v1/faction/*`, presence) is
   already implemented in worldd.
3. **The identity namespace is already unified.** Plan 004 made the
   door (`/signup`) and the gate (in-game name claim) share one
   registry (`names.claim`) — a web account already owns its name.

What's missing is only: a reserved **web tenant**, session-cookie
wrappers around the existing logic, and serving the pane at `/play`.

## Fix — five phases

| # | Phase | Ships |
|---|-------|-------|
| 1 | [Identity](phase-1/PLAN.md) — the `web` tenant; account ↔ player mapping; the registrar knows your name | DB migration + `game.py`/`names.py` |
| 2 | [Web play API](phase-2/PLAN.md) — session-authed `/play/api/*` wrapping the same functions `/v1/*` uses | `worldd/app/webplay.py` |
| 3 | [The pane at /play](phase-3/PLAN.md) — parametrize `pane.py` (API base, cookie auth, 401 → door); serve it | plugin repo + vendor |
| 4 | [The funnel](phase-4/PLAN.md) — signup lands you IN the game; homepage says so | `site.py` + homepage |
| 5 | [Dojo + ship](phase-5/PLAN.md) — walkthroughs, full ship ritual, live probe | dojo results + deploy |

Phases execute in order; each is verified before the next begins.

## Key decisions

- **Same server, no new service.** `/play` is worldd routes, like the
  site (003 decision: "we don't have millions of users").
- **One world.** Web players share the frontier, the Warden, the
  leaderboard and the factions with Luna players. The web is a tenant,
  not a shard: reserved tenant id `web`, player key =
  `lower(username)`. No second economy, no separate era.
- **One character per account on web.** `(tenant='web',
  player=<username>)` — logging in from any browser resumes the same
  climb. (Luna↔web character LINKING — one character played from both
  surfaces — is explicitly out of scope; `/v1/import`/`/v1/character`
  export exists if we ever want it. Noted, not planned.)
- **The pane is the game.** No new UI is written. The exact pane Luna
  users see becomes the page at `/play`, full-viewport. One code path
  to maintain, pixel parity guaranteed, and every future plugin ship
  upgrades the web automatically via `vendor_game.sh`.
- **Auth = the existing session cookie.** HttpOnly + SameSite=Lax +
  Secure already set by `site.py`. Lax blocks cross-site POST cookies
  (CSRF); phase 2 adds an Origin check as the belt to that suspender.
- **The registrar already knows you.** Signup claimed your username;
  the in-game name prompt is skipped for web players — your character
  IS your account name. No name-claim race between door and gate.

## Verification (plan-level; exact commands in each phase)

1. Fresh browser, `linearascent.net` → signup `webprobe-<rand>` →
   lands in the intro; race/class chosen; **no name prompt**; reaches
   ROOTHOLLOW. Under 60 seconds, zero installs.
2. `POST /play/api/act` without a cookie → 401. With a foreign Origin
   → 403.
3. Web player and a Luna-tenant probe see the same `world_day`,
   frontier and Warden; both appear on `/v1/leaderboard`.
4. Log out, log in from a second browser: same character, same scene.
5. `/health` shows the shipped `game` version; dojo run archived.

## Operational notes

- Signup rate limit (`_signup_ok`, 1h window) already throttles bot
  waves; watch `ascent_accounts` growth after launch.
- The pane hits `/play/api/scene` once per page load and one POST per
  click — same order of load as a Luna tenant; no new scaling work.
- Render auto-deploy is still broken: every phase that ships MUST end
  with `render deploys create srv-d9ha3csvikkc73ff5rg0 --confirm
  --wait` + `/health` game check.
- Changes land in BOTH places: pane/renderer edits go to the plugin
  repo and reach worldd via `vendor_game.sh`; worldd-only edits
  (site.py, webplay.py, migrations) live in the outer repo.
