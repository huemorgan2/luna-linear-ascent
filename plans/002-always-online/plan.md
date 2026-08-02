# 002 — Always online: cards that actually click, a world you're always in

Status: PLANNED
Scope: coordination plan across the three repos in this workspace
(`luna` fork, `plugin-linear-ascent`, `worldd`).

## The problems (as reported playing the game)

1. **Clicking a card option does nothing.** The option doesn't get
   selected; only typing in chat works.
2. **Multiplayer is opt-in and invisible.** The plugin only connects to
   worldd if you find the settings tab and press "Join the shared world";
   otherwise you silently play solo. Wanted: the plugin always connects,
   and shows how many players climbed today — including yourself.

## Root causes (verified in code)

### P1 — the card-action bridge is missing from the running Luna

- The plugin's half shipped (0.3.1+): buttons post
  `{type:'luna:card:action', nonce, path:'/api/p/plugin-linear-ascent/act',
  body:{option, scene_id}}` to the parent and wait 6s for
  `luna:card:result` (`plugin-linear-ascent/plugin_linear_ascent/render.py:147-183`).
- The host's half exists only in Luna commit `c855ff3`
  ("057 card-action bridge + card follow-scroll") on branch
  `origin/056-followup-card-ordering` — **not an ancestor of current HEAD**
  (`4077ee8`). In the checkout, the only `message` listener touching card
  iframes hard-returns on anything that isn't `luna:embed:height`
  (`luna/ui/src/views/ChatPanel.tsx:112-122`), so the action message has
  no receiver. Timeout fires, buttons unlock, nothing is logged.
- Contributing confusion: "057" means *card actions* in the plugin but
  *mobile-responsive* in the Luna fork (`luna/plans/057-mobile-responsive/`).
  The bridge was built in a parallel session and never merged.
- Two follow-on requirements once the bridge lands:
  - the standalone card render must pass the plugin id:
    `ChatPanel.tsx:2499` renders `<PluginEmbed … asIframe card />` with no
    `source=` — the bridge is gated on `card && source` and uses `source`
    for the `/api/p/${source}/` prefix guard;
  - the sandboxed iframe (`sandbox="allow-scripts"`, opaque origin, no
    cookie) can never call `/act` itself — the parent bridge must carry
    auth. `POST /api/p/plugin-linear-ascent/act` requires
    `get_current_user` (`routes.py:163-196`).

### P2 — solo is the default; no player metric exists

- Backend resolution at load (`plugin_linear_ascent/plugin.py:126-164`):
  env creds → vault creds → **falls through to local solo**. Joining is a
  manual button in the settings tab (`routes.py:117-161` → worldd
  `POST /v1/enroll`, idempotent per vault-stored `install_id`).
- worldd (FastAPI + Postgres, deployed at
  `https://ascent-worldd.onrender.com` via `render.yaml`) has no
  presence endpoint, but `ascent_players.updated_at` is bumped on **every**
  scene/act (`worldd/app/game.py:56`), so distinct rows with
  `updated_at >= start of current world-day` (day rolls at UTC 06:00,
  `config.py:19`) = daily active players. `GET /admin/world` already
  computes an all-time count, but it's admin-gated.

## Target behavior

- **Clicking an option acts.** Button click → host bridge → authed
  `POST /act` → next scene card posts into the timeline; buttons lock
  during flight; on failure they unlock with the existing
  "reply with a number to act" hint. Typing a number keeps working.
- **The plugin is always in the world.** On load, with no stored
  credentials, it enrolls automatically (silent, idempotent). No button
  required. If worldd is unreachable, the game still runs (degraded solo)
  and reconnects automatically — never a bricked game.
- **Daily climbers are visible.** "Climbers today: N (including you)" in
  the settings status card, and a small stat on scene cards. The current
  player always counts: connecting touches their row.

## Workstreams and where they live

### W1 — Luna fork: land the card-action bridge (fixes P1)

1. Merge/cherry-pick `c855ff3` from `origin/056-followup-card-ordering`
   onto the deployed branch. If the merge is messy, reimplement its three
   parts on mainline:
   - `api.cardAction(path, body, conversationId, messageId)` in
     `ui/src/lib/api.ts` — authed POST from the shell;
   - in `PluginEmbed` (`ChatPanel.tsx`): a `message` listener gated on
     `card && source`, matching `d.type === 'luna:card:action'` and
     `e.source === frame.current.contentWindow`, enforcing the
     `/api/p/${source}/` path prefix (confused-deputy guard), replying
     `{type:'luna:card:result', nonce, ok, status, body}`;
   - the bridge test (`057-card-action-bridge.test.tsx`).
2. Pass `source={m.source}` at the standalone card render
   (`ChatPanel.tsx:2499`). Leave the legacy in-bubble path click-less
   (it has no `card` prop; stock behavior unchanged).
3. Rename the incoming work to avoid the numbering collision with
   `luna/plans/057-mobile-responsive/` — file the bridge under
   `luna/plans/058-card-action-bridge/` with a note pointing at the
   plugin's phase-9 summary.
4. Rebuild the UI, restart QA Luna (8777).

No plugin changes needed for P1 — the client half already ships in 0.4.1
(`render.py`, `test_card_actions.py` is the contract).

### W2 — Plugin: auto-join on load (P2a)

