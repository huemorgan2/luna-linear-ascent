# worldd execution — Phase 5: Hardening + Render deploy

Parent: [plans/001-worldd](../../001-worldd/plan.md) phase 5, plus the production deploy.

## Goal

Production-ready and LIVE on Render (starter plan, always-on, ~$7/mo web + starter Postgres).

## Deliverables

- Per-tenant rate limits (simple token bucket in-process — `numInstances: 1` makes this safe)
- Ledger audit endpoint: `GET /admin/ledger?player=` (admin-key guarded)
- Request logging (structured, one line per request: tenant, path, status, ms)
- `X-Ascent-Api` version check enforced (reject mismatched clients with a clear error)
- **Render deploy**: push repo to GitHub → Render → New → Blueprint → pick repo (reads root `render.yaml`: `ascent-worldd` web starter + `ascent-world-db` Postgres starter, oregon) → set `ASCENT_SHARED_SECRET` + `ASCENT_ADMIN_KEY` in the dashboard (sync:false) → deploy → `GET https://ascent-worldd.onrender.com/health` green
- Register the production bootstrap tenant; point the local plugin at production and play one real fight through the deployed service

## Deploy procedure (browser)

1. Ensure repo pushed to GitHub with latest worldd.
2. Render dashboard (browser): New → Blueprint → select the `luna-linear-ascent` repo → apply. Confirm plan shows **Starter ($7/mo)** for the web service before applying.
3. Environment tab: set the two secrets. `DATABASE_URL` is wired by the blueprint.
4. Watch deploy logs to "Application startup complete"; migrations apply at boot.
5. Browser check of `/health`; then signed smoke calls from local.

## Exit gate

Production `/health` shows `ok: true, db: true`; a fight action played from a local Luna against production lands a ledger row in the production DB; secrets absent from git.
