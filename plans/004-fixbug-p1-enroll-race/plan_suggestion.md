# P1: ascent_tenants enroll race — 1695 duplicate key violations

## Problem
POST /v1/enroll (worldd/app/main.py:578-616) has a classic TOCTOU race:
1. Two concurrent requests SELECT for the same install_id (line 589-591)
2. Both see no row
3. Both INSERT (line 601-603) — bare INSERT, no ON CONFLICT, no transaction
4. The loser hits the unique constraint (idx_tenants_install or ascent_tenants_pkey)
5. The broad `except Exception` (line 604-612) swallows the error and re-SELECTs

Same defect exists in POST /admin/tenants (line 637-639) — bare INSERT with caller-chosen name.

Production impact: 1,695 ERROR lines in pg logs. Clients don't see failures (the catch re-fetches the winner's credentials), but the log noise is massive and masks real errors.

## Root Cause
- worldd/app/main.py:601-603 — bare `INSERT INTO ascent_tenants (tenant, secret, install_id) VALUES ($1, $2, $3)` via autocommit pool.execute(), no ON CONFLICT
- worldd/app/main.py:637-639 — same pattern for /admin/tenants
- No transaction wrapping the SELECT+INSERT pair
- plugin-linear-ascent auto-enrolls every turn with 30s per-process throttle, creating natural concurrency

## Proposed Fix

### Fix 1: /v1/enroll INSERT (main.py:601-603)
Replace the bare INSERT with:
```sql
INSERT INTO ascent_tenants (tenant, secret, install_id)
VALUES ($1, $2, $3)
ON CONFLICT (install_id) WHERE install_id IS NOT NULL
DO NOTHING
RETURNING tenant, secret
```
Then check if RETURNING gave a row — if not, SELECT the existing row (the winner).
This eliminates the TOCTOU entirely: the INSERT is atomic, the loser gets nothing back, and re-fetches cleanly.

### Fix 2: /admin/tenants INSERT (main.py:637-639)
Replace with:
```sql
INSERT INTO ascent_tenants (tenant, secret)
VALUES ($1, $2)
ON CONFLICT (tenant) DO NOTHING
RETURNING tenant
```
Return 409 only when RETURNING is empty (meaning the name was already taken).

### Fix 3: Tighten the except clause (main.py:604-612)
Replace `except Exception` with `except asyncpg.UniqueViolationError` so unexpected errors aren't swallowed.

## Verification
1. Run test suite: `cd worldd && python -m pytest tests/`
2. Check pg logs after deploy — duplicate key errors for ascent_tenants should drop to zero
3. Concurrent enroll test: fire 10 simultaneous /v1/enroll requests with the same install_id — all should return 200 with the same credentials, zero pg errors

## Rollback
Revert the single commit. The old code is functionally correct (clients never see errors), just noisy.
