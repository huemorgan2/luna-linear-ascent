# 01 — signup to first hunt, in the browser, under a minute

## Preconditions

- Production `linearascent.net` live; `/health` game matches the
  shipped version.
- No account or cookies for the test username (`webprobe-<hex>`,
  fresh every run).

## Scenario

1. Open a clean browser context at `https://linearascent.net/`.
   Screenshot the homepage.
2. Find the signup card WITHOUT scrolling more than one viewport.
   Sign up as `webprobe-<hex>` / a 10-char password. Start a timer.
3. Follow wherever the site takes you — no manual URL entry.
4. Click through THE STORY SO FAR pages. Choose race `elf`, class
   `archer`.
5. Continue until the ROOTHOLLOW square card is visible. Stop the
   timer. Screenshot.
6. Open the profile area; read the ident line.
7. Click The Tower Gate → floor 1 → play through the floor movie →
   `hunt` → resolve one combat round.

## Expected behavior

- Signup lands directly in the game (`/play`) — no dead-end "signed
  up" page, no instructions to install anything.
- The intro NEVER asks to type a character name; the ident line shows
  `webprobe-<hex>` as the name.
- Signup → ROOTHOLLOW in under 60 seconds of normal clicking.
- The hunt renders the enemy card and the swing resolves — a full
  game turn works in the browser.

## Fail conditions

- Any scene asks the player to type a name (identity split between
  door and gate — regression on phase 1).
- Redirect lands on the homepage or `/#door` after signup instead of
  the game.
- A click produces "the lift jams", a blank card, or a console error.
- The page requires anything Luna: mentions of installs, tokens, or a
  plugin.

## Verify

- DB: `SELECT doc->>'name' FROM ascent_players WHERE tenant='web' AND
  player='<username>'` → the username.
- worldd logs: the session's acts carry tenant `web`; no HMAC errors.
- `/play/api/pane/scene` with the browser's cookie returns the same
  scene the page shows (no divergent state).
