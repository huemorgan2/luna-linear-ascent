# Phase 4 — the funnel: signup lands you in the game

## Goal

The distance from "visitor" to "first scene" is one form. Measurable:
submitting the homepage signup form lands the browser at `/play`
showing THE STORY SO FAR; the homepage tells visitors the game plays
in the browser.

## Steps

1. `site.py` `_door_response`: non-JSON success redirects to `/play`
   (today `/#door`). JSON callers (`wants_json`) are unaffected —
   Luna flows don't use the door.
2. Homepage: the fixed status line / nav gains `PLAY` (signed in,
   via `/me`) or `SIGN UP & CLIMB` (signed out, anchors the door).
   Copy on the door card: "plays in the browser — nothing to
   install" (the 003 sell, now literally true).
3. Logged-in visits to `/` keep working as the sales page; `/play` is
   the game. No auto-redirect from `/` — people share the homepage.

## Verification

- Browser: fresh signup on the homepage → next paint is `/play` with
  the intro card. Login → `/play`. Logout → homepage.
- `curl -s https://linearascent.net/ | grep -io "nothing to install"`
  → present.

## Rollback

Revert the commit — both changes are presentation-only.
