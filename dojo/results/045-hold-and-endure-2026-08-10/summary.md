# 045 — hold and endure · production dojo run

- **Date:** 2026-08-10 (run started 2026-08-09 ~21:00 UTC)
- **Environment:** production — worldd `https://ascent-worldd.onrender.com`
  (Render srv-d9ha3csvikkc73ff5rg0, deploy `dep-d9sek2pt0dsc73bihirg`),
  marketplace `https://marketplaces.com.ai/mp/official/`
- **Commits:** plugin `4773e1e` (045 phases 1–4 merged with live 043 line),
  outer vendor `c9c75de`
- **Halves check (scene-vs-render):** `/health` → `"game":"0.59.0"` ✓;
  marketplace index → `plugin-linear-ascent 0.59.0`,
  sha256 `af16be23…a472bd8a` matches the published zip ✓
- **Runner:** LLM agent via HMAC tenant probes (`dojo045_probe.py` /
  `dojo045_probe2.py`, scratchpad — API-level run, no browser, hence no
  screenshots). Throwaway tenants `dojo045-3adcdae7`, `dojo045-e8f17560`;
  characters walked from a fresh enroll through the full intro.

## Scenario: tests/045-hold-and-endure/scenario-1-four-fronts.md

| # | Check | Verdict | Evidence |
|---|-------|---------|----------|
| 1 | Fight card has no scan row | **PASS** | rows `['close_in','stand','run','shield_wall']`; string `scout` absent from the whole scene payload |
| 1b | Medlab shelf has no Scout optics | **PASS** | rows `['buy_medgel','buy_trauma_kit','buy_trollblood_tonic','buy_energy_cell','buy_luck_charm','back']` |
| 2 | Victory card shows the floor's menu | **PASS** | "Goblin straggler falls" → `['hunt','gate','stew','heal','keep','talk','town']` (hurt, so stew/heal present); option_art carries `hunt`/`hunt_deep`/`keep` tiles |
| 3 | Forge cards say DEF **and** END | **PASS** | every guard row: e.g. `pay ◈ 100 · +5 DEF · END 1,083`; 20/20 buy rows with DEF also had END |
| 3b | END priced honestly | **PASS** | same rung: keen 845 < base 1,083 < warded 1,896; costlier rungs endure more (T1 1,083 → T5 19,500 shields) |
| 4 | Pack spare promotes via "Use as shield" | **PASS** | bought Warded Scrapwood Buckler → spare Scrapwood to pack; dispatch `wear_scrapwood_buckler` → "+ Scrapwood Buckler back on — the Warded Scrapwood Buckler goes to your pack"; `/v1/character` gear.shield flipped (state, not just markup) |
| 5 | END falls by damage taken, travels with the piece | **PASS** | after grind: `Scrapwood Buckler (END 1,035/1,083)` — 48 damage-units absorbed; the piece went to pack and came back **still at 1,035/1,083** (durability_pack travel) |

**7/7 PASS.**

## Timing

Full walkthrough (enroll → intro → 20+ fights → two buys → promote →
verify): ~6 minutes wall-clock across the two probe scripts; every
API call answered < 2 s.

## Deviations / notes

- API-level run (HMAC probes), not a browser run: the render half was
  verified through the wire contract (hints, option ids, option_art,
  sheet strings all produced by the 0.59.0 renderer inputs). No
  screenshots for this run.
- Gate-issue (price-0) gear is discarded on replacement by design, so
  the "second shield to pack" step used the warded style at the same
  rung (`buy_warded_scrapwood_buckler`, ◈120) instead of the
  level-locked Plank Shield.
- Usernames are world-unique; probe reruns must use fresh names
  ("DojoFourfront already climbs" refusal observed — correct behavior).
- The victory card also shows `gate` ("Back to the tower gate") for a
  fresh floor-1 character — worldd syncs the shared world frontier into
  `unlocked_floor` (`app/game.py:_sync_frontier_into_doc`), and the
  frontier stands above floor 1, so the row is legitimate.

## Regressions

None found.
