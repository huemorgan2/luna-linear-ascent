"""worldd — shared world service for Linear Ascent.

Scaffold: health check + server time only. The real API lands per
plans/001-worldd/plan.md (auth, players, ledgers, world state, social).
"""

from __future__ import annotations

import datetime as dt
import os

from fastapi import FastAPI

API_VERSION = 1

app = FastAPI(title="ascent-worldd", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {
        "ok": True,
        "api": API_VERSION,
        "server_time": dt.datetime.now(dt.timezone.utc).isoformat(),
        "db": bool(os.environ.get("DATABASE_URL")),
    }
