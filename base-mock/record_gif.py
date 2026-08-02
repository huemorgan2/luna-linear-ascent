#!/usr/bin/env python
"""Record a short walking loop of the base-mock demo into an animated GIF."""

from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

URL = "http://localhost:8999/threejs/"
OUT = Path(__file__).parent / "shots" / "walk.gif"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(URL)
    page.wait_for_function("window.mock && window.mock.ready && window.mock.ready()", timeout=30000)
    page.wait_for_timeout(800)
    cv = page.locator("canvas.game")
    box = cv.bounding_box()

    waypoints = [(0, 5), (0, -6), (3.4, -11), (0, -17.4), (-3.5, -13)]
    frames = []
    wp = iter(waypoints)
    page.evaluate("window.mock.walkTo(%f, %f)" % next(wp))
    for i in range(56):
        # advance to the next waypoint when close
        done = page.evaluate(
            "(() => { const p = window.mock.pos(); return p; })()")
        shot = cv.screenshot()
        import io
        frames.append(Image.open(io.BytesIO(shot)).convert("P",
                      palette=Image.ADAPTIVE, colors=8))
        page.wait_for_timeout(90)
        if i in (12, 26, 38, 48):
            try:
                page.evaluate("window.mock.walkTo(%f, %f)" % next(wp))
            except StopIteration:
                pass
    browser.close()

frames[0].save(OUT, save_all=True, append_images=frames[1:],
               duration=110, loop=0, optimize=True)
print(OUT, OUT.stat().st_size // 1024, "KB,", len(frames), "frames")
