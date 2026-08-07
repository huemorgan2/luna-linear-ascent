"""In-process token buckets (numInstances: 1 — worldd scales up, not out).

One bucket per key: /v1/* keys by tenant (main.py middleware), web play
keys per account as `web:<username>` (webplay.py) so one browser climber
can't starve the shared web tenant for everyone.
"""

from __future__ import annotations

import os
import time

CAPACITY = int(os.environ.get("ASCENT_RATE_CAPACITY", "30"))
REFILL_PER_S = float(os.environ.get("ASCENT_RATE_REFILL", "5"))
_buckets: dict[str, list[float]] = {}  # key -> [tokens, last_ts]


def allow(key: str) -> bool:
    now = time.monotonic()
    tokens, last = _buckets.get(key, (float(CAPACITY), now))
    tokens = min(CAPACITY, tokens + (now - last) * REFILL_PER_S)
    if tokens < 1.0:
        _buckets[key] = [tokens, now]
        return False
    _buckets[key] = [tokens - 1.0, now]
    return True
