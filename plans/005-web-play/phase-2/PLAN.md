# Phase 2 — the web play API

## Goal

Every endpoint the pane calls exists under `/play/api/*`,
authenticated by the site session cookie, executing the exact same
functions the HMAC `/v1/*` routes execute. Measurable: with a fresh
signup's cookie, `POST /play/api/scene` returns the intro scene;
without a cookie every route 401s; a cross-origin POST 403s.

## Steps

1. New `worldd/app/webplay.py`, router mounted in `main.py` under
   `/play/api`. Guard: `username = site.session_user(request)` else
   401 `{"detail": "sign in"}`. Identity: `tenant="web"`,
   `player=username.lower()`, `display_name=username` (phase 1).
2. Origin belt: on every POST, if an `Origin` header is present it
   must match the request host — else 403. (SameSite=Lax already
   keeps foreign-site cookies off these POSTs; this catches the rest.)
3. Routes — thin wrappers over what `/v1/*` already calls; the pane's
   full surface (from `pane.py` `call('…')` sites):
   - `POST /play/api/pane/scene` → `game.run_scene`
   - `POST /play/api/act` → `game.run_act`
   - `POST /play/api/pane/peek` → same source as `/v1` peek/presence
   - `GET  /play/api/pane/score` → leaderboard (`/v1/leaderboard` body)
   - `GET  /play/api/pane/community` → faction board/news
   - `GET  /play/api/pane/factions?q=` → `/v1/faction/list`
   - `POST /play/api/pane/faction/{detail,request,cancel_request,
     approve,reject,kick,promote,rename,enter}` → `factions.py`
   - `GET  /play/api/art/factions/{slug}.png` → the vendored faction
     banner PNGs (same files the plugin serves), `Cache-Control:
     public, max-age=86400`.
   Where a `/v1` handler in `main.py` inlines logic, extract it into a
   shared function both routes call — no copy-paste twins.
4. Rate limit: reuse the per-tenant limiter that made the probe 429s
   this week, keyed `web:<username>` so one web account can't starve
   the tenant bucket for everyone (verify the limiter's key shape in
   `auth.py`/middleware and key web calls per-account).
5. Tests: cookie-less 401 on every route; wrong-Origin 403; scene →
   act round-trip for a fresh account; leaderboard includes the web
   player after one act.

## Verification

```
# fresh signup, keep the cookie
curl -si -c j.txt -H 'Accept: application/json' \
  -d 'username=webprobe2&password=probeprobe' https://linearascent.net/signup
curl -s -b j.txt -X POST https://linearascent.net/play/api/pane/scene | jq .scene.eyebrow
# → "THE STORY SO FAR · I"
curl -si -X POST https://linearascent.net/play/api/pane/scene | head -1   # 401
curl -si -b j.txt -H 'Origin: https://evil.example' \
  -X POST https://linearascent.net/play/api/act -d '{}' | head -1          # 403
```

## Rollback

Remove the router mount in `main.py` (one line) and revert. No state
to unwind — the routes write through the same `ascent_players` path
as Luna play.
