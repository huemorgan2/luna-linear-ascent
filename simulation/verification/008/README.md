# Phase4 ammunition and effects checkpoint

Actual engine0.115.0,13 September2026. Not a completed progression tune.

`opening-quiver-fixed.json`:8players,10days,seed31001,4workers,maximumfloor10. Four ordinary policies; no fixture gifts to the progressing players. Run duration20.9167seconds. Engine hash3b3ca0a8fcf481e40bc8378ab1649d6c5d7fd5386df25fbc28442bb30319268c; semantic hashf9935c083979a93733ef90acb380b5fec1c76b5c55882c31853153ad41a73565. Full captured traces for two players remain in the file. Reproduce with `python -m simulation.run --config simulation/configs/collection-opening-smoke.json --quiet` and the pinned engine/simulator source.

All8 reached floor6,6 reached7,5 reached8,3 reached9,1 reached10. Population median readyfloor8; floor8 population median7days. Floor10 fastest observed8days, population median unavailable. This remains substantially slower than the strong-policy floor10 target1.5875days. The two learners stopped at6 with health/cash constraints; the tacticians reached9/8, savers8/7, planners10/9. The result includes finite ammo, current condition, source-persistent effects and varied arrival distances; phase3's different rules remain archived separately.

The first attempted run failed before writing an artifact because a disposable readiness clone retained `quiver_view` while being moved to a floor camp. The corrected setup clears the presentation flag, preserves actual owned ammo/selection, and checks capability immediately after replenishment.17 focused tests and65 full simulator tests passed; the full suite includes serial/automatic-worker equality and exact trace replay. No live-game relaxation was made to permit a hunt from the Forge.

Later source revisions must produce separate runs. This checkpoint proves the new loop executes; it does not prove the desired slowdown, all100floors, investment advantage, all-site returns or shared-warden headcounts. Those remain required work.
