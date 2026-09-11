# Dojo 0063 — floor-2 contrast preservation

Date: 2026-09-11  
Source parent: `2f6fde7`  
Source plugin: `c9877ae`  
Stack: isolated worldd at `127.0.0.1:8610`, isolated QA Luna at `127.0.0.1:8800`, Chrome, disposable local databases

| Scenario | Result | Evidence |
|---|---|---|
| Desktop floor 2 | PASS | Correct 0.111.1 versioned asset loaded; lakes and central shadow read darker than lit ridges; tower, fortress, roofs, quarry, roads, and rails remain legible. |
| Marker wiring | PASS | HUNT, RUSTMAW, CAMP, GATE, and ROOTHOLLOW were present. Standalone keyboard `6` moved to the gate and `2` returned to floor 2. |
| Narrow layout | PASS | Chrome was narrowed to the mobile navigation layout. The full map scaled into the pane and all five chips remained readable without clipping. |
| Real Luna scene | PASS | A real multi-turn Claude Sonnet 4.5 conversation called `ascent_scene`; the pane rendered floor 2 and Luna described Lampfall without free-forming state. |
| Plain-text option | PASS | Sending bare `6` called `ascent_choose · 6`; the pane and Luna both showed the tower gate. |
| Server truth | PASS | Read-only scene retained floor 2, `gate_town`, and 24/25 energy. The intended GATE action changed the location; no energy was spent. |
| Static bytes | PASS | Local versioned HTTP response and packaged image both hash to `d5d46a03cc436ae3bbf7cd0365903b62a851529c9ee69ff0b05621d38b888f9e`. |

The first two Luna attempts happened before the isolated tenant was enrolled and correctly surfaced the unavailable-world response. After enrolling the test tenant and restarting worldd, the required clean read-only turn and number-action turn passed. This was test setup, not a product regression.

Regressions found: none.  
Out-of-world or free-formed-state moments in the clean verification turns: none.  
Recommendation: deploy `0.111.1`.
