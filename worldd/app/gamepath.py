"""Make the game engine importable.

The plugin package (plugin_linear_ascent) is the single source of game
truth. Locally it lives in the sibling submodule; on Render the build
step copies it next to the app (see render.yaml buildCommand).
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CANDIDATES = [
    os.environ.get("ASCENT_GAME_PATH", ""),
    os.path.join(_HERE, "vendor"),                       # render build copy
    os.path.join(os.path.dirname(_HERE), "plugin-linear-ascent"),  # sibling
]


def ensure_game_importable() -> None:
    try:
        import plugin_linear_ascent  # noqa: F401
        return
    except ImportError:
        pass
    for cand in _CANDIDATES:
        if cand and os.path.isdir(
                os.path.join(cand, "plugin_linear_ascent")):
            sys.path.insert(0, cand)
            import plugin_linear_ascent  # noqa: F401
            return
    raise ImportError(
        "plugin_linear_ascent not found; set ASCENT_GAME_PATH")
