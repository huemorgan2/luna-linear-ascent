from copy import deepcopy
import json
import tempfile
import unittest
from unittest.mock import patch
from simulation.game_adapter import replay,engine_source
from simulation.game_agents import GameConfig,assess,create_character
from simulation.game_results import simulate,save


class GameSwarmTests(unittest.TestCase):
    def test_exact_replay_and_cpu_parity(self):
        cfg=dict(players=2,days=2,max_floor=5,readiness_trials=2,minutes_per_day=5,policies=['tactician','rusher'])
        a=simulate({**cfg,'workers':1});b=simulate({**cfg,'workers':2})
        self.assertEqual(a['deterministic_sha256'],b['deterministic_sha256'])
        self.assertEqual(a['players'],b['players'])
        for p in b['players']:
            self.assertTrue(replay(p['key'],p['trace'],expected_source=b['engine_source']['sha256'],expected_state=p['state_sha256'])[1]['match'])
            self.assertEqual(p['counters'].get('actions',0),sum(1 for x in p['trace'] if x[1] is not None and not x[1].startswith('@'))-12)
            self.assertFalse(any('one of the paths' in k for k in p['bottlenecks']))
            self.assertGreaterEqual(p['final']['gold'],0);self.assertGreaterEqual(p['final']['xp'],0)
        self.assertTrue(all(f['warden']['required_players'] is None for f in b['floors']))
        with tempfile.TemporaryDirectory() as d:self.assertEqual(json.loads(save(b,d).read_text()),json.loads(json.dumps(b)))

    def test_probe_does_not_mutate_live_player_or_grant_resources(self):
        s=create_character('probe-no-mutation');before=deepcopy(s.doc)
        assess(s.doc,0,4,GameConfig(readiness_trials=2))
        self.assertEqual(s.doc,before)

    def test_fixed_world_fixture_and_untraced_player(self):
        data=simulate(dict(players=1,days=1,max_floor=4,world_frontier=1,workers=1,readiness_trials=2,trace_players=0,minutes_per_day=1))
        p=data['players'][0]
        self.assertEqual(p['final']['unlocked_floor'],1)
        self.assertIsNone(p['trace'])
        self.assertEqual(data['boundaries']['world_access'],'Fixed frontier 1')

    def test_source_changes_refuse_mixed_run(self):
        source=engine_source();changed={**source,'sha256':'modified'}
        with patch('simulation.game_results.engine_source',side_effect=[source,source,changed]):
            with self.assertRaisesRegex(RuntimeError,'source changed'):
                simulate(dict(players=1,days=1,max_floor=1,minutes_per_day=1,readiness_trials=2,workers=1))

    def test_validation_rejects_proposal_knobs(self):
        for cfg in ({'group_hp_scale':.5},{'days':True},{'world_frontier':101},{'policies':[{}]}):
            with self.assertRaises(ValueError):GameConfig.from_dict(cfg)
