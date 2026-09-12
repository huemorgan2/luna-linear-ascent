import copy
import unittest
from simulation.model import Config,Rules,Weapon,new_player,stream
from simulation.combat import fight_group,make_group
from simulation.policies import maintain,route,reserve
from simulation.swarm import invest,simulate_player,readiness
from simulation.diagnostics import diagnose


class RecoveryTests(unittest.TestCase):
    def rules(self,**kwargs):
        return Rules(Config(players=1,days=3,max_floor=12,readiness_trials=4,warden_trials=1,**kwargs))

    def test_retained_starter_uses_same_three_slots_without_gold_grant(self):
        r=self.rules(recovery_mode="starter")
        p=new_player(r,1,"tactician");p.gold=0
        for w in p.deck:w.condition=0
        maintain(r,p,1)
        self.assertEqual(len(p.deck),3);self.assertEqual(len(p.stored_deck),3)
        self.assertTrue(all(w.source=="recovery-starter" for w in p.deck))
        self.assertEqual(p.wealth(),0)
        self.assertTrue(all(w.condition==0 for w in p.stored_deck.values()))
        self.assertGreater(readiness(r,p,1)["win_rate"],0)

    def test_partial_repair_spends_actual_money_without_full_free_repair(self):
        r=self.rules(recovery_mode="partial")
        p=new_player(r,1,"tactician");p.gold=5
        p.deck[0]=Weapon("breach",0,8,0)
        maintain(r,p,1)
        self.assertGreater(p.deck[0].condition,0)
        self.assertLess(p.deck[0].condition,1)
        self.assertLessEqual(p.counters.get("spent_repairs",0),5)
        self.assertAlmostEqual(p.wealth()+sum(v for k,v in p.counters.items() if k.startswith("spent_")),5)

    def test_original_rusher_stays_reckless(self):
        r=self.rules();p=new_player(r,1,"rusher")
        self.assertFalse(maintain(r,p,1));self.assertEqual(reserve(r,p),0)
        self.assertIsNone(route(r,p,stream(1,1,"route")))

    def test_weak_loadout_selects_lower_route(self):
        r=self.rules();p=new_player(r,1,"tactician");p.ready_floor=10
        floor,_=route(r,p,stream(1,1,"route"))
        self.assertLess(floor,10)
        self.assertGreaterEqual(floor,1)

    def test_broken_cannot_be_upgraded_with_materials_and_money(self):
        r=self.rules(decision_model="original");p=new_player(r,1,"learner")
        p.level=2;p.gold=1000;p.materials[0]=[100,100]
        for w in p.deck:w.condition=0
        invest(r,p,2)
        self.assertTrue(all(w.level==0 for w in p.deck))

    def test_diagnostics_are_non_mutating_and_finances_reconcile(self):
        r=self.rules();p=new_player(r,1,"tactician")
        before=copy.deepcopy(p.__dict__);d=diagnose(r,p,readiness)
        self.assertEqual(p.__dict__,before)
        self.assertEqual(d["finances"]["conservation_error"],0)
        out=simulate_player(r,0,"tactician")
        self.assertTrue(out["timeline"])
        self.assertLess(abs(out["diagnosis"]["finances"]["conservation_error"]),1e-6)
        self.assertTrue(all(x>=0 for x in out["final"]["ammo"].values()))


if __name__=="__main__":unittest.main()
