# 010 — the gmail door: one way in, a name on the way

**Signing up is Gmail-only.** No password to invent, no typed email, no
5-digit code — Google proves who you are, and we ask only for the **one
word** the world will call you by, **after** the round-trip, not before.
**Signing in accepts either road:** Continue with Gmail, or the old
username + password for accounts made before this ship. (When an email
sender is approved we'll re-open password *signup* alongside Gmail; the
password *login* is kept alive for that reason — the column and the
`/login` path stay.) The race portrait — the climber's face — shows only
for a **Gmail-connected** account.

This replaces the earlier email+password+code design (plan draft, now
dropped). The mailer, the `ascent_email_codes` table, the 5-digit box,
the resend ladder and the change-email popup are all **out** — see "what
we dropped" at the end.

The look is drawn and reviewed — see **the mock** first:
`worldd/static/site/mock/gmail-door.html` (the one-button door, the
"pick your name" step, and the profile with the grey **connect Gmail**
box where the portrait sits). The 16×16 Google "G" in the game's own
inks: `gen_google_g.py` in this folder.

## The flow, end to end

1. Homepage → **[ Continue with Gmail ]** (`<a href="/auth/google/start">`).
2. Google consent → back to `/auth/google/callback` with an authorization
   code. We exchange it server-side and read the verified `email`, `sub`,
   `name` from the ID token.
3. Branch on the Google `sub`:
   - **known `sub`** → set the session cookie, 303 to `/play`. Done.
   - **new `sub`** → stash the verified Google claims in a short-lived,
     signed **pending** cookie (no account yet) and 303 to the **name
     step**.
4. **Name step** (`GET /auth/google/name`): a tiny page (the door's own
   skin) — "Signed in as ash@gmail.com. Pick your one word." Pre-filled
   from the Google given name, canonicalized.
5. `POST /auth/google/name {username}` → validate + `names.claim`; on
   success write the account (`auth_provider='google'`, `google_sub`,
   `email`, `pw_hash` NULL), clear the pending cookie, set the session,
   303 to `/play`. Name taken → re-render the step with the error.

Returning players never see step 4/5 — the known `sub` shortcuts to
`/play`.

## Where it all lives (from the survey)

- Door UI: `worldd/static/site/index.html` `#door`; submit in
  `site.js` (`doorPost`); styles in `site.css` (`.doorcard`, `.opt`).
- Auth backend: `worldd/app/site.py` — `/signup`, `/login`, `/me`,
  the `ascent_session` HMAC cookie, scrypt hashing.
- Account row: `ascent_accounts (id, username, pw_hash, email,
  created_at)` — `pw_hash` is `NOT NULL` today; `email` nullable.
- Names: `worldd/app/names.py` (`canonical`, `is_legal`, `claim`,
  `ACCOUNT`, `TAKEN`) — the one registry the door and the gate share.
- The face: `render.py:_profile_html` draws `<img class="portrait">`
  from the race PNG; the mock replaces exactly this element.
- No blue seat in the palette: Google blue borrows cyan-teal `--en`
  (`#45d0c0`); red→`#f26541`, yellow→`#f5b825`, green→`#8ed24a`.

## Data — one migration

New migration `worldd/migrations/0NN_gmail_door.sql` (next free number):

- `ALTER TABLE ascent_accounts ADD COLUMN auth_provider text NOT NULL
  DEFAULT 'password';`  — one of `password` | `google`.
- `ADD COLUMN google_sub text UNIQUE;`  — Google's stable subject id
  (never the email; emails change, `sub` does not). **This column being
  non-null is what "Gmail-connected" means** — the portrait gate and the
  login lookup both key off it.
- `ALTER COLUMN pw_hash DROP NOT NULL;`  — a Gmail account has no
  password. (`/login` already refuses a null hash via `_check_pw`.)
- `email` already exists; Gmail signups fill it with the verified
  address. No `email_verified` column is needed — a Google `sub` present
  is proof enough; we never store an *unverified* email anymore.

No new table. `ascent_accounts` stays in `era.PERMANENT_TABLES` (already
is). Backfill: every existing account keeps `auth_provider='password'`,
`google_sub=NULL` — i.e. **not** Gmail-connected (see "the old accounts").

## Server — the one door

