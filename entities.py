import random
import math
from typing import List, Dict
import inspect


class Enemy:
    def __init__(self,
                 base_hp,
                 base_min_damage,
                 base_max_damage,
                 armor,
                 role="enemy",
                 level=1,
                 crit_chance=0.0,
                 crit_damage=0,
                 alive=True,
                 kill_chance=0.01,
                 experience=1,
                 regular_drop=None,
                 drop_chance=0.1,
                 probability=0.01,
                 map_size=1000,
                 max_entities=None,
                 max_entities_total=None,
                 herd_probability=0.5):
        if regular_drop is None:
            regular_drop = {}

        self.base_hp = base_hp
        self.base_min_damage = base_min_damage
        self.base_max_damage = base_max_damage
        self.armor = armor
        self.alive = alive
        self.level = level
        self.kill_chance = kill_chance
        self.crit_chance = crit_chance
        self.crit_damage = crit_damage
        self.role = role
        self.experience = experience
        self.regular_drop = regular_drop
        self.drop_chance = drop_chance
        self.probability = probability
        self.map_size = map_size
        self.max_entities = max_entities
        self.max_entities_total = max_entities_total
        self.herd_probability = herd_probability
        self.hp = self.calculate_hp()
        self.min_damage, self.max_damage = self.calculate_damage()

    def calculate_hp(self):
        return int(self.base_hp * (1 + 0.2 * (self.level - 1))) # 20% increase per level

    def calculate_damage(self):
        scaling_factor = 1 + 0.10 * (self.level - 1)  # 10% increase per level
        min_damage = int(self.base_min_damage * scaling_factor)
        max_damage = int(self.base_max_damage * scaling_factor)
        return min_damage, max_damage

    def roll_damage(self):
        damage = random.randint(self.min_damage, self.max_damage)
        message = "normal hit"
        if random.random() < self.crit_chance:
            damage = int(damage * self.crit_damage)
            message = "critical hit"
        return {"damage": damage, "message": message}

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "fight", "action": f"/fight?target={self.type}"}]


class Dragon(Enemy):
    type = "dragon"

    def __init__(self, level=1):
        super().__init__(base_hp=350,
                         base_min_damage=20,
                         base_max_damage=30,
                         crit_chance=0.4,
                         crit_damage=2.0,
                         armor=0,
                         level=level,
                         experience=100,
                         drop_chance=1,
                         regular_drop={"bismuth": 50},
                         probability=0.001,
                         map_size=1000,
                         max_entities=10,
                         max_entities_total=10,
                         herd_probability=0)


class Boar(Enemy):
    type = "boar"

    def __init__(self, level=1):
        super().__init__(base_hp=30,
                         base_min_damage=1,
                         base_max_damage=3,
                         crit_chance=0.1,
                         crit_damage=1.5,
                         armor=0,
                         level=level,
                         experience=1,
                         drop_chance=0.2,
                         regular_drop={"food": 1},
                         probability=0.05,
                         map_size=1000,
                         max_entities=500,
                         max_entities_total=1000,
                         herd_probability=0.7)

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "hunt", "action": f"/fight?target={self.type}"}]


class Wolf(Enemy):
    type = "wolf"

    def __init__(self, level=1):
        super().__init__(base_hp=60,
                         base_min_damage=2,
                         base_max_damage=6,
                         crit_chance=0.25,
                         crit_damage=1.8,
                         armor=0,
                         level=level,
                         experience=2,
                         drop_chance=0.3,
                         regular_drop={"food": 1},
                         probability=0.03,
                         map_size=1000,
                         max_entities=300,
                         max_entities_total=600,
                         herd_probability=0.8)

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "hunt", "action": f"/fight?target={self.type}"}]


class Goblin(Enemy):
    type = "goblin"

    def __init__(self, level=1):
        super().__init__(base_hp=40,
                         base_min_damage=4,
                         base_max_damage=6,
                         crit_chance=0.15,
                         crit_damage=1.6,
                         armor=1,
                         level=level,
                         experience=3,
                         drop_chance=0.4,
                         regular_drop={"gold": 5},
                         probability=0.02,
                         map_size=1000,
                         max_entities=200,
                         max_entities_total=400,
                         herd_probability=0.6)


