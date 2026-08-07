# Phase 3 — the pane, served at /play

## Goal

`GET https://linearascent.net/play` serves the SAME pane Luna renders
— GAME / SCORE / COMMUNITY, pixel-identical — wired to `/play/api`
with cookie auth. Measurable: a signed-in browser at `/play` plays a
full turn (scene → click → next scene) with zero console errors; a
signed-out browser is redirected to the door and back after login.

## Steps

1. **Plugin repo** (`pane.py`) — parametrize the three Luna couplings
   behind one function signature, e.g.
   `pane_html(api_base=_API, web=False)`:
   - `API` constant → `api_base` param.
   - Auth: when `web=True`, skip the `luna-auth`/`luna-request-auth`
     postMessage dance entirely; `call()` sends no Authorization
     header (the cookie rides along) and on 401 does
     `location = '/#door?next=/play'`.
   - Full-page mode: `<title>`, a viewport meta, and the game tab
     active by default are already there; verify nothing else assumes
     an iframe parent (grep `parent.postMessage`).
   Default calls stay byte-identical for Luna — the plugin's own
   `/ui/` route calls `pane_html()` with defaults; add a plugin test
   asserting the Luna output is unchanged.
2. **Worldd** (`site.py` or `webplay.py`): `GET /play` — if
   `session_user` → `HTMLResponse(pane_html(api_base="/play/api",
   web=True))`; else 303 to `/#door?next=/play`. `_door_response`
   honors a whitelisted `next` (`/play` only) after login/signup.
3. Ship order (the both-places rule): plugin repo commit → version
   bump → `vendor_game.sh` → worldd route lands in the same outer
   commit as the vendor. Marketplace publish included so Luna and web
   run the same pane version.
4. Tests: plugin — `pane_html()` default output unchanged (snapshot
   of the Luna couplings), `web=True` contains `/play/api` and no
   `luna-request-auth`. worldd — `/play` 303s signed out, 200 signed
   in.

## Verification

- Playwright (dojo harness): signup → follow redirect to `/play` →
  intro pages click through → race `elf`, class `archer` → ROOTHOLLOW
  card visible; screenshot archived; `page.on('console')` shows no
  errors.
- In Luna: the pane still loads and plays a turn (marketplace build
  of the same version) — verifies the parametrization changed
  nothing for the host.

## Rollback

Worldd: remove the `/play` route (revert outer commit). Plugin: the
parametrization is inert for Luna (defaults preserved), so no plugin
rollback is needed unless the snapshot test failed — then revert the
plugin commit before publishing.

## Execution status

Done — 2026-08-07. Plugin 0.50.0 (commit `35a2c00`) adds
`render_pane(api_base=, web=)`; vendored into worldd and served at
`GET /play` (signed-out → 303 `/#door-signin`). Live: `/play` serves
the pane with `'/play/api'` and `const WEB = true;`; dojo 01 played a
full hunt round in the browser. Marketplace publish of 0.50.0 is
blocked by a server-side 500 on the upload endpoint (index still at
0.47.0; retried post-deploy, same 500) — Luna chat play stays on
0.47.0, which remains server-compatible; web play uses only the
vendored copy. Retry publish when the marketplace recovers.
