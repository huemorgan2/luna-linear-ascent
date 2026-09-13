# Prepared weapon and gathering measurements

13 September2026. Pre-execution extension to phase4; source56e1d86/0.115.1 is frozen for browser QA. These are explicitly prepared combat fixtures, not natural progression or a replacement damage model.

## Questions and method

1. For each of16 families, compare using its actual technique with direct strikes on the same real two-creature roster and random seed. Cover real Common/Power/Magic Ground/Air profiles, Contact/Cover openings, and representative grade regions. Use canonical weapon stats, grade0–20 mapping, equal prepared character levels/ranks, affordable-floor canonical armor/shield/shoes and finite arrows. The real core consumes energy, ammo, wear and settles every fight. Record whole-group wins, HP lost, actions, effects and ammunition; immunity and inability to reach are meaningful failures, not exceptions to hide. A useful niche can be better damage, survival, control/escape or cheaper supply, not necessarily the greatest raw attack.
2. Extend the existing floor3 route experiment to all8sites. Matched seeds and equal same-floor prepared decks/defenses/HP/20energy; site tools are bought from declared fixture gold. Compare normal hunting with gathering, including ambush energy, failed groups and forfeited haul. Extract explicitly after six attempts or low resources. No free healing/reload/wait. Report secured target material per charged energy, netgold including tool purchase, deaths and actions. An early site can collect next-grade materials before that weapon grade is available; preserve this distinction.
3. Preserve every raw row, exact fixture settings and engine/runner source hashes under simulation/verification/009. Reject any mixed-source run. Preparation code may arrange initial owned state only; all actions and outcomes go through GameSession/core. This experiment is bounded and deterministic; no LLM decisions.

## Late-site browser fixture

Create a separate empty QA world database `ascent_change_phase4_sites` on owned PostgreSQL17 port5433 only if absent, serve matching vendor on free8862. Declare frontier80 in this separate world and create one NEW web player with prepared late-floor gear/gold/energy. Never raise the natural world's frontier3. Enter a named site, buy its tool, gather, handle any encountered group and extract through actual browser controls. Capture UI, before/after state and payment/haul receipts. Do not overwrite a fixture that already exists. Reuse recovered private QA signing configuration without publishing it.

## Verification and rollback

Implement scripts `simulation/verification/009/weapon_niches.py` and `site_returns.py`; document exact CLI/config in their README before running. Inspect their fixture/action boundary, run a small canary, then the full bounded matrix. Confirm deterministic repeats and no mutated natural database state. Browser scenarioS07 remains required; experiment output alone does not close it.

Rollback removes or reverts only experiment code and stops the newly recorded8862PID. Retain all output, the late-site database, its earned fixture state, snapshots and receipts. No production writes. Runtime changes arising from a measured failure require a separate recorded cause/change/verification before implementation. Current engine and other browser fixtures stay frozen.

Execution: planned; no measurements or late-site database created yet.
