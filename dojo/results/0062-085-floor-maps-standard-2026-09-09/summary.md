# Dojo 0062 — floors 1–10 maps and opaque elevator

Run: 2026-09-09–11. Release candidate: game `0.111.0`.

## Result

PASS locally. The browser database and destructive test-suite database were isolated from each other and from production. No existing player was reset.

| Area | Result | Evidence |
|---|---|---|
| Maps 1–10 | PASS | All ten distinct maps rendered with standard eligibility. Automated live-browser geometry covered 30 views: 760px, 390px, and 320px for each floor. Final result: zero chip overlaps, horizontal overflow, clipped tooltips, or page errors. |
| Actions | PASS | CAMP, keep, and GATE were clicked on every floor in a live browser. NPC and keep cards did not retain the map; floor 10 routed to `Gnarl, the Goblin King fell here`. Floor 11 retained its ordinary menu. |
| Mixed rows and numbers | PASS | At 320px a wounded floor-2 player showed map chips plus stew/heal rows. Displayed `6` opened GATE; displayed `3` healed exactly once. Digits typed into an input remained input. |
| Tooltips and accessibility | PASS | Every visible marker had an immediate hover/focus explanation, accessible description relationship, and viewport-contained tooltip at all tested widths. |
| Elevator | PASS | Ascent, descent, and Roothollow return mounted a viewport-sized `rgb(0,0,0)` overlay with opacity 1 and input inert at mount, first animation frame, and second frame. Keyboard and mouse actions during rides did not mutate state. Input returned after reveal; reload/peek remained quiet. |
| Labs graduation | PASS | Maps rendered with legacy `floormap:false`; the Labs screen no longer listed Floor maps. |
| Luna conversation | PASS | Real turns: `show me floor 2` → `ascent_scene` and the floor-2 map; bare displayed `4` → `ascent_choose` and Tower Gate; `show me the scene` → `ascent_scene` without state mutation. The startup run exposed and fixed a missed iframe auth handshake; the real pane then loaded. |

## Regressions found and fixed

1. Boss and DEEP-HUNT chips overlapped at 320px on dark-forest/cavern floors. Final mobile rows separate deep hunt, gate, camp, town, and hunt; the complete 30-view geometry rerun passed.
2. A generated accessible label leaked the raw bolt marker. It now says `energy`; the no-emoji check passes.
3. Two historical assertions expected floor-1's pre-map art strip. They now verify the standard map on floors 1–10 and the retained art strip on unmapped floor 11.
4. A cached Luna iframe could miss the shell's one-shot load authentication. The pane now asks for auth on startup and retries while tokenless; a live Luna map and three-turn conversation passed.

## Automated checks

- Plugin focused checks: **84 passed**.
- Plugin full suite: **1440 passed, 9 failed, 1 skipped, 1 xfailed**. The same nine failures were reproduced before implementation (combat feel, death relics, no-classes migration scan, arena distance, encounter profile, and three kill-3D checks); this change introduced no new full-suite failure.
- worldd full suite against `ascent_maps_tests`: **223 passed**.
- Source plugin package and vendored worldd package: byte-identical, excluding caches.

Detailed DOM records are in `geometry/geometry.json`, `routes-run.txt`, and `lift-frames-run.txt`. Human-read screenshots and accessibility snapshots are in `screenshots/`; the consolidated phone review is `geometry/phone-maps-contact.png`.

Production deployment and post-deploy checks are recorded in the phase plan after completion.
