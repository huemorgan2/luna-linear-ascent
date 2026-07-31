"""Every module that reaches for the engine must put it on the path itself.

`app/social.py` used to borrow the path from whichever sibling happened to be
imported first. main.py imports the game modules lazily, inside endpoints, so a
freshly booted worldd that was asked for /v1/presence before its first scene
raised ModuleNotFoundError and answered 500 until something else warmed the
import. A subprocess is the only honest test: the pytest session has already
imported half the app.
"""

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_GAME_MODULES = ("social", "game", "factions", "armory", "era")


def _imports_alone(mod: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", f"import app.{mod}"],
        cwd=_ROOT, capture_output=True, text=True, timeout=120)


def test_each_game_module_imports_on_its_own():
    for mod in _GAME_MODULES:
        r = _imports_alone(mod)
        assert r.returncode == 0, f"app.{mod} alone: {r.stderr[-800:]}"
