"""078 Phase 5 — seed N synthetic playing players for the scale proof.

Usage:
    python tools/seed_scale.py 10000            # seed up to N
    python tools/seed_scale.py clean            # remove every seeded row

Hard guard: refuses any DATABASE_URL that is not localhost/127.0.0.1 —
this script must never touch production. All rows land under tenant
'seed' with player keys 'seed_<i>' so cleanup is one tenant-scoped
DELETE and no real player can collide.
"""

import asyncio
import datetime as dt
import json
import os
import random
import sys

import asyncpg

DB = os.environ.get(
    "DATABASE_URL", "postgresql://ascent:ascent@localhost:5434/ascent_world")

RACES = ("human", "elf", "dwarf", "orc", "gnome")
CLASSES = ("warrior", "ranger", "mage", "rogue")
LOCATIONS = ("town", "gate_town", "gate_town", "warden_keep", "lodge",
             "shop", "square")
GUILDS = ("", "", "", "Oakline", "Emberfall", "The Quiet Hand")


def _doc(i: int, rng: random.Random) -> dict:
    level = max(1, min(60, int(rng.gauss(12, 9))))
    floor = max(1, min(40, int(rng.gauss(max(1, level // 2), 4))))
    d = {
        "stage": "playing",
        "name": f"Seed{i}",
        "luna_user": f"seed:seed_{i}",
        "race": rng.choice(RACES),
        "clazz": rng.choice(CLASSES),
        "level": level,
        "xp": rng.randint(0, 500),
        "hp": rng.randint(20, 400),
        "gold": rng.randint(0, 5000),
        "bank": rng.randint(0, 100_000),
        "floor": floor,
        "unlocked_floor": max(floor, min(40, floor + rng.randint(0, 3))),
        "location": rng.choice(LOCATIONS),
        "gear": {"weapon": "rusted_sword"} if rng.random() < 0.8 else {},
        "inventory": {"trollblood_tonic": rng.randint(0, 3)},
        "training": {}, "mastery": {},
        "energy_val": rng.randint(0, 20),
        "energy_ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "rng_counter": 0,
    }
    if rng.random() < 0.12:
        d["sleeping"] = {"where": "lodge"}
        d["location"] = "sleeping"
    if rng.random() < 0.10:
        d["lodged_until_day"] = 10_000_000
    if rng.random() < 0.5:
        d["guild"] = rng.choice(GUILDS)
    # realistic weight: real docs carry their last scene (~6-8 KB)
    d["scene"] = {
        "eyebrow": "FLOOR %d · SEEDED" % floor,
        "headline": "A synthetic scene for the scale proof",
        "body_lines": ["x" * 70] * 40,
        "options": [{"id": f"opt{k}", "label": "y" * 30}
                    for k in range(12)],
    }
    return d


async def main() -> None:
    if "localhost" not in DB and "127.0.0.1" not in DB:
        sys.exit("refusing: DATABASE_URL is not local — never seed prod")
    arg = sys.argv[1] if len(sys.argv) > 1 else "10000"
    conn = await asyncpg.connect(DB)
    try:
        if arg == "clean":
            n = await conn.execute(
                "DELETE FROM ascent_players WHERE tenant='seed'")
            print("cleaned:", n)
            return
        target = int(arg)
        await conn.execute(
            "INSERT INTO ascent_tenants (tenant, secret) "
            "VALUES ('seed', 'seed') ON CONFLICT (tenant) DO NOTHING")
        have = int(await conn.fetchval(
            "SELECT count(*) FROM ascent_players WHERE tenant='seed'") or 0)
        rng = random.Random(78)
        now = dt.datetime.now(dt.timezone.utc)
        batch = []
        for i in range(have, target):
            # updated_at spread: 30% acted today (some minutes ago — the
            # presence tiers see them), the rest across a month
            r = rng.random()
            if r < 0.05:
                age = dt.timedelta(minutes=rng.randint(0, 59))
            elif r < 0.30:
                age = dt.timedelta(hours=rng.randint(1, 23))
            else:
                age = dt.timedelta(days=rng.randint(1, 30))
            batch.append((f"seed_{i}", json.dumps(_doc(i, rng)),
                          now - age))
            if len(batch) >= 500:
                await conn.executemany(
                    "INSERT INTO ascent_players (tenant, player, doc,"
                    " updated_at) VALUES ('seed', $1, $2, $3) "
                    "ON CONFLICT DO NOTHING", batch)
                batch = []
                print(f"  {i + 1}/{target}", flush=True)
        if batch:
            await conn.executemany(
                "INSERT INTO ascent_players (tenant, player, doc,"
                " updated_at) VALUES ('seed', $1, $2, $3) "
                "ON CONFLICT DO NOTHING", batch)
        total = await conn.fetchval(
            "SELECT count(*) FROM ascent_players WHERE stage='playing'")
        print("seeded; playing players now:", total)
    finally:
        await conn.close()


asyncio.run(main())
