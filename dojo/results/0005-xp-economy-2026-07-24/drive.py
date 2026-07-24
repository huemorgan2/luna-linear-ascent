#!/usr/bin/env python
"""Dojo driver for run 0005 — controlled Chromium against the QA Luna.

Usage:
  drive.py login
  drive.py send "<message>" <shot-name> [wait-seconds]
  drive.py shot <shot-name>          # screenshot current chat state
  drive.py read                      # dump visible chat + last card text

Each invocation opens a fresh headless Chromium with the saved auth
storage; chat state lives server-side so this is safe between steps.
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8777"
CHAT = f"{BASE}/chat/41c2349d-7371-4d3b-9ba9-edf8450a83dd"
HERE = Path(__file__).parent
STORAGE = HERE / "storage_state.json"
SHOTS = HERE / "screenshots"


def _dump_state(page) -> str:
    """Text of the main chat column plus every card iframe, last 3500 chars."""
    parts = []
    try:
        parts.append(page.locator("main, body").last.inner_text(timeout=3000))
    except Exception:
        pass
    for fr in page.frames:
        if fr == page.main_frame:
            continue
        try:
            t = fr.locator("body").inner_text(timeout=1500)
            if t.strip():
                parts.append("── card ──\n" + t)
        except Exception:
            continue
    return "\n".join(parts)[-3500:]


def main() -> None:
    cmd = sys.argv[1]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx_kw = {"viewport": {"width": 1280, "height": 1600}}
        if STORAGE.exists() and cmd != "login":
            ctx_kw["storage_state"] = str(STORAGE)
        ctx = browser.new_context(**ctx_kw)
        page = ctx.new_page()

        if cmd == "login":
            page.goto(BASE)
            page.get_by_role("textbox", name="Username").fill("roy")
            page.get_by_role("textbox", name="Password").fill("qa-ascent-006")
            page.get_by_role("button", name="Sign in").click()
            page.wait_for_url("**/*", timeout=10000)
            page.wait_for_timeout(2000)
            ctx.storage_state(path=str(STORAGE))
            print("logged in, storage saved")
            return

        page.goto(CHAT)
        page.wait_for_timeout(3000)

        if cmd == "send":
            msg, shot = sys.argv[2], sys.argv[3]
            wait_s = int(sys.argv[4]) if len(sys.argv) > 4 else 30
            before = _dump_state(page)
            tb = page.get_by_role("textbox", name=lambda n: True) \
                if False else page.locator("textarea, input[placeholder*='Message']").first
            tb.fill(msg)
            tb.press("Enter")
            # wait until the reply settles: poll for growth then quiet period
            deadline = time.time() + wait_s
            last, stable = "", 0
            while time.time() < deadline:
                time.sleep(3)
                cur = _dump_state(page)
                if cur == last and cur != before:
                    stable += 1
                    if stable >= 2:
                        break
                else:
                    stable = 0
                last = cur
            page.wait_for_timeout(1000)
            SHOTS.mkdir(exist_ok=True)
            page.screenshot(path=str(SHOTS / f"{shot}.png"), full_page=False)
            page.keyboard.press("End")
            print(_dump_state(page))
        elif cmd == "shot":
            shot = sys.argv[2]
            SHOTS.mkdir(exist_ok=True)
            page.screenshot(path=str(SHOTS / f"{shot}.png"), full_page=False)
            print(_dump_state(page))
        elif cmd == "read":
            print(_dump_state(page))
        browser.close()


if __name__ == "__main__":
    main()
