"""The candidate simulator uses the same complete-group transitions as play."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from simulation.game_adapter import replay,state,at_time
from simulation.game_agents import GameConfig,Agent,create_character,assess
from simulation.game_collection import fight,decide


class CandidateGameTests(unittest.TestCase):
    def test_real_group_starts_free_and_replays_exactly(self):
        s=create_character('candidate-replay',ruleset='collection-v1')
        self.assertEqual(len(s.doc['deck']),3)
        s.act('gate');s.act('floor_1')
        if s.doc.get('movie_floor'):s.act('skip')
        energy=s.meters()['energy'];s.act('hunt')
        self.assertEqual(s.meters()['energy'],energy)
        self.assertEqual(len(s.doc['group']['members']),2)
        for _ in range(100):
            if not s.doc.get('group'):break
            s.act(fight(s,'tactician',probe=True),seconds=s.seconds+6)
        self.assertTrue(s.doc['group_result']['won'])
        self.assertEqual(s.doc['group_result']['energy'],2)
        self.assertTrue(replay(s.key,s.trace,expected_state=s.state_hash())[1]['match'])

    def test_readiness_does_not_count_first_kill_as_group_win(self):
        s=create_character('candidate-probe',ruleset='collection-v1')
        cfg=GameConfig(ruleset='collection-v1',max_combat_actions=1,readiness_trials=4)
        result=assess(s.doc,0,1,cfg)
        self.assertEqual(result['wins'],0)
        self.assertTrue(all(r['type']=='group' for r in result['samples']))
        self.assertNotIn('group_result',s.doc)

    def test_low_energy_policy_does_not_loop_empty_expeditions(self):
        agent=Agent(GameConfig(ruleset='collection-v1'),0,'tactician')
        agent.s.doc['energy_val']=2
        agent.s.doc['gold']=1000
        with at_time(agent.s.seconds):self.assertIsNone(decide(agent))

    def test_probe_from_arrow_shop_matches_camp_without_changing_supplies(self):
        s=create_character('candidate-quiver-probe',ruleset='collection-v1')
        s.act('forge');s.act('quiver_shop')
        self.assertTrue(s.doc['quiver_view'])
        bow=s.doc['deck'][1]
        s.doc['quiver']['Common']['arcane']=7
        s.doc['arrow_choice'][bow]='arcane'
        before=deepcopy(s.doc)
        camp=deepcopy(before);camp.pop('quiver_view');camp.update(location='gate_town',floor=1)
        cfg=GameConfig(ruleset='collection-v1',readiness_trials=4)
        self.assertEqual(assess(before,0,1,cfg),assess(camp,0,1,cfg))
        self.assertEqual(s.doc,before)
        self.assertEqual(before['quiver']['Common']['arcane'],7)
        self.assertEqual(before['arrow_choice'][bow],'arcane')

    def test_legal_arrow_purchase_triggers_immediate_readiness_check(self):
        a=Agent(GameConfig(ruleset='collection-v1'),0,'tactician')
        a.act('forge');a.act('quiver_shop');a.act('arrow_buy:Common:ordinary')
        self.assertFalse(a.s.scene.refusal)
        with patch.object(a,'probe') as probe:
            a.improvement_probe('arrow_buy:Common:ordinary')
            probe.assert_called_once_with()

    def test_arrow_selection_changes_readiness_signature(self):
        a=Agent(GameConfig(ruleset='collection-v1'),0,'tactician')
        with patch('simulation.game_agents.assess',return_value=dict(win_rate=0)) as check:
            a.probe();a.probe()
            self.assertEqual(check.call_count,1)
            a.s.doc['arrow_choice'][a.s.doc['deck'][1]]='arcane'
            a.probe()
            self.assertEqual(check.call_count,2)

    def test_ruleset_is_explicit_and_legacy_creation_is_unchanged(self):
        legacy=create_character('legacy-explicit')
        self.assertEqual(legacy.doc['slots'],1)
        self.assertNotEqual(legacy.doc.get('ruleset'),'collection-v1')
        with self.assertRaises(ValueError):GameConfig.from_dict({'ruleset':'guessed'})

    def test_partial_group_kills_count_xp_but_never_count_wins(self):
        from plugin_linear_ascent.engine import bestiary,groups
        from plugin_linear_ascent.content import schema
        a=Agent(GameConfig(ruleset='collection-v1'),0,'tactician')
        a.s.doc.update(location='gate_town',floor=1,training=dict(blade=10,bow=10,staff=10))
        with at_time(a.s.seconds):
            members=[bestiary.rolled_member(a.s.doc,1,schema.get_floor(1).encounters[0].id,opening=True) for _ in range(2)]
            for m in members:
                m.update(hp=1,hp_max=1,gap=3,defense=0)
                m['rewards']=dict(gold=12,xp=3,materials={},weapon=None)
            groups.open_group(a.s.doc,members=members)
        a.floors[1]=dict(attempts=1,wins=0,kills=0,deaths=0,actions=0,gold=0,xp=0)
        a.s.look();a.act('strike:'+a.s.doc['deck'][1]);a.act('flee')
        self.assertEqual(a.floors[1]['kills'],1)
        self.assertEqual(a.floors[1]['wins'],0)
        self.assertEqual(a.floors[1]['gold'],0)
        self.assertEqual(a.floors[1]['xp'],3)

    def test_candidate_cpu_parity_and_worker_replay(self):
        from simulation.game_results import simulate
        config=dict(ruleset='collection-v1',players=2,days=1,max_floor=4,readiness_trials=2,
            minutes_per_day=3,policies=['learner','tactician'],trace_players=2)
        serial=simulate({**config,'workers':1})
        parallel=simulate({**config,'workers':0})
        self.assertEqual(serial['deterministic_sha256'],parallel['deterministic_sha256'])
        self.assertEqual(serial['players'],parallel['players'])
        for player in parallel['players']:
            self.assertTrue(replay(player['key'],player['trace'],expected_source=parallel['engine_source']['sha256'],expected_state=player['state_sha256'])[1]['match'])
