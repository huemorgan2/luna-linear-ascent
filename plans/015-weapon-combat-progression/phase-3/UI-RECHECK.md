# Browser corrections after frozen0.114.0

Evidence: `/private/tmp/ascent-phase3-browser/001-phase3/findings.md` and screenshots03–06. The natural web player cleared the first group with no grants:50→82 gold,0→4 XP,80→78 HP and2 energy paid. Reload did not duplicate loot. The browser agent paused at this safe result scene; fresh Luna is in town and BaselineAsh is unchanged.

Correct the observed issues before continuing phase3:

1. Sort owned card payloads by selected deck cell, then grade/family/level/identity for other weapons. JSONB object order must not reorder the displayed deck.
2. Give group buttons their own vertical label/hint layout, remove inherited dot leaders and duplicate numeric brackets, and preserve click/keyboard/plain-number behavior. Forge buttons get explicit keyboard choice numbers.
3. Include every preview member's name/type/reach/stats and pending haul in the plain-text scene consumed by Luna, matching the web card.
4. Replace candidate hunt/deep map chip costs with “1 per enemy” and a free-preview explanation. Candidate meter tooltips must state saved surplus XP and per-enemy/gather energy, and describe the current death policy accurately.
5. Use the existing floor landscape banner at each gathering site; retain place names and the already-authored site text.

No combat, RNG, prices, grants or settlement changes are intended. Verify targeted rendering/core/map/pane tests and full suite follow-up, then restart the same QA launchers preserving state. Resume the same browser evidence run; recheck desktop/390px, a numbered combat reply, and ask Luna to describe the remaining group.

Rollback: this patch changes presentation and ordering only. Revert its recorded plugin commit and re-vendor/restart the same QA processes; preserve all player documents. A source hash change requires a new simulation run/replay comparison before claiming identical recorded output. The underlying0.114.0 group readers stay installed.
