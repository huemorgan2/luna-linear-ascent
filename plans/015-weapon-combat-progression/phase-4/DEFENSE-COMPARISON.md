# Follow-up: prepared defense honing

Pre-execution record,13 September2026. The first32-seed all-site experiment is preserved in simulation/verification/009/site-results.json. At floor55,19/32 hunters and20/32 gatherers died; at80,24/32 and20/32 respectively. Tools improve target-material/energy returns but this alone is not sustainable progression.

Root-cause inspection: the prepared weapons already incorporate `economy.reference_hone(floor)` through collection.stats, while prepared armor/shield keep hone0. At floor55 a real trace starts with14,046,820HP, loses8,189,044HP on one tough troll blow, then dies on a failed escape from the next creature. Existing armor honing multiplies both its mitigation and maxHP and is part of the old reference growth table. No evidence yet supports reducing all monsters to compensate for omitted defensive preparation.

Add an explicit optional `--honed` fixture variant using the same canonical reference hone for armor and shield before initial HP is computed. Keep the original un-honed output; run matched32seeds into a different file. Record exact hone counts in every row. All later damage/payments still use actual core and no repair/heal/refill is granted after entry. This is conditional preparedness, not earned investment or affordable natural progress; phase5 must simulate paying for defense honing and compare it with other purchases.

The first family matrix also isolates a single weapon with Ordinary arrows and good shoes. Zero technique advantage cannot disprove Runestring's Arcane niche, Ramguard's bow-switch/escape niche, or Frostbind against faster pursuit. Add only these declared targeted comparisons after inspecting the broad matrix. Do not change engine coefficients on the strength of an experiment that omits its intended tactic.

Rollback: revert the optional experiment parameter; retain both raw result sets. No live-player or engine mutation. Verify a small canary, then the bounded comparison. Source remains0.115.1 during the current browser run.
