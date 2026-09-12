import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from simulation.bosses import battle, evaluate_floor, minimum_party, parameters
from simulation.model import Config, Rules, new_player
from simulation.results import CpuPool, aggregate, cohort_stats, save_run, simulate, validate_run
from simulation.swarm import readiness, reference_player, snapshot


class SwarmTests(unittest.TestCase):
    def test_probes_do_not_mutate_player(self):
        r = Rules(Config(readiness_trials=4))
        p = new_player(r, 1, "tactician")
        before = copy.deepcopy(p.__dict__)
        a = readiness(r, p, 1)
        b = readiness(r, p, 1)
        self.assertEqual(a, b)
        self.assertEqual(p.__dict__, before)

    def test_replay_and_seed_effect(self):
        cfg = dict(players=2, days=3, workers=1, max_floor=5, readiness_trials=4, warden_trials=1)
        a, b = simulate(cfg), simulate(cfg)
        self.assertEqual(a["deterministic_sha256"], b["deterministic_sha256"])
        c = simulate({**cfg, "seed": 999})
        self.assertNotEqual(a["deterministic_sha256"], c["deterministic_sha256"])
        for p in a["players"]:
            self.assertGreaterEqual(p["final"]["gold"], 0)
            self.assertGreaterEqual(p["final"]["bank"], 0)
            self.assertGreaterEqual(p["final"]["energy"], 0)
            self.assertTrue(all(x >= 0 for pair in p["final"]["materials"] for x in pair))
            days = [m["day"] for m in p["milestones"]]
            self.assertEqual(days, sorted(days))
            counts = p["counters"]
            incoming = 50+counts.get("earned_gold",0)+counts.get("interest",0)+counts.get("salvage_gold",0)
            outgoing = sum(v for k,v in counts.items() if k.startswith("spent_"))+counts.get("lost_gold",0)
            self.assertAlmostEqual(incoming-outgoing,p["final"]["gold"]+p["final"]["bank"],places=7)

    def test_censored_players_are_not_discarded(self):
        m = dict(floor=10, day=4, active_minutes=20, assessment=dict(win_rate=1))
        players = [dict(milestones=[m]), dict(milestones=[]), dict(milestones=[])]
        x = cohort_stats(players, 10, 30)
        self.assertEqual(x["mean_days"], 4)
        self.assertEqual(x["reach_fraction"], 1/3)
        self.assertIsNone(x["population_median"])
        self.assertIsNone(x["population_p90"])
        self.assertEqual(x["restricted_mean_days"], 64/3)
        y = cohort_stats(players, 11, 30)
        self.assertIsNone(y["mean_days"])
        self.assertEqual(y["censored"], 3)

    def test_parallel_matches_serial(self):
        cfg = dict(players=6, days=2, max_floor=6, readiness_trials=4, warden_trials=1)
        a = simulate({**cfg, "workers": 1})
        with patch("simulation.results.available_cpus", return_value=3):
            b = simulate({**cfg, "workers": 0})
        self.assertEqual(b["execution"]["workers"], 3)
        self.assertEqual(a["deterministic_sha256"], b["deterministic_sha256"])
        self.assertEqual(a["players"], b["players"])
        self.assertEqual(a["wardens"], b["wardens"])
        self.assertEqual([p["id"] for p in b["players"]], list(range(6)))

    def test_many_cpu_windows_pool_shards(self):
        # Verify dispatch past Python's per-pool limit without spawning 128 test processes.
        with patch("simulation.results.platform.system", return_value="Windows"), patch("simulation.results.ProcessPoolExecutor") as executor:
            pool = CpuPool(128, Config())
            self.assertEqual([c.kwargs["max_workers"] for c in executor.call_args_list], [61,61,6])
            for i in range(128):
                pool.submit(str, i)
            self.assertEqual(executor.return_value.submit.call_count, 128)
            pool.shutdown()

    def test_run_roundtrip_and_validation(self):
        a = simulate(dict(players=1, days=1, max_floor=2, readiness_trials=4, warden_trials=1))
        with tempfile.TemporaryDirectory() as d:
            p = save_run(a, d)
            self.assertEqual(validate_run(json.loads(p.read_text()))["deterministic_sha256"], a["deterministic_sha256"])
        with self.assertRaises(ValueError):
            validate_run({"schema_version": 2})

    def test_finite_boss_energy_and_healing(self):
        r = Rules(Config(warden_trials=1))
        p = reference_player(r, 20)
        m = snapshot(r, p, 20, 0, dict(win_rate=1))
        params = parameters(r, 20, m)
        a = battle(r, 20, [m], 1, {**params, "hp": 1e20, "heal_per_second": 0}, trace=True)
        self.assertFalse(a["won"])
        self.assertLessEqual(a["strikes"], m["energy"]//r.config.warden_energy_per_strike)
        self.assertTrue(all(t["energy"] >= 0 for t in a["trace"]))
        easy = minimum_party(r, 20, [m], {**params, "heal_per_second": 0})
        hard = minimum_party(r, 20, [m], {**params, "heal_per_second": params["heal_per_second"]*2})
        self.assertGreaterEqual(hard["required"] or 10000, easy["required"] or 10000)
        empty = evaluate_floor(r, 20, [])
        self.assertIsNone(empty["observed"]["required"])
        self.assertEqual(empty["available_players"], 0)


if __name__ == "__main__":
    unittest.main()
