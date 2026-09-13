# Legacy baseline walkthrough —13 September2026

Root4e51eb6; plugin1f1b661; engine0.112.0. Isolated QA worldd8860, Luna8898; fresh synthetic player BaselineAsh. An LLM browser runner drove a real Luna conversation. Main agent read the rendered School, Vault, town and hunt-completion screenshots and compared saved server states.

| Scenario | Result | Evidence |
|---|---|---|
| Entry / character creation | PASS after QA tenant enrollment |09/10 screenshots; real game pane |
| Numbered choice | PASS |Bare2 chose Elf; later2 deposited half at Vault |
| Look unchanged | PASS in runner DB comparison |Repeated scene reads; no second transaction |
| School | PASS baseline observation |Existing weapon training and paid slot offers |
| Vault | PASS baseline observation |Actual visit and25 gold deposit; bank25 survives hunt |
| Normal hunt | PASS |Lane wolf; before80HP/0XP/25gold, after75HP/2XP/45gold; encounter cleared |
| Higher-floor/deep/shield-wall/death browser cases | NOT RUN in this bounded baseline |Direct engine and service baseline tests supplement but do not replace these browser scenarios; full candidate cases remain mandatory |

Regressions filed before candidate edits: plain Chat does not automatically reveal the game pane; a19.1s server action committed while Luna timed out and displayed offline; stale web scene IDs are accepted twice. Out-of-order floor3 prompt stayed in intro but Luna selected an intro action rather than attempting an invalid engine call, so it does not prove the refusal contract. These are new-design opening/action-seam acceptance cases, not a claim that the old game is ready to ship.

The baseline is sufficient to pin observed old rules and start candidate schema work. It is not full S01 coverage or a completion claim for the redesign. Raw synthetic snapshots/transcript and additional screenshots remain at /private/tmp/ascent-baseline-browser/001-baseline. Real Vault timing and six-floor finite-energy probes are in plans/015-weapon-combat-progression/phase-1. No production data touched.
