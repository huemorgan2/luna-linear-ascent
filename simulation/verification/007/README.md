# Material-bundle correction — phase3 candidate

Actual-engine experiments,13 September2026. Earlier0.114.0 results remain in006.

- `bundles-only-opening.json`:0.114.4/c062bee;8players,10days,maxfloor10,seed31001. Three reach10, five reach9, six reach8; populationmedian readyfloor9. Compare006: zero reached10 and two reached9. This small sample does not establish a strong-policy curve or a100-floor outcome.
- `opening-run.json`:0.114.5/e029396 engine content, same settings. Exact progression milestones,counters,timelines and owned state match0.114.4; stored scene payloads differ because they now disclose reach and gathering routes. Source/semantic hashes remain separate. `replays.json` records exact re-execution of both captured complete action traces.
- `first-ten-30-days.json`:0.114.4,30days, same8players; full traces omitted in this compact archive. Six careful players reach10 in7.00–15.34days; two learners do not. Earlier006 careful arrivals were13.00–19.67days. The strong-policy target for10 is1.5875days: still missed.
- `gathering-returns.json`:64 explicit prepared floor3 fixtures per route, actual core actions, no free healing/wait/upgrade. FullHP,level3,rank3starters,20energy,300gold; tools paid from declared fixturegold. Wood site secured1.159Wood/energy versus hunting0.435 (2.666×); metal0.944RawMetal/energy versus0.528 (1.787×). Ambush energy and abandoned hauls count. No deaths in these prepared fixtures. Mean netgold hunting+384.33,wood−1.67,metal−18.97; tools were newly purchased each trial. This is conditional route efficiency, not natural onboarding or amortized long-term ROI.

Reproduce the route experiment using `ASCENT_GAME_PATH=/path/to/plugin-parent python simulation/verification/007/gathering_probe.py`. It imports the same game package and never resolves damage/rewards itself. Runs write complete results to /private/tmp/ascent-phase3-gathering-returns.json. Reproduce swarm from configs/collection-opening-smoke.json and the recordedsource. Current-source runs may differ after future game changes; replay verifies the source hash before any claim of equivalence.

Remaining: natural first-upgrade browser proof, further policy/investment/curve tuning, all100floors and genuine shared-warden services. No extrapolated points or pretend multiplayer results.
