# Phase 1 — identity: the web tenant

## Goal

A reserved tenant `web` exists in production; `(tenant='web',
player=lower(username))` is the canonical web character; a freshly
created web doc carries the account's username as its character name so
the in-game registrar never asks for one. Measurable: creating a web
doc for account `X` yields `doc["name"] == X` and no `awaits_text`
name step in the intro; the names registry holds exactly one row for
`X`.

## Steps

1. Migration (worldd `db.py` migration list): insert the reserved
   tenant row —
   `INSERT INTO ascent_tenants (tenant, secret, name_hint) VALUES
   ('web', <random 32-byte hex>, 'the website') ON CONFLICT DO
   NOTHING`. The secret is generated, stored, and never printed or
   returned by any endpoint; `web` never appears in `/v1/enroll`
   output. Guard in `auth.py`: HMAC auth REJECTS tenant `web` (the
   web tenant is reachable only through phase-2's cookie routes), so
   a leaked row can't be replayed through `/v1/*`. The same migration
   adds `ascent_accounts.email text` — nullable, no constraints — for
   phase 4's optional resurrection email.
2. `game.py`: extend doc creation (`_load_doc`) with an optional
   `display_name` — when set (web path only), the new doc gets
   `name` filled and whatever flag the intro uses to decide the name
   ask (verify against `engine/core.py` intro flow; if the engine
   gates on `p.get("name")`, filling it is the whole step).
3. `names.py`: the account already holds the username
   (`names.ACCOUNT`). Confirm a web doc claiming the SAME name for
   its player row is a no-op for the same owner (or skip the player
   claim entirely for tenant `web` — the account claim IS the
   claim). Choose whichever `names.claim` supports with the smaller
   diff; add a test either way.
4. Tests (worldd suite, DB-backed): new web doc has the name; intro
   for a web doc skips the name prompt; `/v1/scene` with tenant
   `web` + valid-looking HMAC → 401/403.

## Verification

- `psql: SELECT tenant, name_hint FROM ascent_tenants WHERE
  tenant='web';` → one row.
- Local worldd: create doc for `webprobe1`, walk intro via
  `run_act` — story pages, race, class, then ROOTHOLLOW; assert no
  `awaits_text` name scene appears and profile ident shows
  `webprobe1`.
- HMAC probe signed with the web tenant's secret against `/v1/scene`
  → rejected.

## Rollback

- `DELETE FROM ascent_tenants WHERE tenant='web';` (no player docs
  exist yet in this phase). Revert the commit.
