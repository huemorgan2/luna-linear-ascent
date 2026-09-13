# Phase3 observations — provisional, not a balance approval

The initial candidate smoke run used the actual plugin source via `ASCENT_GAME_PATH`, not the older vendored package. Engine hash `7dbf142d42f14fd35392b183aa0367f0b9d8bd4d5bee2a83f46f8a088d9f1e64`; the uncommitted package still reported0.113.5, so the hash (not that stale version label) identifies the experiment. The candidate release will bump its version before browser deployment.

One two-day tactician trace reproduced its final state exactly (`e01a2f7acc4ad0f9d73e1fd3b4398d106bf17cf130d6ada5cd834f83e341bd9a`). It cleared20 groups/57 enemies, spent63 enemy energy charges, earned1345 gold/691 XP, and suffered5 deaths. It first qualified for floor5 at day0.334. This did not prove that farming floor5 was sustainable; health spending drained the route.

The eight-player/10-day run `20260913T063105Z-1137277a` used4 CPU workers, seed31001 and four policies (two each),4 readiness trials and a staged personal-readiness frontier. It took27.1957 seconds. Two learners qualified for floor6; the six other players qualified for floor8 by day4.000–8.668. Stronger policies completed actual gathering and6–12 Forge upgrades. Those observations are too slow for the intended target and too small to establish a population curve. No shared warden win or real-world demographic claim follows from this experiment.

The run also exposed an agent bug: with two energy, a cautious policy entered an expedition then immediately extracted to reserve ambush energy, and repeated this without gathering. Some players recorded more extractions than attempts. The policy now stops to recover below its three-energy safety threshold. That is a strategy correction, not a fabricated game reward or hidden refill. The earlier run is retained as failed-policy evidence, not presented as the corrected curve.

Corrected smoke, full suite and browser evidence will be appended after completion. Phase5 still must compare held-out strategies, actual Vault investment timing, material return per energy/time, grade boundaries, the full100-floor curve and larger mixed cohorts.

## Frozen0.114.0 follow-up

`simulation/verification/006/opening-run.json` archives run20260913T064406Z-ebbf36fa. Eight players/10 days/4 workers completed in15.9706s; median final capability is floor8, with2/8 qualifying for floor9 and0/8 for floor10. Both captured traces replay exactly. The corrected per-floor accounting includes XP from partial group kills even when their haul is lost; a partial kill never counts as a group win. Group wins and extraction transfer gold once.

All62 simulator tests passed in31.41s, including explicit candidate enrollment/replay, whole-group readiness, low-energy policy recovery, partial-group accounting and1-versus-automatic-worker semantic parity. Frozen HTTP action checks passed8 tests in13.14s. These results support the shared-engine integration. They do not meet the final progression gate: first3 floors are already within starter capability; floor8 takes4 days for half this small cohort; phase5 must improve and validate the economic route across the full tower.
