# Dojo 0064 — all-floor contrast and exact map points

Date: 2026-09-11

Source parent: `3ace69f` plus release changes

Source plugin: `92c86b6f`

Stack: isolated worldd at `127.0.0.1:8610`, isolated QA Luna at `127.0.0.1:8800`, Chrome, disposable local databases

| Scenario | Result | Evidence read from Chrome |
|---|---|---|
| Floor 3 | PASS | Drowned Pasture water/ground/forest bands remain distinct; all five chips terminate in a visible gold point with stepped black edge. |
| Floor 4 | PASS | Lightless Glade preserves the deep forest mass against the lit tower clearing; six dots remain visible across bright and dark terrain. |
| Floor 7 | PASS | Orchard blocks, road grid, forest, and open ground separate clearly; edge and center markers point to their configured sites. |
| Floor 10 | PASS | Kingsfield's dark forest, lighter ridges, roads, town, tower, and keep remain legible; all six marker points are visible. |
| Narrow pane | PASS | At a 245px game-pane width the floor-10 map scales pixelated, all six chips remain inside the image, and each point remains attached. |
| Plain-number route | PASS | Sending bare `7` from the floor-10 camp called `ascent_choose · 7` and rendered the Tower Gate. |
| Real Luna continuity | PASS | Luna used `ascent_choose` to travel from the gate to floor 3 after confirmation; it did not invent a state change. |
| Server truth | PASS | Player row reported floor 3/camp after the tool action; the later bare-number action reported the gate with 24/25 energy unchanged. |

The first request for a floor-3 map was made from the Tower Gate. Luna described the camp/map relationship and asked before changing floors; after the player confirmed, it used game actions and rendered Weirsend. This was a conservative travel confirmation, with no free-formed state.

Static verification: all ten assets are 492×369 RGBA, opaque, and exactly black plus `(217,217,211)`. Floors 1 and 2 kept their approved SHA-256 values. Floors 3–10 match the recorded preserve-source candidates. Focused plugin tests passed 61/61; the plugin full suite passed 1,461 with the same nine unrelated baseline failures; the vendored worldd suite passed 220/220.

Regressions found: none.

Out-of-world or free-formed-state moments: none.

Recommendation: release 0.112.0.
