"""078 Phase 5 — the act benchmark.

Runs the app in-process (ASGI — the full path: auth, injection, engine,
save, render, gzip; only the network hop is out) and fires N mixed acts,
printing p50/p95 latency and payload sizes against the plan's budgets.
Rate limits are raised for the run — the point is server cost per click,
not the limiter.

Usage:  python tools/bench_act.py [player] [acts]
"""

import asyncio
import json
import os
import statistics
import sys
import time

sys.path.insert(0, ".")

os.environ.setdefault(
    "DATABASE_URL", "postgresql://ascent:ascent@localhost:5434/ascent_world")
os.environ["ASCENT_RATE_CAPACITY"] = "1000000"
os.environ.setdefault("ASCENT_SHARED_SECRET", "local-dev-shared-secret")

PLAYER = sys.argv[1] if len(sys.argv) > 1 else "speedprobe1"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 100

# a mixed click diet: menus, the square, the gate, intro steps
OPTIONS = ("town", "square", "town", "gate", "town", "next", "begin")


async def main() -> None:
    from httpx import ASGITransport, AsyncClient

    from app import site
    from app.config import reset_config
    reset_config()
    from app.main import app

    tok = site._session_token(PLAYER)
    lat, sizes = [], []
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=ASGITransport(app=app),
                               base_url="http://bench",
                               cookies={"ascent_session": tok}) as c:
            await c.post("/play/api/act", json={"option": "town"})
            for i in range(N):
                body = {"option": OPTIONS[i % len(OPTIONS)]}
                t0 = time.perf_counter()
                r = await c.post("/play/api/act", json=body)
                lat.append(1000 * (time.perf_counter() - t0))
                r.raise_for_status()
                sizes.append(len(r.content))
    lat.sort()
    p50 = statistics.median(lat)
    p95 = lat[int(0.95 * len(lat)) - 1]
    print(f"acts={N} player={PLAYER}")
    print(f"latency  p50={p50:6.1f}ms  p95={p95:6.1f}ms  "
          f"max={lat[-1]:6.1f}ms   budget: p95 < 80ms local")
    print(f"payload  p50={statistics.median(sizes)/1024:6.1f}KB  "
          f"max={max(sizes)/1024:6.1f}KB   budget: ≤ 30KB")


asyncio.run(main())
