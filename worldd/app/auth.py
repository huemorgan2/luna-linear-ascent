"""Tenant HMAC auth — signature = HMAC-SHA256(secret, f"{ts}.{body}").

Clock skew ±300s. Constant-time compare. Tenants live in ascent_tenants;
secrets are cached with a short TTL so a revoke lands within a minute.
"""

from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException, Request

from . import db

SKEW_SECONDS = 300
WEB_TENANT = "web"     # 005: reachable only via webplay.py's cookie routes
_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 60.0


async def _tenant_secret(tenant: str) -> str | None:
    hit = _cache.get(tenant)
    if hit and hit[1] > time.time():
        return hit[0]
    pool = await db.get_pool()
    row = await pool.fetchrow(
        "SELECT secret FROM ascent_tenants WHERE tenant=$1 AND NOT disabled",
        tenant)
    if row is None:
        return None
    _cache[tenant] = (row["secret"], time.time() + _CACHE_TTL)
    return row["secret"]


async def verify_tenant(request: Request) -> str:
    tenant = request.headers.get("X-Ascent-Tenant", "")
    ts = request.headers.get("X-Ascent-Ts", "")
    sig = request.headers.get("X-Ascent-Signature", "")
    api = request.headers.get("X-Ascent-Api", "")
    if api != "1":
        raise HTTPException(426, "unsupported api version; expected 1")
    if not tenant or not ts or not sig:
        raise HTTPException(401, "missing auth headers")
    if tenant == WEB_TENANT:
        # 005: the web tenant's secret is never disclosed, so a signature
        # claiming it is a leak being replayed — same answer as no tenant.
        raise HTTPException(401, "unknown tenant")
    try:
        ts_i = int(ts)
    except ValueError:
        raise HTTPException(401, "bad timestamp")
    if abs(time.time() - ts_i) > SKEW_SECONDS:
        raise HTTPException(401, "timestamp out of range")
    secret = await _tenant_secret(tenant)
    if secret is None:
        raise HTTPException(401, "unknown tenant")
    body = await request.body()
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + body,
                        hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(401, "bad signature")
    return tenant
