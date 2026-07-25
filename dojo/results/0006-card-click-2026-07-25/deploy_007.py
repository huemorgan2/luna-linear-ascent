#!/usr/bin/env python
"""Production deploy 0.48.007 — plan-033 pipeline via the admin's browser session.

Reuses the (copied) Playwright-MCP Chrome profile, which holds the live
luna.com.ai admin session. Same steps as 056/057 deploys:
snapshot -> build -> wait -> promote -> restore -> report.

Usage: deploy_007.py snapshot|build|wait|promote <image_id>|status|machines
"""

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

VERSION = "0.48.007"
PROFILE = "/tmp/deploy-chrome-profile"
HERE = Path(__file__).parent
SNAP = HERE / "deploy-snapshot.json"


def api(page, path, method="GET"):
    return page.evaluate(
        """async ({path, method}) => {
            const r = await fetch(path, {method, credentials: 'include'});
            const text = await r.text();
            let body; try { body = JSON.parse(text) } catch { body = text.slice(0, 400) }
            return {status: r.status, body};
        }""",
        {"path": path, "method": method},
    )


def main() -> None:
    cmd = sys.argv[1]
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            PROFILE, channel="chrome", headless=True,
            viewport={"width": 1280, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://luna.com.ai/admin", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)

        if cmd == "snapshot":
            r = api(page, "/api/admin/machines")
            if r["status"] != 200:
                print("machines failed:", r["status"], str(r["body"])[:200])
                sys.exit(1)
            snap = [
                {"machine_id": m["machine_id"], "agent_id": m.get("agent_id"),
                 "agent_slug": m["agent_slug"], "fly_state": m["fly_state"],
                 "image_version": m["image_version"]}
                for m in r["body"]
            ]
            SNAP.write_text(json.dumps(snap, indent=2))
            stopped = [m for m in snap if m["fly_state"] in ("stopped", "suspended")]
            print(f"{len(snap)} machines; versions="
                  f"{sorted({m['image_version'] for m in snap})}")
            print(f"pre-stopped ({len(stopped)}):",
                  ", ".join(m["agent_slug"] for m in stopped))
        elif cmd == "build":
            r = api(page, "/api/admin/images/build", "POST")
            print("build:", r["status"], json.dumps(r["body"])[:300])
        elif cmd == "wait":
            t0 = time.time()
            while time.time() - t0 < 40 * 60:
                r = api(page, "/api/admin/images")
                items = r["body"] if isinstance(r["body"], list) else r["body"].get("images", [])
                img = next((i for i in items if i.get("version") == VERSION), None)
                st = img["build_status"] if img else "absent"
                print(time.strftime("%H:%M:%S"), st, flush=True)
                if st == "built":
                    print("image_id:", img["id"])
                    return
                if st in ("failed", "error"):
                    print("BUILD FAILED:", json.dumps(img)[:400])
                    sys.exit(1)
                time.sleep(30)
            sys.exit("timed out")
        elif cmd == "promote":
            image_id = sys.argv[2]
            r = api(page, f"/api/admin/images/{image_id}/promote-main", "POST")
            print("promote:", r["status"], json.dumps(r["body"])[:800])
        elif cmd == "machines":
            r = api(page, "/api/admin/machines")
            now = r["body"]
            versions = sorted({m["image_version"] for m in now})
            print(f"{len(now)} machines; versions={versions}")
            snap = json.loads(SNAP.read_text()) if SNAP.exists() else []
            before = {m["machine_id"]: m for m in snap}
            stragglers = [m for m in now if m["image_version"] != VERSION]
            if stragglers:
                print("stragglers:", ", ".join(
                    f"{m['agent_slug']}={m['image_version']}" for m in stragglers))
            for m in now:
                b = before.get(m["machine_id"])
                if b and b["fly_state"] != m["fly_state"]:
                    print(f"  state {m['agent_slug']}: {b['fly_state']} -> {m['fly_state']}")
            print("ALL ON " + VERSION if not stragglers else "INCOMPLETE")
        elif cmd == "restore":
            snap = json.loads(SNAP.read_text())
            stopped = [m for m in snap if m["fly_state"] in ("stopped", "suspended")]
            for m in stopped:
                r = api(page, f"/api/agents/{m['agent_id']}/stop", "POST")
                print("restore stop", m["agent_slug"], "->", r["status"],
                      json.dumps(r["body"])[:120])
        ctx.close()


if __name__ == "__main__":
    main()
