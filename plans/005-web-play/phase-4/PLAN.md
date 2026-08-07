# Phase 4 — the funnel: signup lands you in the game

## Goal

The distance from "visitor" to "first scene" is one form, reachable
from the top of the page. Measurable: submitting signup OR login —
JS fetch or scripts-off form POST — lands the browser at `/play`
showing THE STORY SO FAR; a sign-in option sits in the first viewport
(today the door is only at the bottom); signup carries an optional
email field stored on the account.

## Steps

1. `site.py` `_door_response`: non-JSON success redirects to `/play`
   (today `/#door`). JSON success keeps `{ok, username}` — `site.js`
   itself navigates to `/play` on ok (both signup and login), so both
   script paths funnel the same way. Luna flows don't use the door.
2. **Sign-in at the top** (Roy, 2026-08-07: "now it's just in the
   bottom"): the fixed header bar gets `[ SIGN IN ]` (signed out,
   anchors `#door` in sign-in mode) / `[ ▶ PLAY ]` (signed in, links
   `/play`), decided by `/me`. The gate card's nav gains
   `[ SIGN-IN ]` beside `[ SIGN-UP ]`.
3. **Clear flow**: `#door` links carry a mode (`#door-signin` /
   `#door`), and `site.js` flips the form's tab accordingly, so "sign
   in" from the top opens the door already on the sign-in tab. A
   signed-in visitor's door card shows "You're in, <name>" with
   `[ ▶ ENTER THE TOWER ]` → `/play` plus sign-out.
4. **Optional email** (resurrection): signup form gains
   `EMAIL — optional, for resurrection` under the passwords, signup
   mode only. `site.py` stores it as-is (trimmed, ≤254 chars) into
   `ascent_accounts.email` (column from phase 1). No validation, no
   verification mail, no flow — deliberately dumb.
5. Homepage copy: door card and floor-3 card say the game plays in
   the browser — "nothing to install"; footer's "Browser climb:
   soon" becomes a `/play` link. No auto-redirect from `/` — people
   share the homepage.

## Verification

- Browser: fresh signup on the homepage → next paint is `/play` with
  the intro card. Login → `/play`. Logout → homepage. Scripts-off
  form POST → 303 to `/play`.
- Header of a signed-out page shows `[ SIGN IN ]`; clicking it lands
  on the door with the SIGN-IN tab active.
- `psql: SELECT email FROM ascent_accounts WHERE username=$probe` →
  the typed address; signup without email still works (NULL).
- `curl -s https://linearascent.net/ | grep -io "nothing to install"`
  → present.

## Rollback

Revert the commit — presentation plus one nullable-column write; no
data to unwind (the email column itself stays, harmless).

## Execution status

Done — 2026-08-07, commit `6f2f0f3`, live on production. Both doors
(JSON and scripts-off form) land on `/play`; top bar gained
`[ SIGN IN ]` (flips to `[ ▶ PLAY ]` when signed in); gate card gained
a SIGN-IN option; `#door-signin` anchor works scripts-off and flips
the door tab via JS (dojo 02 verified the flip + hidden email row);
optional resurrection email stored trimmed or NULL (test-verified).
`test_site.py` redirect expectation updated to `/play`.
