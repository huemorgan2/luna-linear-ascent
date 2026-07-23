# luna-linear-ascent

**Linear Ascent** — a LORD-style multiplayer text RPG for [Luna](https://luna.com.ai): the frontier village of Roothollow, a 100-floor arcanotech tower, daily energy pacing, bank interest, offline PvP, guild boss quorums, and the Luna agent playing your shardmind sidekick.

Two parts:

| Part | Runtime | Role |
|---|---|---|
| **`plugin-linear-ascent/`** (git submodule) | Python, loaded into your Luna | The game: tools (`ascent_*`), chat cards, 1-bit banners, engine, sidekick. Repo: [huemorgan2/plugin-linear-ascent](https://github.com/huemorgan2/plugin-linear-ascent) |
| **`worldd/`** — `ascent-worldd` | FastAPI, deployed on Render (always-on) | The one shared world: authoritative state, world-day rollover, PvP/letters/grants/quorums across all Luna installs. |

The two talk over HTTPS, **HMAC-signed** with a shared secret. The plugin sends intents; worldd rolls dice, applies the economy, and returns outcomes.

```
players ── chat ── Luna + plugin-linear-ascent ──signed HTTP── ascent-worldd (Render, 24/7) ── Postgres
```

Plans: game production in [plugin-linear-ascent/plans/002-full-game](https://github.com/huemorgan2/plugin-linear-ascent/blob/main/plans/002-full-game/plan.md) · service in [worldd/plans/001-worldd](worldd/plans/001-worldd/plan.md).

---

## Quick start

### 0. Prereqs
- A running **Luna**.
- A **Render** account (for the always-on world service).
- Two secrets:
  ```bash
  export ASCENT_SHARED_SECRET=$(openssl rand -hex 32)   # worldd <-> plugin HMAC
  export ASCENT_ADMIN_KEY=$(openssl rand -hex 16)       # protects /admin/* (tenant registration)
  ```

### 1. Deploy worldd to Render
1. Push this repo to GitHub.
2. Render → **New → Blueprint** → pick the repo. It reads `render.yaml`:
   an `ascent-worldd` web service (**starter** plan — lowest paid, always-on)
   + an `ascent-world-db` Postgres (**starter**).
3. Set these env vars on the service (Dashboard → Environment):
   - `ASCENT_SHARED_SECRET` — the value from step 0.
   - `ASCENT_ADMIN_KEY` — the value from step 0.
   - `DATABASE_URL` is wired automatically from `ascent-world-db`.
4. Deploy. When live, open
   `https://ascent-worldd.onrender.com/health` → should show `"ok": true` with the server time.

### 2. Install the plugin into Luna
Copy `plugin-linear-ascent/plugin_linear_ascent/` into your Luna's plugins directory (or package + install from a marketplace). Set on the **Luna** side:
```bash
LUNA_ASCENT_WORLDD_URL=https://ascent-worldd.onrender.com
LUNA_ASCENT_SHARED_SECRET=<same ASCENT_SHARED_SECRET>
```
Restart Luna. The `ascent_*` tools become available; say "play linear ascent" to roll a character.

> Until the plugin reaches its multiplayer phase, it also runs fully standalone on its local `StateBackend` — no service needed for solo floors 1–10.

### 3. Local Luna
worldd never calls Luna back — all traffic is plugin → worldd — so a local Luna needs **no tunnel**. Just point `LUNA_ASCENT_WORLDD_URL` at the Render URL (or at `http://localhost:8600` when running worldd locally).

---

## Configuration

### worldd (Render env)
| Var | Required | Meaning |
|---|---|---|
| `ASCENT_SHARED_SECRET` | ✅ | HMAC secret shared with the plugin (bootstrap tenant) |
| `ASCENT_ADMIN_KEY` | ✅ | protects `/admin/*` tenant registration |
| `DATABASE_URL` | ✅ | Postgres (wired by the blueprint) |

### Plugin (env / vault)
| Var | Required | Meaning |
|---|---|---|
| `LUNA_ASCENT_WORLDD_URL` | for multiplayer | worldd base URL |
| `LUNA_ASCENT_SHARED_SECRET` | for multiplayer | same as `ASCENT_SHARED_SECRET` (or vault key `plugin_linear_ascent.shared_secret`) |

---

## Local development

```bash
# worldd
cd worldd
python -m venv .venv && .venv/bin/pip install -r requirements.txt
DATABASE_URL=postgres://... .venv/bin/uvicorn app.main:app --port 8600 --reload

# plugin — work happens in the submodule; see its README
git submodule update --init
```

## License

MIT — see [LICENSE](LICENSE).