Auth logic in `worldd/app/site.py`; the OAuth mechanics in a small new
`worldd/app/google_oauth.py` (URL build, token exchange, ID-token
decode/verify). Config in `worldd/app/config.py`:
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`
(all three already set locally in `worldd/.env` and on Render).

### `GET /auth/google/start`

302 to Google's consent screen: `scope=openid email profile`,
`response_type=code`, `access_type=online`, a signed `state` nonce in a
short `HttpOnly` cookie, and PKCE (`code_challenge`, verifier kept in the
same short cookie). If the caller already has a session, remember it in
the `state` so the callback **links** Gmail to that account instead of
making a new one (this is the profile's "connect Gmail").

### `GET /auth/google/callback?code&state`

Verify `state` against the cookie; exchange `code` (+ PKCE verifier)
server-to-server for tokens; verify the ID token (signature via Google's
JWKS, `aud`==client id, `iss`, `exp`) and read `sub`, `email`,
`email_verified`, `name`. Then:

- **linking** (session present in state) → set `google_sub`,
  `auth_provider='google'`, `email` on the current account; 303 `/play`.
- **known `sub`** → log that account in; 303 `/play`.
- **`sub` unknown, `email` matches an existing account** → link it
  (fill `google_sub`), log in; 303 `/play`. (Rescues an old account
  whose stored email equals the Google one.)
- **brand new** → write the verified claims into a signed, ~10-min
  `pending` cookie; 303 `/auth/google/name`. No account yet.

Google's `picture` URL is read and **ignored** — the face is the race
portrait, always. (Noted so nobody wires an avatar later by reflex.)

### The name step

- `GET /auth/google/name` → requires the `pending` cookie (else back to
  `/`). Renders the small "pick your name" card (server-rendered, same
  terminal skin), username pre-filled with
  `names.canonical(given_name or email local-part)`.
- `POST /auth/google/name {username}` → `names.is_legal` + `names.claim`
  in one transaction with the `INSERT INTO ascent_accounts`
  (`auth_provider='google'`, `google_sub`, `email`, `pw_hash` NULL).
  Taken/illegal → re-render with the inline error. OK → clear `pending`,
  set the session cookie, 303 `/play`.
- Reuses `_session_token` / cookie code and `_door_response` shape.

### `/me`

Add `auth_provider` and `gmail` (bool: `google_sub IS NOT NULL`) so the
profile pane knows whether to draw the portrait or the connect box.

### The old doors

- **`/login` (username + password) — KEPT and surfaced.** A returning
  climber with a pre-Gmail account signs in exactly as today. It sits on
  the door under an OR rail, below the Gmail button.
- **`/signup` (username + password) — kept wired, hidden from the UI.**
  New accounts only come through Gmail for now. `/signup` stays reachable
  (scripts-off / emergency / tests) but is not surfaced on the homepage.
  When the email sender is approved we re-surface it beside Gmail — this
  is why the password path is preserved rather than deleted.

## The door — frontend (`index.html` + `site.js` + `site.css`)

Matches the mock:

- The `#door` card leads with the **`.gbtn`** row —
  `<a href="/auth/google/start">` with **"Continue with Gmail"** + the
  inline 16×16 `.gicon-svg`. Hover borders gold like every option. Works
  scripts-off (it's a link). This one button both signs up and signs in.
- Below it, an **OR rail** (`.or`) and a compact **sign-in** form for
  returning password accounts: username + password + `[ SIGN-IN ]`,
  `formaction="/login"`. No SIGN-UP button, no email/retype fields — the
  only password path left on the page is *login*. `site.js` keeps the
  `doorPost("/login")` branch; the signup branch/tabs are dropped from
  the visible UI (the endpoint stays).
- The G glyph ships as a tiny reusable snippet — authored once by
  `gen_google_g.py`, inlined as `<svg>` (11 lit-pixel colors, ~90
  rects). The same data can seed a `google_g()` helper in `render.py`
  for the profile's connect box.
- `?door_err=` handling stays (login can still fail with a bad password).

## The profile — the portrait gate (`render.py`)

In `_profile_html`: draw the `<img class="portrait">` **only** when the
account is Gmail-connected. When it is **not** (an old password account
that hasn't linked), replace the portrait with the `.vbox` **connect
Gmail** box from the mock:

- **CONNECT GMAIL** title, "Your climber's look appears once your account
  is linked to Gmail.", a dotted rule, then the plain-text **connect
  Gmail** link (the 16×16 G before it, "Gmail" underlined) →
  `<a href="/auth/google/start">`. (Roy: "no button just text.")
- Everything to its right (meters, pips, pack) is unchanged; the box
  occupies the exact 140-wide portrait slot.

The `gmail` flag is threaded from the account row through
`game._load_doc` / webplay identity into the `Scene` (a single new field).
Because the pane is one code path shared by web and Luna
(`vendor_game.sh`), the box only ever renders for the **web** tenant with
an unlinked account; Luna players and Gmail-connected web players get the
portrait as today.

### The old accounts

New accounts are Gmail from step one, so they always carry a face. The
only accounts that can see the connect box are **pre-010 password
accounts**. Default: they see the connect box until they link Gmail
(one click, `sub` matched or freshly linked). This honors "the portrait
shows only when Gmail is connected" literally. If yanking faces off
mid-climb feels wrong, the alternative is a one-line grandfather
(`created_at < ship_ts` keeps the portrait) — flagged, not chosen.

## Google setup (novalystrix.ai org) — done

Already completed in the browser handoff:

1. Google Cloud Console → **novalystrix.ai** org → the `novalystrix`
   project.
2. OAuth client "Linear Ascent" (Web application) created; consent
   screen External, scopes `openid email profile`.
3. Authorized redirect URIs:
   - `https://linearascent.net/auth/google/callback`
   - `http://localhost:8000/auth/google/callback` (local dev).
4. Client id + secret in `worldd/.env` (dev) and Render env
   (`GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI`).

While the consent screen is in **testing**, add test users (Roy's
accounts) or publish it before public launch.

## Tests

worldd `tests/test_010_gmail_door.py` (mock the Google token exchange /
ID-token decode so no network):

- callback with a **new `sub`** → no account yet, `pending` cookie set,
  303 to `/auth/google/name`; then `POST name` → account exists,
  `auth_provider='google'`, `google_sub` set, `pw_hash` NULL, name
  claimed in the registry, session cookie set.
- callback with a **known `sub`** → straight 303 `/play`, session set,
  no second account.
- callback whose **email matches** an existing password account → linked
  (`google_sub` filled), not duplicated.
- name step: taken name → re-render with error, no account written;
  missing/expired `pending` cookie → redirect to `/`.
- `state` mismatch or bad ID token → 400, no account, no session.
- `/me` returns `gmail: true/false` and `auth_provider`.
- password `/login` still works for a legacy account; a null-`pw_hash`
  Google account cannot log in by password.

plugin `tests/test_010_portrait_gate.py`:

- `_profile_html` for a `web`, **not** Gmail-connected account contains
  the **CONNECT GMAIL** box, the `connect Gmail` text link, and **no**
  `<img class="portrait">`.
- Gmail-connected web account, or a Luna player → the portrait, no box.
- `google_g()` returns the 4-ink SVG; snapshot the pixel count/colors.

Plus a **dojo** run (`.cursor/skills/run-dojo`): a fresh browser through
the Gmail door end-to-end against QA — consent, land on the name step,
pick a name, watch `/play` open with the face; then hit the door again
and confirm it walks straight back in.

## Order

1. **Data** — the migration; confirm `PERMANENT_TABLES`.
2. **OAuth core** — `google_oauth.py` (URL build, token exchange, ID
   token verify) + `config.py` wiring; unit tests with a mocked exchange.
3. **The doors** — `/auth/google/start`, `/auth/google/callback`, the
   name step; `/me` flags; tests.
4. **The front door** — swap the `#door` form for the Gmail row in
   `index.html`/`site.css`; trim `site.js`.
5. **The gate** — `render.py` portrait gate + connect box + `google_g()`;
   thread the `gmail` flag; tests.
6. **Ship** — vendor the plugin (`vendor_game.sh`), migrate + deploy on
   Render (deploys are manual — `render deploys create … --wait` +
   `/health`), publish the consent screen, dojo the funnel, archive.

## What we dropped (from the earlier draft)

- Typed-email signup, the required-email field, the email format regex.
- `ascent_email_codes`, the 5-digit code, `POST /me/verify(/resend/
  change-email)`, the resend ladder, the change-email popup.
- `worldd/app/mailer.py` and any SMTP/provider decision — **no email is
  sent by the game at all** now.
- `email_verified` column — replaced by "has a Google `sub`".

## Out of scope (noted, not built)

- Other providers (Apple, GitHub). The `auth_provider` column leaves room.
- Using Google's profile picture as an avatar — the face is the race
  portrait, on purpose.
- Password reset / hard-retiring the password door — a later call.
- Linking one character across Luna and web (still 005's non-goal).
