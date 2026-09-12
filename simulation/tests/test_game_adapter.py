import copy
from concurrent.futures import ThreadPoolExecutor
import unittest
from simulation.game_adapter import GameSession, at_time, core, state, economy, engine_source, replay


def character(key='engine-test'):
    s=GameSession(key)
    while s.doc['stage']=='intro':s.act(s.legal()[0].id)
    s.act('human');s.act('', 'Testclimber')
    return s


class GameAdapterTests(unittest.TestCase):
    def test_full_document_scene_rng_matches_direct_game(self):
        s=character();s.act('gate');s.act('floor_1')
        if s.doc.get('movie_floor'):s.act('skip')
        s.act('hunt')
        for n in range(60):
            if not s.doc.get('encounter'):break
            s.act('attack',seconds=s.seconds+6)
        with at_time(0):direct=state.new_player(s.key)
        for seconds,opt,text in s.trace:
            with at_time(seconds):
                scene=core.current_scene(direct) if opt is None else core.apply_choice(direct,opt,text)
                direct.pop('_ledger',[]);direct.pop('_effects',[])
                direct['scene']=scene.to_dict()
        self.assertEqual(s.doc,direct)
        self.assertEqual(s.doc['rng_counter'],direct['rng_counter'])
        self.assertGreater(s.doc['rng_counter'],0)
        self.assertTrue(replay(s.key,s.trace,expected_state=s.state_hash())[1]['match'])

    def test_actual_hunt_energy_and_no_proposed_slots(self):
        s=character();self.assertEqual(s.doc['slots'],1)
        s.act('gate');s.act('floor_1')
        if s.doc.get('movie_floor'):s.act('skip')
        before=s.meters()['energy'];s.act('hunt')
        self.assertEqual(s.meters()['energy'],before-economy.COST_WILDS_FIGHT)
        self.assertIsInstance(s.doc['encounter'],dict)
        self.assertNotIn('group',s.doc['encounter'])

    def test_clock_contexts_do_not_leak_and_regen_uses_engine(self):
        def trial(seconds):
            s=character(str(seconds));s.doc['energy_val']=0
            s.look(seconds)
            return s.meters()['energy']
        with ThreadPoolExecutor(2) as pool:values=list(pool.map(trial,[0,2700]))
        self.assertEqual(values,[0,1])
        self.assertNotEqual(state.now().year,1970)

    def test_repair_cost_and_xp_paid_by_game(self):
        s=character();s.act('forge')
        g=economy.FORGE[s.doc['gear']['weapon']]
        s.doc['durability']['weapon']=0
        s.look();before=(s.doc['gold'],s.doc['xp'])
        price=economy.repair_price(g,1)
        s.act('repair_weapon')
        self.assertTrue(s.scene.refusal)
        self.assertEqual(s.doc['gold'],before[0])
        # Prepared unit fixture: the real repair requires XP as well as gold.
        s.doc['xp']=economy.hone_xp(s.doc['unlocked_floor'])
        s.act('repair_weapon')
        self.assertFalse(s.scene.refusal)
        self.assertEqual(s.doc['gold'],before[0]-price)
        self.assertEqual(s.doc['xp'],0)
        self.assertEqual(s.doc['durability']['weapon'],economy.item_pool(g))

    def test_source_guard_and_refused_action(self):
        s=character();before=copy.deepcopy(s.doc['gear']);s.act('buy_mythical_nonexistent')
        self.assertTrue(s.scene.refusal);self.assertEqual(s.doc['gear'],before)
        with self.assertRaises(ValueError):replay(s.key,s.trace,expected_source='different revision')
        source=engine_source();self.assertIn('engine/core.py',source['files'])
        self.assertIn('engine/combat.py',source['files'])
        self.assertTrue(any(k.endswith('.yaml') for k in source['files']))
