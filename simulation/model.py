"""Inspectable model contracts; candidate coefficients are saved in every run."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parent
POLICIES = {
    "learner": dict(name="Learner", color="#bdc5c5", deck=["breach", "ember", "skirmisher"],
        description="Uses the strongest listed weapon; occasional wrong choice; upgrades the main weapon first.",
        tactical=False, mistakes=.18, retreat=.15, bank=.1, deep=False, exhausted=False),
    "tactician": dict(name="Tactician", color="#63d5c2", deck=["ramguard", "hexglass", "skirmisher"],
        description="Chooses reachable counters and ready techniques; maintains three useful tools; retreats early.",
        tactical=True, mistakes=0., retreat=.30, bank=.25, deep=True, exhausted=False),
    "farmer": dict(name="Material hunter", color="#c9a6ec", deck=["viper", "ember", "runestring"],
        description="Targets the carrier of the missing recipe material; saves for efficient upgrades.",
        tactical=True, mistakes=.02, retreat=.25, bank=.2, deep=True, exhausted=False),
    "saver": dict(name="Saver", color="#e0c17a", deck=["breach", "frostbind", "hawkeye"],
        description="Banks most spare gold for interest; buys upgrades only when readiness is blocked.",
        tactical=True, mistakes=.04, retreat=.35, bank=.85, deep=False, exhausted=False),
    "rusher": dict(name="Rusher", color="#ef907f", deck=["thunder", "stormbell", "recoil"],
        description="Pushes the next floor, chooses deep hunts, and keeps fighting while exhausted.",
        tactical=True, mistakes=.08, retreat=.08, bank=0., deep=True, exhausted=True),
    "specialist": dict(name="Specialist", color="#8ab9f0", deck=["viper", "ramguard", "runestring"],
        description="Two blades and an arcane-capable bow; chooses favorable ground routes and combo actions.",
        tactical=True, mistakes=0., retreat=.25, bank=.3, deep=True, exhausted=False),
}


@dataclass
class Config:
    players: int = 60
    days: int = 180
    workers: int = 0
    seed: int = 1601
    max_floor: int = 100
    policies: list = field(default_factory=lambda: list(POLICIES))
    minutes_per_day: float = 30
    sessions_per_day: int = 3
    attendance: float = .9
    activity_spread: float = .2
    action_seconds: float = 6
    energy_regen_minutes: float = 45
    exhaustion_damage: float = .5
    exhaustion_speed: int = 2
    readiness_trials: int = 8
    readiness_threshold: float = .8
    max_combat_actions: int = 48
    group_hp_scale: float = 1
    group_size_scale: float = 1
    gold_scale: float = 1
    material_scale: float = 1
    upgrade_cost_scale: float = 1
    defense_cost_scale: float = 1
    repair_fraction: float = .2
    death_gold_loss: float = .5
    death_condition_loss: float = .1
    bank_interest_daily: float = .05
    sleep_hours: float = 8
    warden_hp_scale: float = 1
    warden_pool: str = "base"
    warden_heal_start: int = 10
    warden_heal_reference: float = 1.05
    warden_heal_growth: float = 1.035
    warden_cadence_seconds: float = 3
    warden_energy_per_strike: int = 3
    warden_max_party: int = 256
    warden_trials: int = 3
    warden_success_threshold: float = .67

    @classmethod
    def from_dict(cls, values):
        if not isinstance(values, dict):
            raise ValueError("Settings must be a JSON object")
        unknown = set(values) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError("Unknown settings: " + ", ".join(sorted(unknown)))
        c = cls(**values)
        ranges = {
            "players": (1, 100000, int), "days": (1, 3650, int), "seed": (0, 2**31-1, int),
            "workers": (0, 1024, int),
            "max_floor": (1, 100, int), "minutes_per_day": (1, 240, float),
            "sessions_per_day": (1, 12, int), "attendance": (.1, 1, float),
            "activity_spread": (0, .8, float), "action_seconds": (1, 60, float),
            "energy_regen_minutes": (1, 180, float), "exhaustion_damage": (.05, 1, float),
            "exhaustion_speed": (0, 8, int), "readiness_trials": (4, 32, int),
            "readiness_threshold": (.5, 1, float), "max_combat_actions": (8, 160, int),
            "group_hp_scale": (.1, 5, float), "group_size_scale": (.5, 2, float),
            "gold_scale": (.1, 20, float), "material_scale": (.1, 20, float),
            "upgrade_cost_scale": (.1, 10, float), "defense_cost_scale": (.1, 10, float),
            "repair_fraction": (0, 1, float), "death_gold_loss": (0, 1, float),
            "death_condition_loss": (0, .9, float), "bank_interest_daily": (0, .1, float),
            "sleep_hours": (0, 12, float), "warden_hp_scale": (.05, 100, float),
            "warden_heal_start": (1, 101, int), "warden_heal_reference": (0, 20, float),
            "warden_heal_growth": (1, 1.15, float), "warden_cadence_seconds": (1, 30, float),
            "warden_energy_per_strike": (1, 12, int), "warden_max_party": (1, 512, int),
            "warden_trials": (1, 8, int), "warden_success_threshold": (.5, 1, float),
        }
        for key, (lo, hi, typ) in ranges.items():
            v = getattr(c, key)
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
                raise ValueError(f"{key} must be a finite number")
            if typ is int and not isinstance(v, int):
                raise ValueError(f"{key} must be an integer")
            if not lo <= v <= hi:
                raise ValueError(f"{key} must be between {lo} and {hi}")
        if not isinstance(c.policies, list) or not c.policies or any(not isinstance(x, str) or x not in POLICIES for x in c.policies):
            raise ValueError("Select one or more known policies")
        if len(set(c.policies)) != len(c.policies):
            raise ValueError("Policies cannot be duplicated")
        if c.warden_pool not in ("base", "legacy_shared"):
            raise ValueError("warden_pool must be base or legacy_shared")
        return c

    def to_dict(self):
        return asdict(self)


class Rules:
    def __init__(self, config=None, path=None):
        self.config = config or Config()
        path = path or ROOT / "data/inputs.json"
        raw = Path(path).read_bytes()
        self.hash = hashlib.sha256(raw).hexdigest()
        self.data = json.loads(raw)
        self.floors = self.data["floors"]
        self.economy = self.data["economy"]
        self.characters = self.data["characters"]
        self.weapons = {w["id"]: w for w in self.data["model"]["weapons"]}
        self.types = {t["id"]: t for t in self.data["model"]["types"]}
        self.upgrades = {(s["gi"], s["level"]): s for s in self.data["upgrades"]}
        self.arrows = {a["id"]: a for a in self.data["model"]["arrows"]}
        self.loot = self.data["model"]["loot"]

    def state(self, item):
        return self.upgrades[(item.grade, item.level)]

    def attack(self, p, item):
        return (self.characters[p.level-1]["atk"] + self.state(item)["atk"] *
                self.weapons[item.family]["factor"] * max(0, item.condition))

    def armor(self, p):
        return self.economy[p.armor_floor-1]["armor"]

    def shield(self, p):
        return self.economy[p.shield_floor-1]["shield"] * p.shield_condition

    def hp_max(self, p):
        return self.characters[p.level-1]["hp"] + 4 * self.armor(p)

    def energy_cap(self, p):
        best = max([p.armor_floor, p.shield_floor] + [self.state(w)["floor"] for w in p.deck])
        return self.economy[min(100, best)-1]["energy_cap"]

    def price(self, item, through=False):
        steps = range(item.level+1) if through else [item.level]
        return sum(math.ceil(self.upgrades[item.grade, l]["gold"] *
            self.weapons[item.family]["cost"] * self.config.upgrade_cost_scale) for l in steps)

    def group_size(self, floor, rng):
        bounds = (2, 2) if floor <= 3 else (2, 3) if floor <= 10 else (2, 4) if floor <= 25 else (3, 4) if floor <= 50 else (3, 5) if floor <= 75 else (3, 6)
        return max(2, round(rng.randint(*bounds) * self.config.group_size_scale))


@dataclass
class Weapon:
    family: str
    grade: int = 0
    level: int = 0
    condition: float = 1
    cooldown: int = 0
    source: str = "starter"


@dataclass
class Player:
    id: int
    policy: str
    level: int = 1
    xp: float = 0
    gold: float = 50
    bank: float = 0
    hp: float = 80
    energy: float = 24
    armor_floor: int = 1
    shield_floor: int = 1
    shield_condition: float = 1
    speed: int = 5
    deck: list = field(default_factory=list)
    materials: list = field(default_factory=lambda: [[0, 0] for _ in range(4)])
    ammo: dict = field(default_factory=lambda: {"ordinary": 30, "arcane": 10, "poison": 0, "fire": 0, "pinning": 0, "concussive": 0})
    ready_floor: int = 0
    ready: dict = field(default_factory=dict)
    counters: dict = field(default_factory=dict)
    bottlenecks: dict = field(default_factory=dict)
    active_seconds: float = 0
    last_time: float = 0
    last_bank_day: int = 0
    tutorial: bool = False

    def count(self, key, amount=1):
        self.counters[key] = self.counters.get(key, 0) + amount

    def wealth(self):
        return self.gold + self.bank

    def pay(self, amount, category):
        amount = max(0, amount)
        if self.wealth() + 1e-8 < amount:
            return False
        from_bank = max(0, amount-self.gold)
        self.bank = max(0, self.bank-from_bank)
        self.gold = max(0, self.gold-(amount-from_bank))
        self.count("spent_"+category, amount)
        return True


def new_player(rules, ident, policy):
    p = Player(ident, policy, deck=[Weapon(f) for f in POLICIES[policy]["deck"]])
    p.hp = rules.hp_max(p)
    p.energy = rules.energy_cap(p)
    return p


def stream(seed, player, purpose):
    h = hashlib.sha256(f"{seed}:{player}:{purpose}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def interpolate(knots, floor):
    for i in range(1, len(knots)):
        a, b = knots[i-1], knots[i]
        if floor <= b[0]:
            t = max(0, (floor-a[0])/(b[0]-a[0]))
            return [x+(y-x)*t for x, y in zip(a[1:], b[1:])]
    return knots[-1][1:]