1. Extract the enroll logic out of the `/join` route
   (`routes.py:128-159`) into a reusable
   `ensure_enrolled(ctx) -> bool` (create/read vault `install_id`,
   `POST {DEFAULT_WORLD_URL}/v1/enroll`, store `tenant/secret/url`,
   `runtime.configure_remote(source="vault")`).
2. In `on_load` (`plugin.py:126-164`): after the env→vault checks, when
   neither yields credentials, call `ensure_enrolled` instead of falling
   through to solo. On success, touch the player row (one
   `WorldClient.character` call) so the daily count includes this player
   immediately.
3. Failure handling — "force" must not mean "brick offline":
   - enroll failure → stay on `LocalBackend`, schedule retries with
     backoff; also re-attempt lazily on the next `scene_for`/`act_for`
     when `source == "local"` and no explicit opt-out is set;
   - mid-session worldd errors keep today's behavior (remote errors
     surface; no silent divergence of world state).
4. Settings tab (`routes.py:221-334`) reframes: status-first ("Connected
   to the shared world" / "Reconnecting…"), the Join button becomes a
   "Retry now" shown only while disconnected. Keep "Disconnect" as the
   explicit opt-out; store an opt-out flag in the vault so auto-join
   respects it (disconnect that doesn't stick is a bug, not a feature).
5. Enroll is IP-rate-limited 5/hr on worldd (`main.py:123`) and
   idempotent per `install_id` — auto-join fits, but retries must back
   off well under that limit.

### W3 — worldd: daily-players stat (P2b)

1. New public endpoint `GET /v1/world/stats` (`worldd/app/main.py`),
   unauthenticated like `/health`, lightly cached (≥30s in-process):
   `{daily_players, world_day, server_time}` from
   `SELECT count(*) FROM ascent_players WHERE updated_at >= $day_start`
   with `$day_start` = today at UTC 06:00 (reuse the world-day helpers).
   No migration needed.
2. Add `daily_players` to the `_world` payload injected into scenes
   (`worldd/app/social.py:21-75`) so cards can show it without an extra
   round-trip.
3. Tests: day-boundary math around the 06:00 UTC rollover; count
   includes a player whose only touch is `character` (the W2 connect
   touch); cache doesn't serve a stale count across the rollover.
4. Bump worldd to 0.4.0, `vendor_game.sh` sync, redeploy on Render.

### W4 — Plugin: surface the count (P2b)

1. `/status` route (`routes.py:98-115`): also fetch `/v1/world/stats`;
   settings status card gains a "Climbers today" row — rendered as
   "N (including you)" once connected.
2. Scene cards (`render.py:render_scene`): when `_world.daily_players`
   is present, show a small footer/eyebrow stat ("N climbers on the
   mountain today"). Absent (solo/degraded) → omitted, no layout shift.
3. Version 0.5.0 in `version.py` + `luna-plugin.toml`.

## Execution order

1. **W1 first** — it fixes a shipped-but-broken feature and needs no
   plugin/worldd changes. Browser-verify on QA Luna (8777): click an
   option → next card appears; kill the network → buttons unlock with the
   number-fallback hint; number-typing path still works; page reload
   keeps the timeline; mobile width (Luna 057) unaffected.
2. **W3** (worldd stats endpoint) — deployable independently; verify
   `GET /v1/world/stats` live on Render.
3. **W2 + W4** (plugin 0.5.0) — dojo/browser check the full matrix:
   - fresh install, worldd up → auto-joins, settings shows Connected +
     climbers count including self, cards show the stat;
   - fresh install, worldd down → game runs solo, settings shows
     Reconnecting, later auto-recovers;
   - explicit Disconnect → stays disconnected across restarts;
   - existing vault-joined install → unchanged tenant, progress intact.
4. Tests: plugin suite (auto-join branches, opt-out flag, stats
   rendering both present/absent), worldd suite (W3), Luna bridge test.
5. Ship: commit Luna fork, redeploy worldd, publish plugin 0.5.0 to the
   marketplace, bump submodules + vendor sync in this repo, write the
   phase summary under `plugin-linear-ascent/plans/003-execution/`.

## Risks

- **Merge drift on `c855ff3`**: mainline `ChatPanel.tsx` has moved (056
  series + 057-mobile landed after the branch forked). If conflicts are
  nontrivial, reimplement rather than force the merge — the bridge is
  ~3 small pieces and has a test.
- **Stock-Luna marketplace users** still lack the bridge until it lands
  upstream → their buttons keep falling back to "reply with a number to
  act", which is the designed degradation. Note it in the plugin README.
- **Auto-enroll consent**: joining a shared world becomes default-on.
  Mitigate with the sticky opt-out (W2.4) and a one-line "connected to
  the shared world" status the player can see. Nothing personal is sent
  (install_id + optional name hint).
- **Enroll rate limit (5/hr/IP)**: retry backoff must cap attempts;
  a retry storm from one household/NAT could lock out fresh installs.
- **Public stats endpoint** exposes a population number and adds an
  unauthenticated query — cache it and keep the response to counts only.
- **Count semantics**: `ascent_players` rows are per (tenant, player);
  multiple characters per install would inflate "players". Acceptable
  now; note it. "Including you" is guaranteed by the W2 connect-touch,
  not by display-side +1 arithmetic (no double counting).