class Specter(Enemy):
    type = "specter"

    def __init__(self, level=2):
        super().__init__(base_hp=80,
                         base_min_damage=10,
                         base_max_damage=20,
                         crit_chance=0.3,
                         crit_damage=2.0,
                         armor=0,
                         level=level,
                         experience=10,
                         drop_chance=0.6,
                         regular_drop={"ectoplasm": 1},
                         probability=0.01,
                         map_size=1000,
                         max_entities=100,
                         max_entities_total=200,
                         herd_probability=0.3)

    def roll_damage(self):
        damage_info = super().roll_damage()
        if damage_info["message"] == "critical hit":
            # Specters drain health on critical hits
            self.hp += damage_info["damage"] // 2
        return damage_info


class Hatchling(Enemy):
    type = "hatchling"

    def __init__(self, level=3):
        super().__init__(base_hp=150,
                         base_min_damage=20,
                         base_max_damage=40,
                         crit_chance=0.2,
                         crit_damage=1.8,
                         armor=5,
                         level=level,
                         experience=25,
                         drop_chance=0.8,
                         regular_drop={"dragon_scale": 1},
                         probability=0.005,
                         map_size=1000,
                         max_entities=50,
                         max_entities_total=100,
                         herd_probability=0.2)
        self.breath_attack_cooldown = 0

    def roll_damage(self):
        if self.breath_attack_cooldown == 0:
            # Use breath attack
            damage = random.randint(int(self.max_damage * 1.5), int(self.max_damage * 2))
            self.breath_attack_cooldown = 3
            return {"damage": damage, "message": "breath attack"}
        else:
            # Normal attack
            damage_info = super().roll_damage()
            self.breath_attack_cooldown -= 1
            return damage_info

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "slay", "action": f"/fight?target={self.type}"}]

class Bandit(Enemy):
    type = "bandit"

    def __init__(self, level=2):
        super().__init__(base_hp=70,
                         base_min_damage=8,
                         base_max_damage=15,
                         crit_chance=0.2,
                         crit_damage=1.7,
                         armor=2,
                         level=level,
                         experience=5,
                         drop_chance=0.5,
                         regular_drop={"gold": 10},
                         probability=0.03,
                         map_size=1000,
                         max_entities=250,
                         max_entities_total=500,
                         herd_probability=0.4)

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < 0.1:  # 10% chance to steal gold
            damage_info["message"] += " and stole some gold"
        return damage_info


class Troll(Enemy):
    type = "troll"

    def __init__(self, level=3):
        self.regeneration_rate = 5  # Set the regeneration rate before calling super().__init__
        super().__init__(base_hp=200,
                         base_min_damage=15,
                         base_max_damage=30,
                         crit_chance=0.1,
                         crit_damage=2.0,
                         armor=8,
                         level=level,
                         experience=20,
                         drop_chance=0.7,
                         regular_drop={"troll_hide": 1},
                         probability=0.01,
                         map_size=1000,
                         max_entities=100,
                         max_entities_total=200,
                         herd_probability=0.2)

    def calculate_hp(self):
        hp = super().calculate_hp()
        return min(hp + self.regeneration_rate, self.base_hp * (1 + 0.1 * (self.level - 1)))  # Cap at max HP


class Harpy(Enemy):
    type = "harpy"

    def __init__(self, level=2):
        self.evasion_chance = 0.2  # Set evasion_chance before calling super().__init__
        super().__init__(base_hp=90,
                         base_min_damage=12,
                         base_max_damage=18,
                         crit_chance=0.3,
                         crit_damage=1.6,
                         armor=1,
                         level=level,
                         experience=8,
                         drop_chance=0.6,
                         regular_drop={"feather": 3},
                         probability=0.02,
                         map_size=1000,
                         max_entities=150,
                         max_entities_total=300,
                         herd_probability=0.5)

    def roll_damage(self):
        if random.random() < self.evasion_chance:
            return {"damage": 0, "message": "evaded"}
        return super().roll_damage()


