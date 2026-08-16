#!/usr/bin/env python3
"""010 — a 16x16 Google "G" drawn in the game's own inks.

No blue seat exists in the warmed-CGA palette, so Google blue borrows the
cyan-teal energy ink (--en / AETHER). The other three are near-exact:
Google red -> hurt, yellow -> gold, green -> hp.

Output: an <svg> of 1px rects (one per lit pixel), printed as a
data: URI so it can be inlined on the door and in the profile. Rendered
with image-rendering:pixelated it stays crisp when scaled up.
"""
from __future__ import annotations

import math
from urllib.parse import quote

# palette seats (mock.css / render.py) — closest match to the Google logo
BLUE = "#45d0c0"   # --en  (no true blue in the 16; cyan-teal stands in)
RED = "#f26541"    # --hurt
YELLOW = "#f5b825"  # --gold
GREEN = "#8ed24a"   # --hp

W = H = 16
CX = CY = 7.5
INNER = 3.4
OUTER = 7.35


def cell(x: int, y: int) -> str | None:
    dx, dy = x - CX, y - CY
    d = math.hypot(dx, dy)
    # the crossbar: a horizontal blue tongue from the ring's right edge
    # into the centre, sitting on the two middle rows.
    if 7 <= y <= 8 and 7.0 <= x <= 12.0 and d <= OUTER:
        return BLUE
    if d < INNER or d > OUTER:
        return None
    ang = math.degrees(math.atan2(-dy, dx))  # 0=right, 90=up
    # the mouth: the notch above the bar on the right stays empty
    if 3 < ang < 48:
        return None
    if -48 <= ang <= 3:
        return BLUE      # right + lower-right, merging into the bar
    if 48 <= ang < 140:
        return RED       # the top arc
    if ang >= 140 or ang <= -140:
        return YELLOW    # the left arc
    return GREEN         # the bottom arc


def build() -> tuple[str, str]:
    rects = []
    grid = []
    for y in range(H):
        row = []
        for x in range(W):
            c = cell(x, y)
            row.append(c)
            if c:
                rects.append(
                    f'<rect x="{x}" y="{y}" width="1" height="1" fill="{c}"/>')
        grid.append(row)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'shape-rendering="crispEdges">{"".join(rects)}</svg>')
    data = "data:image/svg+xml;charset=utf-8," + quote(svg, safe="")
    # an ascii preview so the shape is reviewable in the terminal
    legend = {BLUE: "B", RED: "R", YELLOW: "Y", GREEN: "G", None: "."}
    art = "\n".join("".join(legend[c] for c in row) for row in grid)
    return data, art


if __name__ == "__main__":
    data_uri, preview = build()
    print(preview)
    print()
    print(data_uri)
