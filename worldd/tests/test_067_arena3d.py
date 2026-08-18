"""067 — the arena's 3D layer rides /play next to the kill finisher.

fight3d.js is loaded ONCE: the import map's "fight3d" entry and the
script tag share one URL, so arena3d.js (which imports "fight3d") gets
the same module instance — one kill observer, one asset cache. Both
modules must parse (node --check).
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import uuid

from app import webplay

PW = "probeprobe"
ROOT = pathlib.Path(__file__).resolve().parents[1]
F3D = ROOT / "static" / "site" / "fight3d"


async def _signup(client):
    u = f"Ar{uuid.uuid4().hex[:10]}"
    r = await client.post("/signup", json={"username": u, "password": PW,
                                           "password2": PW})
    assert r.status_code == 200, r.text


async def test_play_loads_fight3d_once_and_arena3d(client):
    await _signup(client)
    r = await client.get("/play")
    assert r.status_code == 200
    html = r.text
    assert html.count(webplay.FIGHT3D_URL) == 2          # map entry + tag
    assert f'"fight3d":"{webplay.FIGHT3D_URL}"' in html
    assert f'src="{webplay.FIGHT3D_URL}"' in html
    assert f'src="{webplay.ARENA3D_URL}"' in html
    assert html.index('"fight3d":') < html.index(f'src="{webplay.ARENA3D_URL}"')


def test_modules_parse_and_arena_imports_fight3d():
    arena = (F3D / "arena3d.js").read_text()
    assert 'from "fight3d"' in arena
    assert "backgrounds300" in arena
    fight = (F3D / "fight3d.js").read_text()
    for name in ("createStage", "renderFrame", "ensureFor", "buildPlayer",
                 "tripoMonster", "burst", "banishFx", "arrowFx", "magicFx",
                 "MONSTERS3D", "STRIKES", "PLAYER_YAW"):
        assert name in fight.split("export {", 1)[1]
    node = shutil.which("node")
    if not node:
        return
    for f in ("fight3d.js", "arena3d.js"):
        subprocess.run([node, "--check", str(F3D / f)], check=True)
