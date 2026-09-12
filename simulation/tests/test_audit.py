import unittest
from simulation.model import Config, Rules, Weapon, new_player
from simulation.combat import damage


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.r = Rules(Config(model_revision="audited-v2"))

    def test_repair_single_capital_basis_and_running_growth(self):
        w = Weapon("breach", 0, 9, .5)
        floor = self.r.state(w)["floor"]
        expected = round(200*1.3**(floor-1)*1.05*.13*.5/1.04**(floor-1))
        self.assertEqual(self.r.repair_quote(w), expected)
        self.assertLess(self.r.repair_quote(w), Rules(Config(model_revision="proposal-v1",repair_fraction=.2)).repair_quote(w))
        self.assertEqual(self.r.repair_quote(Weapon("breach")), 0)

    def test_upgrade_keeps_missing_units_and_refuses_broken(self):
        old = Weapon("breach",0,8,.6)
        new = self.r.upgraded(old)
        self.assertAlmostEqual(self.r.endurance(old)*(1-old.condition),self.r.endurance(new)*(1-new.condition))
        self.assertIsNone(self.r.upgraded(Weapon("breach",0,8,0)))

    def test_fade_and_shield_match_documented_examples(self):
        self.assertEqual(self.r.fade(10,5),1)
        self.assertEqual(self.r.fade(10,4),.9)
        self.assertEqual(self.r.fade(100,1),.25)
        p = new_player(self.r,0,"learner")
        self.assertEqual(self.r.shield_endurance(p),125)

    def test_defense_floor_and_basic_recovery(self):
        p = new_player(self.r,0,"learner")
        enemy = dict(proposedType="ground-common",defense=1e9)
        hit,_ = damage(self.r,p,p.deck[0],enemy,0)
        self.assertAlmostEqual(hit,.15*.75*self.r.attack(p,p.deck[0])*1.25)
        basic = Weapon("breach",condition=0,source="recovery-starter")
        self.assertEqual(self.r.attack(p,basic),5.5)
        self.assertEqual(self.r.repair_quote(basic),1)
        self.assertGreater(damage(self.r,p,basic,enemy,0)[0],0)
        self.assertIsNone(self.r.upgraded(basic))


if __name__ == "__main__": unittest.main()
