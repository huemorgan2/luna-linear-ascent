# Funnel Fighters — visitor + signup funnel tracking

Goal: know that people visit, sign up, enter the game, and come back.
Nothing inside the game is tracked. One file owns every line of Funnel
Fighters code; the rest of the site only calls its functions.

## The one file

`worldd/static/site/funnel.js` — the ONLY place the vendor exists:

- the async loader snippet (queue shim + script insert), verbatim from
  the vendor, wrapped in our function
- config at the top, one block:
  ```js
  var FF_SITE = "4a62eb26-43d4-464e-835e-b11481d24645";
  var FF_HOST = "https://funnelfighters.io";
  var FF_SDK  = FF_HOST + "/sdk/funnelfighters.js";
  var PAGES   = { "/": "home", "/mechanics": "mechanics", "/play": "play" };
  ```
- a tiny public API on `window.ff` — every function is adblock-safe
  (no-ops if the SDK never loaded) and never throws:

  | function            | what it sends                                   |
  |---------------------|--------------------------------------------------|
  | `ff.page()`         | `page_view {page}` — called automatically on load, page name from `PAGES[location.pathname]` |
  | `ff.door(tab)`      | `door_view {tab}` — signup/signin tab reached    |
  | `ff.signup(step, reason)` | `signup_try` / `signup_ok` / `signup_err {reason}` |
  | `ff.signin()`       | `signin_ok` — a player came back through the door |
  | `ff.enter()`        | `enter_game` — called automatically when pathname is `/play` |
  | `ff.who(username)`  | `identify(username)` — ties return visits to the account |

- auto behavior on load: init SDK → `ff.page()` → if on `/play`,
  `ff.enter()` + `ff.who()` from the script tag's `data-user` attribute.
  So `/play` needs the tag and nothing else.

Return visits ("they come back") need no custom event: the FF visitor
cookie counts returning visitors on every `page_view`, and `ff.who()`
names them once signed in. `signin_ok` is the explicit come-back marker.

## Every placement (complete list)

| # | file | change |
|---|------|--------|
| 1 | `worldd/static/site/funnel.js` | NEW — everything above |
| 2 | `worldd/static/site/index.html` | one `<script src="/static/site/funnel.js?v=…" defer>` tag |
| 3 | `worldd/static/site/mechanics.html` | same single tag |
| 4 | `worldd/static/site/site.js` | 6 one-line calls in existing handlers: `hashMode()`/`setMode()` → `ff.door(mode)`; form submit → `ff.signup("try")`; doorPost success on `/signup` → `ff.signup("ok")`; doorPost success on `/login` → `ff.signin()`; doorPost error → `ff.signup("err", detail)`; `/me` returns signed-in → `ff.who(user)` |
| 5 | `worldd/app/webplay.py` (`play_page`) | server-side inject one tag into the pane HTML before `</head>`: `<script src="/static/site/funnel.js?v=…" data-user="{username}" defer></script>`. The plugin repo is NOT touched — Luna chat cards and the chat pane never see the tracker; only the website's `/play` does |

Not tracked, on purpose: `admin.html`, `mock/*`, every in-game action
(`/play/api/*` stays clean), the plugin itself.

## Every event (complete list)

| event | fired from | funnel meaning |
|-------|-----------|----------------|
| `page_view {page: home\|mechanics\|play}` | funnel.js auto | visitor + return visitor |
| `door_view {tab: signup\|signin}` | site.js | reached the door |
| `signup_try` | site.js | submitted the form |
| `signup_ok` | site.js | account created |
| `signup_err {reason}` | site.js | where signups die |
| `signin_ok` | site.js | came back and signed in |
| `enter_game` | funnel.js auto on /play | the game actually opened |
| identify(username) | site.js `/me` + /play `data-user` | names the visitor |

The funnel reads: `page_view(home)` → `door_view` → `signup_try` →
`signup_ok` → `enter_game`, then later `page_view` (returning) →
`signin_ok` → `enter_game`.

## Tests (worldd/tests/test_funnel.py, new)

1. `/` and `/mechanics` HTML contain the funnel.js tag; funnel.js serves
   with the site id inside.
2. `/play` (signed-in session) contains the injected tag with
   `data-user="<username>"`.
3. `admin.html` does NOT contain funnel.js.
4. The plugin pane rendered for Luna (`render_pane(web=True)` output
   before injection / chat card HTML) contains no `funnelfighters`.

## Execution order

1. Write funnel.js. 2. Tags in index/mechanics. 3. site.js calls.
4. webplay.py injection. 5. test_funnel.py. 6. Full worldd suite.
7. Commit root repo (these files only — the bestiary session's dirty
   art/mock files stay out). Deploy only on your word, as always.

No plugin version bump — the plugin repo has zero changes.
