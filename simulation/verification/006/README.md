# Candidate group-engine verification (in progress)

Phase3 introduces `ruleset: collection-v1`. Run the actual vendored engine with:

```sh
python3 simulation/run.py --config simulation/configs/collection-opening-smoke.json
python3 -m unittest discover -s simulation/tests -v
```

The first smoke includes8 players across4 policies,10 simulated days,4 workers and a staged personal-readiness frontier. Use `--workers 0` for automatic available-CPU selection. This is a small integration run, not the final100-floor balance experiment. Full multiplayer warden victories remain unmeasured.

Source hashes, replays and reports are appended after the corresponding frozen run and browser gates finish. Do not substitute the historical individual-hunt reports for this group's results.
