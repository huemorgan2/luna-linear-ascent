---
name: render-production
description: >-
  Access Linear Ascent production on Render.com — the ascent-worldd web
  service and ascent-world-db Postgres: query the production database, check
  deploy status, view logs, trigger deploys, and manage environment
  variables. Use when the user mentions production, Render, deploy,
  production database, worldd on Render, or needs to check/query live world
  data.
---

# Render Production Access — ascent-worldd

## The deployment

Defined by the root `render.yaml` blueprint:

| Resource | Name | Plan | Region |
|---|---|---|---|
| Web service | `ascent-worldd` | starter (always-on, `numInstances: 1`) | oregon |
| Postgres 16 | `ascent-world-db` | starter | oregon |

- **Runtime**: Python, `rootDir: worldd`, start:
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health**: `https://ascent-worldd.onrender.com/health` →
  `{"ok": true, "api": 1, "server_time": ..., "db": true}`
- **Single instance is load-bearing**: world-day rollover runs in-process
  under a Postgres advisory lock. Never scale above 1 instance.

Use the `user-render` MCP server for dashboard operations (deploy status,
logs, env vars) when possible; fall back to the browser on the Render
dashboard otherwise.

## Production Database

Get the **external** connection string from the Render dashboard
(`ascent-world-db` → Connect → External Database URL) or via the `user-render`
MCP; it is not stored in this repo. Then:

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:$PATH"
PROD_DB="<external connection string>"
psql "$PROD_DB" -c "YOUR QUERY HERE"
```

**CRITICAL RULES:**
- **NEVER DELETE production data** — always migrate and preserve. Player
  characters, ledgers, and world history are irreplaceable.
- **NEVER run DROP, TRUNCATE, or DELETE** without explicit user approval
- The `ledger` table is **append-only** — never UPDATE or DELETE its rows
- Use read-only queries by default (`SELECT`, `\d`, `\dt`)
- For writes, always confirm with the user first
- Prefer `UPDATE ... WHERE` over destructive operations

### Common queries

```bash
# Table list
psql "$PROD_DB" -c "\dt"

# World state (singleton)
psql "$PROD_DB" -c "SELECT * FROM world;"

# Row counts for key tables
psql "$PROD_DB" -c "SELECT 'tenants' AS t, COUNT(*) FROM tenants UNION ALL SELECT 'players', COUNT(*) FROM players UNION ALL SELECT 'ledger', COUNT(*) FROM ledger UNION ALL SELECT 'letters', COUNT(*) FROM letters UNION ALL SELECT 'kills', COUNT(*) FROM kills;"

# Check a table schema
psql "$PROD_DB" -c "\d players"
```

### Copying production DB to local

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:$PATH"
PROD_DB="<external connection string>"
pg_dump "$PROD_DB" --no-owner --no-acl > /tmp/ascent_prod_dump.sql
dropdb ascent_world 2>/dev/null; createdb ascent_world
psql ascent_world < /tmp/ascent_prod_dump.sql
```

## Environment Variables

Set on the `ascent-worldd` service (Dashboard → Environment). Both secrets
are `sync: false` — they live only in the dashboard, never in git.

| Key | Purpose |
|-----|---------|
| `ASCENT_SHARED_SECRET` | HMAC secret shared with the Luna plugin (bootstrap tenant). `openssl rand -hex 32` |
| `ASCENT_ADMIN_KEY` | Protects `/admin/*` (tenant registration). `openssl rand -hex 16` |
| `DATABASE_URL` | Wired automatically from `ascent-world-db` by the blueprint |

If `ASCENT_SHARED_SECRET` is rotated, every Luna install's
`LUNA_ASCENT_SHARED_SECRET` (or vault key
`plugin_linear_ascent.shared_secret`) must be updated in step.

## Deploying

`ascent-worldd` deploys from this repo via the Render blueprint. To deploy:

```bash
git push origin main
```

Check deploy status and logs via the `user-render` MCP or the dashboard
(service → Events / Logs). After every deploy, verify:

```bash
curl -s https://ascent-worldd.onrender.com/health
```

### Manual deploy via browser

1. Navigate to the `ascent-worldd` service in the Render dashboard
2. Click "Manual Deploy"
3. Select branch (usually `main`)

## Running Migrations on Production

Migrations are plain SQL files in `worldd/migrations/`, applied automatically
at startup under the Postgres advisory lock (safe because `numInstances: 1`).
The normal path is therefore: commit the migration, push, let the deploy
apply it.

For a manual/emergency apply:

```bash
export PATH="/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/bin:$PATH"
PROD_DB="<external connection string>"
psql "$PROD_DB" -f worldd/migrations/NNN_migration_name.sql
```

**Always review the migration SQL before running on production**, and follow
the data-preservation rules above — keep old columns/tables until the
migration is verified live.
