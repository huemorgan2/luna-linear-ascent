#!/usr/bin/env python
"""Dojo run 0006 — verify card option clicks act through the 059 bridge.

Loads the QA chat, finds the newest scene card with option buttons,
clicks one, and asserts a new card scene appears WITHOUT typing anything.
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8777"
CHAT = f"{BASE}/chat/41c2349d-7371-4d3b-9ba9-edf8450a83dd"
HERE = Path(__file__).parent
STORAGE = HERE.parent / "0005-xp-economy-2026-07-24" / "storage_state.json"
SHOTS = HERE / "screenshots"


def card_frames(page):
    out = []
    for fr in page.frames:
        if fr == page.main_frame:
            continue
        try:
            if fr.locator("button.opt").count() > 0:
                out.append(fr)
        except Exception:
            continue
    return out


def main() -> None:
    SHOTS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 1600},
            storage_state=str(STORAGE))
        page = ctx.new_page()
        page.goto(CHAT)
        page.wait_for_timeout(4000)
        page.keyboard.press("End")
        page.wait_for_timeout(1000)

        frames = card_frames(page)
        if not frames:
            print("FAIL: no scene card with option buttons found")
            sys.exit(1)
        fr = frames[-1]
        n_frames_before = len(page.frames)
        headline_before = fr.locator(".headline").inner_text(timeout=2000)
        opts = fr.locator("button.opt")
        first_opt = opts.first.inner_text(timeout=2000)
        print(f"before: card '{headline_before}', clicking option: {first_opt!r}")
        page.screenshot(path=str(SHOTS / "01-before-click.png"))

        t0 = time.time()
        opts.first.click()

        # success = a NEW card iframe appears (engine acted, no typing)
        deadline = time.time() + 15
        new_card = None
        while time.time() < deadline:
            page.wait_for_timeout(500)
            if len(page.frames) > n_frames_before:
                cards = card_frames(page)
                if cards and cards[-1] != fr:
                    new_card = cards[-1]
                    break
        elapsed = time.time() - t0
        page.keyboard.press("End")
        page.wait_for_timeout(800)
        page.screenshot(path=str(SHOTS / "02-after-click.png"))

        if new_card is None:
            # maybe the click was refused (stale scene) — hint text tells us
            try:
                hint = fr.locator(".reply").inner_text(timeout=1500)
            except Exception:
                hint = "<no hint>"
            print(f"FAIL: no new card after {elapsed:.1f}s; hint: {hint!r}")
            sys.exit(1)

        headline_after = new_card.locator(".headline").inner_text(timeout=3000)
        print(f"PASS: new card '{headline_after}' appeared {elapsed:.1f}s after click")
        browser.close()


if __name__ == "__main__":
    main()
