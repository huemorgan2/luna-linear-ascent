"""Conservation and replay of prepared strategies through the actual engine."""
from copy import deepcopy
import unittest
from simulation.game_agents import Agent,GameConfig
from simulation.game_adapter import at_time,state,replay
from simulation.game_strategy import decide,investments,prepare_owned
from plugin_linear_ascent.engine import collection

class StrategyTests(unittest.TestCase):
    def agent(self,policy='planner'):
        return Agent(GameConfig(ruleset='collection-v1',days=1,max_floor=5,readiness_trials=2,minutes_per_day=2,planner_margin=1),0,policy)

    def test_quotes_and_decision_do_not_change_earned_state_or_rng(self):
        a=self.agent();a.s.doc.update(gold=1000,level=4,unlocked_floor=6)
        a.s.look();before=deepcopy(a.s.doc)
        with at_time(a.s.seconds):
            investments(a);decide(a)
        self.assertEqual(a.s.doc,before)

    def test_investor_collects_return_once_and_can_fund_real_work(self):
        a=self.agent('investor');a.s.doc['gold']=1000
        a.act('vault');a.act('deposit_all')
        a.s.look(86400)
        with at_time(a.s.seconds):choice=a.step()
        self.assertEqual(choice,'collect_interest')
        before=a.s.doc['bank'];a.act(choice)
        self.assertGreater(a.s.doc['bank'],before)
        earned=a.s.doc['bank']
        a.s.look();self.assertEqual(a.s.doc['bank'],earned)
        with at_time(a.s.seconds):choice=decide(a)
        self.assertEqual(choice,'withdraw_all')
        a.act(choice);self.assertEqual(a.s.doc['bank'],0)
        self.assertEqual(a.s.doc['gold'],earned)
        for _ in range(12):
            with at_time(a.s.seconds):choice=decide(a)
            if choice is None:break
            a.act(choice);self.assertFalse(a.s.scene.refusal)
            if any(e['kind'] in ('buy','craft','hone','upgrade') for e in a.s.events):break
        self.assertLess(a.s.doc['gold'],earned)

    def test_new_grade_is_bought_by_action_and_selected_without_erasing_owned_items(self):
        a=self.agent();a.s.doc.update(level=30,unlocked_floor=28,gold=10**9)
        a.s.doc['materials']={'Steel':100,'Hardwood':100}
        a.s.look();old=set(a.s.doc['collection'])
        # Use the strategy's real Forge option, without minting a new item in this test.
        options=investments(a)
        choice=next(row for row in options if row[2].startswith('forge_craft:') and row[2].endswith(':Rare'))
        a.act('forge');a.act(choice[2]);self.assertFalse(a.s.scene.refusal)
        for _ in range(10):
            with at_time(a.s.seconds):action=prepare_owned(a)
            if not action:break
            a.act(action);self.assertFalse(a.s.scene.refusal)
        self.assertTrue(old.issubset(a.s.doc['collection']))
        self.assertTrue(any(a.s.doc['collection'][i]['grade']=='Rare' for i in a.s.doc['deck']))
        self.assertTrue(collection.reconcile(a.s.doc)['ok'])
        self.assertLess(a.s.doc['gold'],10**9)
        self.assertLess(a.s.doc['materials']['Steel']+a.s.doc['materials']['Hardwood'],200)

    def test_strategy_settings_validate_real_families_and_flags(self):
        for values in ({'collection_deck':['unknown']*3},{'collection_deck':['breach']},{'collection_gather':'yes'}):
            with self.assertRaises(ValueError):GameConfig.from_dict(values)
        c=GameConfig.from_dict({'collection_deck':['ramguard','hawkeye','repulsor'],'collection_gather':False})
        self.assertEqual(GameConfig.from_dict(c.to_dict()),c)

    def test_prepared_and_random_players_replay_exactly(self):
        for policy in ('planner','investor','random'):
            a=self.agent(policy);out=a.run()
            self.assertEqual(out['counters'].get('refused_actions',0),0)
            self.assertEqual(out['bottlenecks'].get('decision_loop',0),0)
            self.assertTrue(replay(out['key'],out['trace'],expected_state=out['state_sha256'])[1]['match'])

    def test_navigation_wakes_sleeping_player_and_short_visits_have_play_time(self):
        from simulation.game_collection import navigate
        a=self.agent();a.act('sleep_menu');a.act('sleep_fields');a.s.look(28800)
        self.assertEqual(navigate(a,'town'),'wake')
        out=self.agent().run()
        self.assertGreater(out['counters'].get('enemy_start',0),0)

    def test_new_policies_are_identical_with_serial_and_available_cpus(self):
        from simulation.game_results import simulate
        config=dict(ruleset='collection-v1',players=2,days=1,max_floor=5,readiness_trials=2,
            minutes_per_day=2,policies=['planner','investor'],trace_players=2,readiness_policy='planner')
        serial=simulate({**config,'workers':1});parallel=simulate({**config,'workers':0})
        self.assertEqual(serial['deterministic_sha256'],parallel['deterministic_sha256'])
        for row in parallel['players']:
            self.assertTrue(replay(row['key'],row['trace'],expected_state=row['state_sha256'])[1]['match'])

if __name__=='__main__':unittest.main()
