import copy
import random
import unittest
from unittest.mock import patch

from simulation.combat import damage, fight_group, make_group, roll_loot, shield_hit, start_enemy
from simulation.export_inputs import validate
from simulation.model import Config, Rules, Weapon, new_player, stream


class CombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = Rules()

    def enemy(self, **kwargs):
        m = copy.deepcopy(self.r.floors[0]["monsters"][0])
        m.update(hp=1, atk=0, gap=0, specimen="common", deep=False)
        m.update(kwargs)
        return m

    def test_snapshot_shape_and_grade_gates(self):
        validate(self.r.data)
        self.assertEqual(self.r.upgrades[3, 6]["floor"], 84)
        self.assertEqual(self.r.weapons["breach"]["acquisition"]["Legendary"]["dropDurabilityPct"], 10)

    def test_five_enemies_two_energy(self):
        p = new_player(self.r, 0, "rusher")
        p.energy = 2
        result = fight_group(self.r, p, 1, [self.enemy() for _ in range(5)], random.Random(1), trace=True)
        begins = [t for t in result.trace if t["event"] == "begin"]
        self.assertTrue(result.won)
        self.assertEqual([t["exhausted"] for t in begins], [False, False, True, True, True])
        self.assertEqual(result.energy_spent, 2)
        self.assertEqual(p.energy, 0)

    def test_last_point_stays_funded(self):
        p = new_player(self.r, 0, "rusher")
        p.energy = 1
        result = fight_group(self.r, p, 1, [self.enemy(hp=50)], random.Random(1), trace=True)
        self.assertGreater(result.actions, 1)
        self.assertEqual(result.energy_spent, 1)
        self.assertEqual(result.exhausted_enemies, 0)

    def test_retreat_keeps_unspent_energy_and_xp_but_not_haul(self):
        p = new_player(self.r, 0, "rusher")
        p.energy = 5
        with patch("simulation.combat.roll_loot", return_value=([[2, 6], [0, 0], [0, 0], [0, 0]], Weapon("breach"))):
            result = fight_group(self.r, p, 1, [self.enemy() for _ in range(5)], random.Random(1), retreat_after=2)
        self.assertEqual(result.kills, 2)
        self.assertEqual(p.energy, 3)
        self.assertGreater(p.xp, 0)
        self.assertEqual(p.gold, 50)
        self.assertEqual(p.materials, [[0, 0] for _ in range(4)])
        self.assertEqual(result.drops, [])

    def test_complete_haul_and_overflow_xp(self):
        p = new_player(self.r, 0, "rusher")
        p.xp = 24
        with patch("simulation.combat.roll_loot", return_value=([[2, 6], [0, 0], [0, 0], [0, 0]], None)):
            result = fight_group(self.r, p, 1, [self.enemy(), self.enemy()], random.Random(1))
        self.assertTrue(result.won)
        self.assertGreater(p.gold, 50)
        self.assertGreater(p.xp, 24)
        self.assertEqual(p.level, 1)
        self.assertEqual(p.materials[0], [6, 18])  # two rolls plus one authored starter bundle

    def test_exhaustion_halves_damage_once(self):
        p = new_player(self.r, 0, "tactician")
        w = Weapon("breach", 1, 4)
        a = damage(self.r, p, w, self.enemy(), 0)[0]
        b = damage(self.r, p, w, self.enemy(), 0, exhausted=True)[0]
        self.assertAlmostEqual(b, a/2)

    def test_reach_and_shield_leakage(self):
        p = new_player(self.r, 0, "tactician")
        w = Weapon("breach")
        self.assertEqual(damage(self.r, p, w, self.enemy(proposedType="air-common"), 0)[0], 0)
        hp, wear = shield_hit(100, 10000, 10000)
        self.assertEqual((hp, wear), (25, 25))

    def test_dot_does_not_tick_on_application(self):
        p = new_player(self.r, 0, "rusher")
        p.deck = [Weapon("ember")]
        x = fight_group(self.r, p, 1, [self.enemy(hp=70)], random.Random(2), trace=True)
        ticks = [t for t in x.trace if t["event"] == "dot"]
        self.assertTrue(ticks)
        self.assertGreaterEqual(ticks[0]["turn"], 2)

    def test_no_early_legendary_and_seeded_groups(self):
        a = make_group(self.r, 20, stream(1, 1, "g"))
        b = make_group(self.r, 20, stream(1, 1, "g"))
        self.assertEqual(a, b)
        rng = random.Random(1)
        for _ in range(100):
            mats, item = roll_loot(self.r, self.enemy(), 1, rng)
            self.assertEqual(mats[3], [0, 0])
            self.assertTrue(item is None or item.grade != 3)

    def test_invalid_config(self):
        for values in ({"players": 0}, {"days": True}, {"gold_scale": float("nan")}, {"unknown": 1}, {"policies": ["unknown"]}):
            with self.assertRaises(ValueError):
                Config.from_dict(values)


if __name__ == "__main__":
    unittest.main()
