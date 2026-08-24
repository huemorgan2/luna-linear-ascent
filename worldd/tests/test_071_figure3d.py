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
    # The pane reveal timer holds the original declarative canvas. Once
    # figure3d replaces it, the live canvas must clear that stale opacity:0
    # state itself.
    assert 'classList.remove("waiting")' in js
    assert 'classList.add("shown")' in js
    # Object3D.add() returns the scene. Chaining position.set() onto it moves
    # every model out of this portrait's narrow orthographic camera.
    assert "const fill = new THREE.DirectionalLight" in js
    assert "scene.add(fill)" in js
    # Every card swap detaches the old portrait. It must release the RAF,
    # render targets, and WebGL context instead of accumulating one complete
    # renderer per selection.
    assert "if (!gl.canvas.isConnected)" in js
    assert "function dropGone()" in js
    assert "dropGone();" in js
    assert "gl.rtColor.dispose()" in js
    assert "gl.rtNormal.dispose()" in js
    assert "gl.renderer.forceContextLoss()" in js
    assert "const reusable = [...lives.entries()]" in js
    assert "scan(game);\n    dropGone();" in js
    assert "const FRAME_MS = 1000 / 15" in js
    assert "document.hidden || rect.bottom <= 0" in js
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
