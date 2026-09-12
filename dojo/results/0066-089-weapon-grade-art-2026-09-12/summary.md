# 0066 — distinct weapon grade artwork

Date: 12 September 2026. Plan: `worldd/plans/089-game-wiki/phase-3-grade-art/PLAN.md`. Baseline7063488; plan committed first as1efa8b8. Environment: isolated wiki checkout, game0.112.0, local public wiki at127.0.0.1:8609; isolated Postgres16 on55442 for coded tests. This is a public website walkthrough; no Luna combat action was changed or claimed tested.

First user action: open `/wiki#arsenal` and switch Common/Rare/Epic/Legendary. Executed through the real in-app browser. The LLM inspected screenshots and DOM output.

| Scenario14 check | Result | Evidence |
|---|---|---|
| Arsenal changes drawings for all families | PASS | Clicked all four grade controls; each rendered16 separate URLs,64 unique across grades. |
| Four-grade comparison | PASS | Opened Thunder Maul, Ramguard Sword, Runestring Bow and Ember Staff. Screenshots show different monochrome constructions, not recolors. |
| Source row → correct detail grade | PASS | Rare Runestring and Epic Ember rows opened matching selected portraits and settings. |
| Gallery selection updates details | PASS | Ember selected through all four grades; portrait and selected tile URLs agree. Legendary Ramguard preserved focus and shows shop+6/full, drop+0/10%. |
| Detail → Forge consistency | PASS | Legendary Ramguard's Forge and acquisition row both resolve Dawnbreaker; screenshot confirms portrait and Legendary frame. |
| Phone390×844 | PASS | Two152px columns, four loaded80px-wide portraits,16px labels. Selected Epic card visible at y251–593. Page width390; dialog scroll/client width350/350. No horizontal overflow. Viewport reset afterward. |
| Console | PASS | No browser errors. |
| Asset/progression integrity | PASS | All64 PNG routes200;64 unique files/content hashes and64 distinct normalized alpha silhouettes. All prior generated data matches after excluding only revision/art fields. |
| Coded checks | PASS | Four targeted Python tests, six Node tests; full worldd suite224 passed in86.61s. Generator check and JS syntax check passed. |

Screenshots are the inline CUA captures in this task: maul comparison, sword comparison, Legendary arsenal, Legendary Ramguard Forge, Runestring comparison, Ember comparison and mobile Epic/Legendary cards. The browser API returns images in the task rather than local screenshot files; no nonexistent file paths are claimed. Original new sprites and prompts are versioned in the implementation.

Regressions: none found.

## Publication verification

Implementation4e052b1 published to main and explicitly deployed as dep-dail93bm8hqs73db2qb0, live2026-09-12T13:37:07Z. Public linearascent.net browser verified revision089.3, all four loaded maul designs, Legendary selection/source agreement and no console errors. Render origin returned64 distinct PNGs and data.json exactly equal to the checked-in bundle (SHA2562214560346aa9cd8497def472cf73c165681c44bd660282ca85ba5be5be58e38). Health ok:true,db:true,game0.112.0. Complete. Roll back this visual update with `git revert 4e052b1`, push and explicit Render deployment.
