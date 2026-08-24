"""071 — Labs figure3d rides /play from its own folder."""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import uuid

from app import webplay

PW = "probeprobe"
ROOT = pathlib.Path(__file__).resolve().parents[1]
F3D = ROOT / "static" / "site" / "figure3d"


async def _signup(client):
    u = f"Fg{uuid.uuid4().hex[:10]}"
    r = await client.post("/signup", json={"username": u, "password": PW,
                                           "password2": PW})
    assert r.status_code == 200, r.text


async def test_play_loads_figure3d(client):
    await _signup(client)
    r = await client.get("/play")
    assert r.status_code == 200
    html = r.text
    assert f'src="{webplay.FIGURE3D_URL}"' in html
    assert "figure3d/figure3d.js" in html


def test_module_parses_and_stays_decoupled():
    js = (F3D / "figure3d.js").read_text()
    assert 'from "three"' in js
    assert "from \"fight3d\"" not in js and "from 'fight3d'" not in js
    assert "tBayer" in js
    node = shutil.which("node")
    if not node:
        return
    subprocess.run([node, "--check", str(F3D / "figure3d.js")], check=True)


def test_folder_has_player_copies():
    for name in ("human", "elf", "giant"):
        assert (F3D / "models" / "players" / f"{name}.glb").is_file()
    for fam in ("blade", "bow", "staff", "shield", "armor", "boots", "charm"):
        assert (F3D / "models" / "items" / f"{fam}.glb").is_file()
    assert (F3D / "vendor" / "utils" / "BufferGeometryUtils.js").is_file()
