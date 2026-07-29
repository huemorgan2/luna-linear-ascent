"""022/007 — era reset tooling. DESTRUCTIVE BY DESIGN; dry-run by default.

Wipes every transient ascent_* table and boots the new era; the two
permanent tables (ascent_eras, ascent_reincarnation) and ascent_tenants
survive. NEVER point this at production casually: the real run demands
--execute AND ERA_RESET_CONFIRM=yes in the environment, and the standing
rule is to rehearse against a scratch DB first.

    DATABASE_URL=postgres://... python tools/era_reset.py            # dry run
    DATABASE_URL=... ERA_RESET_CONFIRM=yes python tools/era_reset.py --execute
"""

from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg  # noqa: E402

from app import era  # noqa: E402


async def main() -> int:
    execute = "--execute" in sys.argv[1:]
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL is empty — nothing to reset.")
        return 2
    if execute and os.environ.get("ERA_RESET_CONFIRM") != "yes":
        print("refusing: --execute needs ERA_RESET_CONFIRM=yes in the "
              "environment. Rehearse with a dry run first.")
        return 2

    conn = await asyncpg.connect(url)
    try:
        perm_before = {}
        for t in era.PERMANENT_TABLES + ("ascent_tenants",):
            perm_before[t] = await conn.fetchval(f"SELECT count(*) FROM {t}")
        tx = conn.transaction()
        await tx.start()
        out = await era.era_reset(conn)
        for t, n in perm_before.items():
            after = await conn.fetchval(f"SELECT count(*) FROM {t}")
            assert after == n, f"PERMANENT table {t} changed — aborting"
        if execute:
            await tx.commit()
            print(f"ERA {out['era']} BOOTED. wiped: {out['wiped']}")
        else:
            await tx.rollback()
            print(f"dry run (rolled back). would boot era {out['era']}; "
                  f"would wipe: {out['wiped']}")
        return 0
    finally:
        await conn.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
