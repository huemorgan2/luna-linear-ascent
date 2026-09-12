from copy import deepcopy
import unittest
from unittest.mock import patch

from simulation.game_adapter import state,economy,core,at_time
from simulation.game_agents import Agent,GameConfig
from simulation.game_planner import decide,obsolete_sale,legal_actions,fight


class PlannerTests(unittest.TestCase):
    def agent(self):return Agent(GameConfig(players=1,days=1,policies=('planner',),readiness_trials=2),0,'planner')

    def test_chain_qualified_floors_and_cache_failed_observation(self):
        a=self.agent();before=(a.s.doc['gold'],a.s.doc['xp'])
        with patch('simulation.game_agents.assess',side_effect=[dict(win_rate=1),dict(win_rate=1),dict(win_rate=0)]) as assess:
            a.probe();a.probe()
            self.assertEqual(assess.call_count,3)
        self.assertEqual([m['floor'] for m in a.milestones],[1,2])
        self.assertEqual([m['day'] for m in a.milestones],[0,0])
        self.assertEqual((a.s.doc['gold'],a.s.doc['xp']),before)
        self.assertEqual(a.s.doc['unlocked_floor'],3)

    def test_historical_mode_keeps_one_floor_per_check(self):
        a=self.agent();a.cfg.probe_mode='session'
        with patch('simulation.game_agents.assess',return_value=dict(win_rate=1)) as assess:a.probe()
        self.assertEqual(assess.call_count,1);self.assertEqual(a.ready,1)

    def test_carried_medgel_uses_real_engine_without_gold(self):
        a=self.agent();a.s.doc['hp']=10;a.s.doc['gold']=0;a.s.doc['inventory']['medgel']=1;a.s.look()
        before=deepcopy(a.s.doc)
        with at_time(a.s.seconds):action=decide(a)
        self.assertEqual(action,'use_medgel');self.assertEqual(a.s.doc,before)
        a.act(action)
        self.assertEqual(a.s.doc['hp'],35);self.assertNotIn('medgel',a.s.doc['inventory']);self.assertEqual(a.s.doc['gold'],0)

    def test_sell_obsolete_keeps_counter_and_real_pawn_price(self):
        a=self.agent();p=a.s.doc
        p['gear']['weapon']='notched_cleaver';p['held']=['notched_cleaver'];p['inventory'].update(scrap_dagger=1,basic_bow=1,medgel=2)
        with at_time(0):
            self.assertEqual(obsolete_sale(p),'scrap_dagger');offer=core._pawn_offer(p,economy.FORGE['scrap_dagger'])
        a.s.act('pawn');gold=p['gold'];a.s.act('sell_scrap_dagger')
        self.assertEqual(p['gold'],gold+offer);self.assertIn('basic_bow',p['inventory']);self.assertEqual(p['inventory']['medgel'],2)

    def test_planner_sleeps_between_visits_and_replays(self):
        from simulation.game_adapter import replay,engine_source
        a=self.agent();a.cfg.minutes_per_day=3
        result=a.run()
        self.assertGreaterEqual(sum(x[1]=='sleep_fields' for x in result['trace']),2)
        self.assertTrue(replay(result['key'],result['trace'],expected_source=engine_source()['sha256'],expected_state=result['state_sha256'])[1]['match'])
        self.assertFalse(result['bottlenecks'].get('decision_loop'))

    def test_planner_config_is_validated(self):
        for cfg in ({'probe_mode':'invented'},{'planner_path':'laser'},{'planner_margin':3},{'planner_growth':'free'}):
            with self.assertRaises(ValueError):GameConfig.from_dict(cfg)
