# 004 — One name, one world

The door asked for a username. The gate asked for a name. They were two
different strings, neither one unique, and the game printed both as if they
were the same person. This plan makes them one thing.

**The law.** A climber's name *is* their username: one word, unique across the
whole world — every tenant, and the site's door too. `Master Chief` is
`MasterChief`; the space is joined, not refused.

---

## Phase 1 — The naming law lives in the engine

`plugin_linear_ascent/engine/names.py` — one function, one rule, imported by
both sides. worldd enforces it (registry, door); the engine asks for it. Two
copies of a naming law is one law and one bug.

- `canonical(raw)` — strip, keep letters and numbers of **any** script plus
  `-` and `_`, cut to 24. Spaces **join**: a player who types `Master Chief`
  means `MasterChief`, and refusing them mid-creation is a worse welcome than
  doing it. Case is kept — the name is a legend, `MasterChief` carves better
  than `masterchief` — and uniqueness is case-blind, so nobody gets to be the
  *other* masterchief. `Криер` is a name; the alphabet this bans is
  punctuation and gaps, not other people's letters.
- `is_legal(name)` — 2 to 24 strokes of that alphabet.

## Phase 2 — The gate asks for a username

`creation_name` becomes the username step:

- the card says username, and says the two things that surprise people: it is
  what everyone will read, and it is one word.
- typed `Nyx of the Vale` → `NyxoftheVale`, taken, with the card saying it
  joined the words rather than silently pocketing a different name.
- a name already climbing comes back refused — *"one name, one world"* — and
  the card asks again. The engine cannot know that alone; see Phase 3.

## Phase 3 — The registry (worldd is the only judge)

`ascent_names` — `name_lower` primary key, the name as typed, `kind`
(`account` | `climber`), and the owner (`tenant`, `player`) for a climber.
**Permanent** (`app/era.py`): the Stone keeps names, so an era reset must not
hand `Brackjaw` to a stranger. The row remembers its owner, so the same hands
reclaim their own name in the next era for free.

- `app/names.py` — `claim()` returns `created` / `mine` / `taken`, and
  `release()` undoes a claim the engine then didn't take.
- `game.run_act` claims **before** the engine runs (the name step, text turn
  only), leaves the verdict in `doc["_world"]["name_claim"]`, and releases the
  row if the engine did not end up carving it. One transaction, so two
  climbers racing for `Fleet` cannot both win.
- Local (offline) play has no registry and no flag: single-player keeps
  whatever it likes.

### Migration 013 — the names that already exist

Nothing is dropped; names are transformed in place (devprocess §data).

1. account usernames get their words joined (the old alphabet allowed spaces
   and `'`), collisions resolved with a numeric suffix, `ascent_accounts`
   updated;
2. every player doc name likewise — accounts win a tie, they outlive the
   climb;
3. both are inserted into `ascent_names` as their kind.

## Phase 4 — The door reads sign-up / sign-in

`static/site/index.html`, `site.js`, `site.css`, `app/site.py`:

- the gate's call to action is **`[ SIGN-UP — free, no email ]`**; the door's
  second button is **`[ SIGN-IN ]`**, and the card carries two tabs so the form
  says which one it is.
- **sign-up**: `USERNAME`, `NEW PASSWORD`, `RETYPE PASSWORD` — a mismatch is
  refused with the reason, client-side and again at the server, in the same
  voice as the rest.
- **sign-in**: `USERNAME`, `PASSWORD` — the retype row is gone.
- scripts off, the page still works: both submit buttons are in the markup with
  their `formaction`, and the server canonicalizes and matches regardless.
- signing up claims the name in `ascent_names` in the same transaction as the
  account, so the door and the gate cannot both hand out `Fleet`.

---

## Tests

`plugin-linear-ascent/tests/test_034_one_name.py`

- `canonical` joins words, keeps case, drops what granite can't hold, cuts at 24
- the gate takes `Nyx of the Vale` as `NyxoftheVale` and says it joined them
- a name the world has already claimed is refused and the card asks again
- one stroke, and a name of nothing but punctuation, are both refused

`worldd/tests/test_names.py`

- claim → `created`, again by the same hands → `mine`, by other hands → `taken`
- case-blind: `fleet` cannot take `Fleet`
- the site's door and the gate share one namespace, both directions
- a creation turn through `/v1/act` claims the name; a second tenant asking for
  it is refused and stays in creation
- release puts a name back when the engine refused it
- `ascent_names` is permanent across an era reset, and its owner reclaims

`worldd/tests/test_site.py` (updated)

- sign-up needs both passwords and refuses a mismatch
- `Master Chief` at the door becomes `MasterChief`
- the page says SIGN-UP and SIGN-IN, and posts without JS
