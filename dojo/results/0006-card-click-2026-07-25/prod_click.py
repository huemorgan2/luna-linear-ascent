#!/usr/bin/env python
"""Verify card clicks act on production (Cortana, luna.com.ai) after 0.48.007."""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CHAT = "https://luna.com.ai/a/vaselin-gamer/chat/49132e68-e7fa-475c-8276-5f1fcce4bde8"
PROFILE = "/tmp/deploy-chrome-profile"
SHOTS = Path(__file__).parent / "screenshots"


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
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, channel="chrome", headless=True,
            viewport={"width": 1280, "height": 1600})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(CHAT, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        page.keyboard.press("End")
        page.wait_for_timeout(1500)

        frames = card_frames(page)
        if not frames:
            print("no card with options visible in prod chat")
            page.screenshot(path=str(SHOTS / "prod-00-no-card.png"))
            sys.exit(1)
        fr = frames[-1]
        n_before = len(page.frames)
        opts = fr.locator("button.opt")
        labels = [opts.nth(i).inner_text() for i in range(opts.count())]
        # prefer a harmless option: back/square/town if present, else the first
        pick = 0
        for i, lb in enumerate(labels):
            if any(w in lb.lower() for w in ("back", "square", "town")):
                pick = i
                break
        print("options:", [lb.replace("\n", " / ") for lb in labels])
        print("clicking:", labels[pick].replace("\n", " / "))
        page.screenshot(path=str(SHOTS / "prod-01-before.png"))
        t0 = time.time()
        opts.nth(pick).click()

        deadline = time.time() + 15
        new_card = None
        while time.time() < deadline:
            page.wait_for_timeout(500)
            if len(page.frames) > n_before:
                cards = card_frames(page)
                if cards and cards[-1] != fr:
                    new_card = cards[-1]
                    break
        elapsed = time.time() - t0
        page.keyboard.press("End")
        page.wait_for_timeout(1000)
        page.screenshot(path=str(SHOTS / "prod-02-after.png"))
        if new_card is None:
            try:
                hint = fr.locator(".reply").inner_text(timeout=1500)
            except Exception:
                hint = "<none>"
            print(f"FAIL: no new card after {elapsed:.1f}s; hint {hint!r}")
            sys.exit(1)
        headline = new_card.locator(".headline").inner_text(timeout=3000)
        print(f"PASS: production click -> new card '{headline}' in {elapsed:.1f}s")
        ctx.close()


if __name__ == "__main__":
    main()
