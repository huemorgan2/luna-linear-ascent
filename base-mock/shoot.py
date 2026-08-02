#!/usr/bin/env python
"""Screenshot the base-mock demo: idle, walking, prompts, loot, talk."""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8999/threejs/"
SHOTS = Path(__file__).parent / "shots"
SHOTS.mkdir(exist_ok=True)


def walk_to(page, x, z, timeout_ms=25000):
    page.evaluate(f"window.mock.walkTo({x}, {z})")
    page.wait_for_function(
        f"Math.hypot(window.mock.pos()[0] - ({x}), window.mock.pos()[1] - ({z})) < 0.3",
        timeout=timeout_ms)
    page.wait_for_timeout(400)


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(URL)
        page.wait_for_function("window.mock && window.mock.ready && window.mock.ready()", timeout=30000)
        page.wait_for_timeout(1200)
        if errors:
            print("PAGE ERRORS:", *[e[:300] for e in errors[:5]], sep="\n  ")
            page.screenshot(path=str(SHOTS / "error.png"))
            sys.exit(1)

        page.screenshot(path=str(SHOTS / "01-idle.png"))

        walk_to(page, 5.6, 8.5)            # vault door (east row)
        page.screenshot(path=str(SHOTS / "03-near-vault.png"))
        print("prompt:", page.locator("#prompt").inner_text())
        page.keyboard.press("1")
        page.wait_for_timeout(500)
        print("toast:", page.locator("#toast").inner_text())

        walk_to(page, -2.6, 12.9)          # sleeper Wex
        page.screenshot(path=str(SHOTS / "05-near-sleeper.png"))
        print("prompt:", page.locator("#prompt").inner_text())
        page.keyboard.press("1")
        page.wait_for_timeout(500)
        page.screenshot(path=str(SHOTS / "06-looted.png"))
        print("toast:", page.locator("#toast").inner_text())
        page.keyboard.press("2")
        page.wait_for_timeout(400)
        print("toast:", page.locator("#toast").inner_text())

        # behind the lodge — enter works from any side
        walk_to(page, -13.4, 9.0)
        page.screenshot(path=str(SHOTS / "06b-behind-lodge.png"))
        print("prompt (behind lodge):", page.locator("#prompt").inner_text())

        # the square: fountain + tower gate
        walk_to(page, 0, -11.6)
        page.screenshot(path=str(SHOTS / "07-square.png"))
        walk_to(page, 0, -17.4)     # tower gate
        page.screenshot(path=str(SHOTS / "08-gate.png"))
        print("prompt:", page.locator("#prompt").inner_text())
        page.keyboard.press("1")
        page.wait_for_timeout(500)
        print("toast:", page.locator("#toast").inner_text())
        browser.close()
        print("done")


if __name__ == "__main__":
    main()
