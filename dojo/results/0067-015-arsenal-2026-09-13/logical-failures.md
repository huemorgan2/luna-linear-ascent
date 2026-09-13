# Logical failures — phase4 browser002

All failures were reported when discovered. No source changes or quiet replacements of earlier evidence were made.

## P4-002 — partial discovery; exact-query gate FAIL

At 2026-09-13 10:46:59 UTC, in preserved conversation60d7a0a6-1771-4b5e-a105-3d9364325c7f, the first query was exactly `show me the arrows I can use with this bow`.

Observed two `read` calls at10:47:03 and10:47:07 against old `result:toolu_016A1G6nBBpWtAf7cnAmrYd2`; zero `ascent_*` calls. Final reply10:47:12 recognizes Ordinary100/capacity400 but says “The quiver shows no other arrow types available yet.” This is partial improvement over0.115.0's blanket denial, not a total failure to recognize arrows. Current0.115.1 has six arrow definitions. The old result lacks that current payload. Screenshot02 is the completed answer; screenshot01 is its intermediate streaming state.

Fresh-data recovery was a separate turn, not a replacement result: `ascent_character`, `ascent_scene`, then `read` of the new character result correctly produced all six Common payloads, stock, effects, and5/10/10/15/10/15 gold bundle prices. Screenshot03. The exact first-query gate remains FAIL. Earlier P4-001 remains in the root plan.

## P4-003 — FAIL: unsupported future energy claim

The floor1 preview reply said `Energy: 5/25 (will be 6 when first action begins)`. The actual start spends one energy per enemy; the completed two-enemy group spent2, leaving3. There was no grant. Screenshot06 retains this prose and the bounded combat instruction. This is a Luna explanation error; no engine energy defect was observed.

## P4-004 — FAIL: explicit action caps exceeded in two turns

Recurrence of existing P3-008, owned by plan phase7. This run adds evidence to that issue; it is not a newly introduced engine regression. Main identifies the required remedy as a deterministic tool-call guard, not additional prose coaching. This role made no fix.

Preview instruction: “Take at most four game actions total, then stop and show the roster, HP, and energy.” Observed FIVE `ascent_choose` calls: `9 → 17 → 1 → 1 → 1`. The fifth opens the preview. This additional instance was found during the final message audit and immediately reported.

Combat instruction: “Take at most four game actions this turn … If unfinished after four actions, preserve the battle and stop.” Observed FIVE `ascent_choose` calls: `3 → 2 → 2 → 2 → 2`, at10:49:57.425,10:50:00.456,10:50:03.491,10:50:06.533,10:50:09.595 UTC. The fifth cleared the group. Screenshot06; exact instruction, arguments, timestamps and result excerpts in `luna-turn-actions.json` and `luna-allowlisted-messages.json`.

Only one group was fought, as authorized. Outcome: gold8→43, XP13→17, HP58 unchanged, energy5→3, Hawkeye condition1304→1299. Its preserved pre-phase4 group reader correctly retained arrowless legacy behavior: Ordinary100 unchanged. No state was restored or reset.

Mitigation for the remainder was explicit one-action prompts. All NINE such turns made exactly one `ascent_choose` call. They bought one Arcane20 bundle and returned to floor1 camp. Main then ordered no additional natural choices; no natural preview or Arcane selection was submitted afterward.

## Environment and usability observations

- Luna is the existing basic debug chat. It renders prose but shows `Not supported in basic chat` instead of game cards/tool results. No UI plugin was installed or reconfigured. Real game-card visual checks used the authorized /play fixtures.
- Poison/burn tick logs use generic channel/damage lines. Source identity and poison kill attribution are proven in the saved authoritative state, not exposed by the prose log alone.
- Mobile390px keeps all six payload controls in a3×2 grid. Concussive wraps across lines; it remains visible and actionable. No horizontal page overflow was observed in the reviewed shots.
- One driver call timed out waiting for Playwright to click an aria-disabled control. It made no game action. Browser driver was recovered; later physical mouse clicks on the visible gray controls exercised actual engine refusals. No service restart or state rollback occurred.
