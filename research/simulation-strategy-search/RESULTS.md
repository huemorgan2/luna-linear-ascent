# Stronger player paths — measured results, 12 September 2026

The corrected planner progresses farther under the same game rules. Across two fresh validation seeds, its median final monster floor after 30 days was **7.5 and 8**, versus **4.5 and 4** for the corrected Mage baseline. The whole game is not yet tuned to the desired gentle slowdown; these results establish a stronger legal path and expose the remaining work.

## Experiment

Search `20260912T195050Z-185ec874` screened 18 profiles on seeds 1901/1902 (2 players per profile/seed, 5 days), then tested three finalists and three baselines on seeds 2001/2002 (4 players per profile/seed, 30 days). Total: 48 runs, 120 player trajectories, 1,800 simulated player-days, 386.560 wall-clock seconds on 8 CPUs. Each candidate receives matched initial player keys and attendance. These are paired trials, not 120 independent human players.

Selection uses mean final qualified floor over all training players; ties use time accumulated qualified for each floor. Unfinished players count. The winner was fixed before validation. All accepted trials have zero rejected actions and zero decision/refusal loops. The original experiment is retained with status `invalid` after it exposed an unavailable close-in action; it is excluded from all conclusions here.

## Same schedule, different methods

Every player is scheduled for 30 minutes/day in 3 visits, with 90% daily attendance and 6 seconds per action. Readiness means winning at least 7 of 8 disposable real-engine test fights with owned gear/condition and restored health/energy. This is a sample gate, not a confidence guarantee.

| Strategy | Median final floor, seed 2001 | Median final floor, seed 2002 | Deaths across 8 players |
|---|---:|---:|---:|
| Mage / historical checks | 4.5 | 4.5 | 213 |
| Mage / corrected checks | 4.5 | 4 | 287 |
| Learner / corrected checks | 4.5 | 3 | 107 |
| Magic planner / farm at character level | 6 | 7 | 127 |
| Magic planner / farm below character level / levels first | 7.5 | 8 | 54 |
| Magic planner / farm below character level / training first | 7.5 | 8 | 54 |

Levels-first and training-first produced identical observed progression here. That preference has no demonstrated advantage in this sample. Farming below character level does have an observed advantage over farming at it. Differences may change with longer runs or different attendance.

## Calendar days to defeat each floor’s monsters

The following pools the selected planner’s eight validation players, retaining unfinished players in the median denominator. The earliest player may change by floor. These are cumulative days since character creation, not days spent on that particular floor.

| Monster floor | Days until half the players can win | Fastest observed days | Players who qualified / 8 |
|---|---:|---:|---:|
| 1 | 0.000 | 0.000 | 8 / 8 |
| 2 | 0.000 | 0.000 | 8 / 8 |
| 3 | 0.002 | 0.001 | 8 / 8 |
| 4 | 3.000 | 3.000 | 8 / 8 |
| 5 | 4.668 | 4.000 | 8 / 8 |
| 6 | 13.000 | 12.000 | 8 / 8 |
| 7 | 16.000 | 15.336 | 7 / 8 |
| 8 | 25.002 | 21.000 | 6 / 8 |
| 9 | Not reached within 30 days | Not reached within 30 days | 0 / 8 |
| 10 | Not reached within 30 days | Not reached within 30 days | 0 / 8 |

The day-one improvement is real, but floor 4 typically takes about 3 days in these seeds, and later floor gains are uneven. This still falls short of the intended gradual slowdown. Do not draw a smooth extrapolated line through unreached floors.

## What the stronger player does

- Carries several damage paths and chooses actual usable attacks from visible monster information. It does not read future random values.
- Uses looted healing before buying it; sells obsolete gear while retaining counter-weapons.
- Buys useful equipment, actual training and character levels; pays the engine’s gold/XP charges.
- Farms below character level and drops a route after repeated losses.
- Sleeps between visits through actual game actions. Sleep is safe in this personal experiment because social ambushes are not executed.

Probe checks now follow equipment/training improvements and can recognize several already-beatable floors at the same time. The historical comparison changes both timing and counter use; the staged world frontier can also change prices/reward fade sooner. It is not a pure timing-only causal experiment. Comparing the corrected Mage with the planner keeps the measurement rule the same.

## Remaining limitations and next tuning decisions

The planner still spends resources on healing and repair, and no validated player qualifies for floor 9 within 30 days. This bounds the tested policies; it does not prove floor 9 impossible. Search richer recovery, honing and investment strategies before declaring an engine hard wall. Tune the actual library only after agreeing on target days per floor, then rerun the same seeds and separate fresh validation. Keep strategic advantages rather than equalizing every weapon.

The actual engine is revision 0.111.0, SHA `3217d52ec623a7b41376921310173bf681573edbe6c9e9d730fccc6a7ae29dae`. No game rules changed. Current individual hunts and school slots are used; proposed group encounters, fixed three-weapon decks and replacement rarity rules are not inserted. Shared warden victories and multiplayer unlock waiting remain outside this personal-engine run. Fastest observed means an empirical result, not a mathematically proven speed limit.

## Inspect and reproduce

Open the dashboard’s **Stronger player paths** section. Each seed has a button showing median and fastest days against the corrected Mage. The report and every raw run remain under `simulation/game-searches/` and `simulation/game-runs/`.

```bash
python3 simulation/game_search.py --screen-players 2 --screen-days 5 --validation-players 4 --validation-days 30 --training-seeds 1901,1902 --validation-seeds 2001,2002 --finalists 3
python3 simulation/run.py --config simulation/configs/stronger-paths.json
python3 simulation/serve.py
```

Worker count defaults to available CPUs. Seed/config results are reproducible across worker counts; IDs and elapsed seconds are expected to differ. A later runner revision is recorded by hash. Saved data is ignored by Git; copy both result directories when moving existing results to another computer.

## Mixed-strategy graph

Run `20260912T195925Z-5edc5381` uses 24 players (four each of Learner, Tactician, Saver, Archer, Mage and Planner), seed 2201, 30 days, 8 CPUs and complete traces for every player. It finished in 80.284 seconds with zero rejected actions.

The median qualifies for floor 4 after 4 days. Only 11 of 24 qualify for floor 5, so its population-median point is correctly absent. The fastest player qualifies for floor 5 after 7 days (Planner #11), floor 6 after 10.004 days (Planner #5), floor 7 after 14 days (Planner #5), and floor 8 after 19 days (Planner #17). All four planners qualify for floor 8 by day 30. This deliberately mixed collection includes weak strategies; its median is not a prediction of a human population that learns and adopts better methods.

[Open median versus fastest](http://127.0.0.1:8766/?run=20260912T195925Z-5edc5381#game-quantiles). [Open the matched-strategy results](http://127.0.0.1:8766/?run=20260912T195710Z-3280ae5a#strategy-search).