class Minotaur(Enemy):
    type = "minotaur"

    def __init__(self, level=4):
        self.charge_cooldown = 0  # Set charge_cooldown before calling super().__init__
        super().__init__(base_hp=300,
                         base_min_damage=25,
                         base_max_damage=40,
                         crit_chance=0.15,
                         crit_damage=2.2,
                         armor=10,
                         level=level,
                         experience=30,
                         drop_chance=0.8,
                         regular_drop={"minotaur_horn": 1},
                         probability=0.005,
                         map_size=1000,
                         max_entities=50,
                         max_entities_total=100,
                         herd_probability=0.1)

    def roll_damage(self):
        if self.charge_cooldown == 0:
            damage = random.randint(int(self.max_damage * 1.5), int(self.max_damage * 2.5))
            self.charge_cooldown = 3
            return {"damage": damage, "message": "charging attack"}
        else:
            damage_info = super().roll_damage()
            self.charge_cooldown -= 1
            return damage_info

class Skeleton(Enemy):
    type = "skeleton"

    def __init__(self, level=2):
        super().__init__(base_hp=50,
                         base_min_damage=5,
                         base_max_damage=10,
                         crit_chance=0.2,
                         crit_damage=1.5,
                         armor=2,
                         level=level,
                         experience=4,
                         drop_chance=0.5,
                         regular_drop={"bone": 2},
                         probability=0.04,
                         map_size=1000,
                         max_entities=300,
                         max_entities_total=600,
                         herd_probability=0.4)
        self.reassemble_chance = 0.2

    def roll_damage(self):
        damage_info = super().roll_damage()
        if self.hp <= 0 and random.random() < self.reassemble_chance:
            self.hp = self.calculate_hp() // 2  # Reassemble with half HP
            damage_info["message"] += " (skeleton reassembled)"
        return damage_info

class Wraith(Enemy):
    type = "wraith"

    def __init__(self, level=3):
        self.phase_chance = 0.3  # Set phase_chance before calling super().__init__
        super().__init__(base_hp=120,
                         base_min_damage=18,
                         base_max_damage=25,
                         crit_chance=0.25,
                         crit_damage=1.9,
                         armor=0,
                         level=level,
                         experience=15,
                         drop_chance=0.7,
                         regular_drop={"soul_essence": 1},
                         probability=0.015,
                         map_size=1000,
                         max_entities=120,
                         max_entities_total=240,
                         herd_probability=0.3)

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < self.phase_chance:
            damage_info["damage"] = int(damage_info["damage"] * 1.5)  # Wraith phases through armor
            damage_info["message"] += " (phased)"
        return damage_info

    def calculate_damage(self):
        min_damage, max_damage = super().calculate_damage()
        if random.random() < self.phase_chance:
            return int(min_damage * 1.5), int(max_damage * 1.5)  # Wraith phases through armor
        return min_damage, max_damage

class Scenery:
    def __init__(self, hp):
        self.hp = hp
        self.type = "scenery"
        self.role = "scenery"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []


class Forest(Scenery):
    type = "forest"

    def __init__(self):
        super().__init__(hp=100)
        self.type = "forest"
        self.role = "scenery"
        self.probability = 0

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "chop", "action": "/chop?amount=1"},
            {"name": "chop 10", "action": "/chop?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]


class Mountain(Scenery):
    type = "mountain"

    def __init__(self):
        super().__init__(hp=100)
        self.type = "mountain"
        self.role = "scenery"
        self.probability = 0

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "mine", "action": "/mine?amount=1"},
            {"name": "mine 10", "action": "/mine?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]


class Wall(Scenery):
    type = "wall"
    def __init__(self):
        super().__init__(hp=200)
        self.type = "wall"
        self.role = "obstacle"
        self.probability = 0


# Dictionary to store all entity types
# Automatically collect all entity classes
entity_classes = [
    cls for name, cls in inspect.getmembers(inspect.getmodule(Enemy), inspect.isclass)
    if issubclass(cls, (Enemy, Scenery)) and cls not in (Enemy, Scenery)
]

# Create the entity_types dictionary
entity_types = {}
for cls in entity_classes:
    if hasattr(cls, 'type'):
        entity_types[cls.type] = cls
    else:
        print(f"Warning: {cls.__name__} does not have a 'type' attribute.")