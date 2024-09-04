import random
from typing import Dict, List, Any
import inspect

class Enemy:
    type = "enemy"
    base_hp = 100
    base_min_damage = 1
    base_max_damage = 2
    base_armor = 0
    crit_chance = 0.05
    crit_damage = 1.5
    drop_chance = 0.1
    regular_drop: Dict[str, int] = {}
    probability = 0
    map_size = 1000
    max_entities = None
    max_entities_total = None
    herd_probability = 0.5
    min_level = 1
    max_level = 100
    experience_value = 10

    def __init__(self, level: int):
        self.level = max(self.min_level, min(level, self.max_level))
        self.max_hp = self.calculate_hp()
        self.hp = self.max_hp
        self.min_damage, self.max_damage = self.calculate_damage()
        self.armor = self.calculate_armor()
        self.alive = True
        self.experience = self.calculate_experience()

    def calculate_hp(self):
        return int(self.base_hp * (1 + 0.1 * (self.level - 1)))  # 10% increase per level

    def calculate_damage(self):
        scaling_factor = 1 + 0.05 * (self.level - 1)  # 5% increase per level
        min_damage = int(self.base_min_damage * scaling_factor)
        max_damage = int(self.base_max_damage * scaling_factor)
        return min_damage, max_damage

    def calculate_armor(self):
        return self.base_armor + int(0.5 * (self.level - 1))  # 0.5 armor increase per level

    def calculate_experience(self):
        return int(self.experience_value * (1 + 0.1 * (self.level - 1)))  # 10% increase per level

    def roll_damage(self):
        damage = random.randint(self.min_damage, self.max_damage)
        message = "normal hit"
        if random.random() < self.crit_chance:
            damage = int(damage * self.crit_damage)
            message = "critical hit"
        return {"damage": damage, "message": message}

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "fight", "action": f"/fight?target={self.type}"}]

    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "level": self.level,
        }

class Boar(Enemy):
    type = "boar"
    base_hp = 35
    base_min_damage = 2
    base_max_damage = 4
    crit_chance = 0.1
    crit_damage = 1.5
    drop_chance = 0.2
    regular_drop = {"food": 1}
    probability = 0.1
    max_entities = 500
    max_entities_total = 1000
    herd_probability = 0.7
    min_level = 3
    max_level = 18
    experience_value = 10

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "hunt", "action": f"/fight?target={self.type}"}]

class Wolf(Enemy):
    type = "wolf"
    base_hp = 60
    base_min_damage = 3
    base_max_damage = 7
    crit_chance = 0.25
    crit_damage = 1.8
    drop_chance = 0.3
    regular_drop = {"wolf_pelt": 1}
    probability = 0.2
    max_entities = 300
    max_entities_total = 600
    herd_probability = 0.8
    min_level = 8
    max_level = 25
    experience_value = 15

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [{"name": "hunt", "action": f"/fight?target={self.type}"}]

class Goblin(Enemy):
    type = "goblin"
    base_hp = 45
    base_min_damage = 4
    base_max_damage = 6
    base_armor = 1
    crit_chance = 0.15
    crit_damage = 1.6
    drop_chance = 0.4
    regular_drop = {"gold": 5}
    probability = 0.24
    max_entities = 200
    max_entities_total = 400
    herd_probability = 0.5
    min_level = 5
    max_level = 22
    experience_value = 12

class Specter(Enemy):
    type = "specter"
    base_hp = 80
    base_min_damage = 10
    base_max_damage = 20
    crit_chance = 0.3
    crit_damage = 2.0
    drop_chance = 0.6
    regular_drop = {"ectoplasm": 1}
    probability = 0.24
    max_entities = 100
    max_entities_total = 200
    herd_probability = 0.3
    min_level = 20
    max_level = 50
    experience_value = 40

    def roll_damage(self):
        damage_info = super().roll_damage()
        if damage_info["message"] == "critical hit":
            # Specters drain health on critical hits
            self.hp += damage_info["damage"] // 2
        return damage_info

class Hatchling(Enemy):
    type = "hatchling"
    base_hp = 150
    base_min_damage = 15
    base_max_damage = 25
    base_armor = 5
    crit_chance = 0.2
    crit_damage = 1.8
    drop_chance = 0.8
    regular_drop = {"dragon_scale": 1}
    probability = 0.24
    max_entities = 50
    max_entities_total = 100
    herd_probability = 0.2
    min_level = 30
    max_level = 70
    experience_value = 80

    def __init__(self, level: int):
        super().__init__(level)
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

class Bandit(Enemy):
    type = "bandit"
    base_hp = 70
    base_min_damage = 8
    base_max_damage = 15
    base_armor = 2
    crit_chance = 0.2
    crit_damage = 1.7
    drop_chance = 0.5
    regular_drop = {"gold": 10}
    probability = 0.24
    max_entities = 250
    max_entities_total = 500
    herd_probability = 0.4
    min_level = 10
    max_level = 35
    experience_value = 25

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < 0.1:  # 10% chance to steal gold
            damage_info["message"] += " and stole some gold"
        return damage_info

class Troll(Enemy):
    type = "troll"
    base_hp = 200
    base_min_damage = 15
    base_max_damage = 30
    base_armor = 8
    crit_chance = 0.1
    crit_damage = 2.0
    drop_chance = 0.7
    regular_drop = {"troll_hide": 1}
    probability = 0.24
    max_entities = 100
    max_entities_total = 200
    herd_probability = 0.2
    min_level = 25
    max_level = 60
    experience_value = 70
    regeneration_rate = 5

    def calculate_hp(self):
        hp = super().calculate_hp()
        return hp + self.regeneration_rate * (self.level - 1)  # Additional HP from regeneration

class Harpy(Enemy):
    type = "harpy"
    base_hp = 90
    base_min_damage = 12
    base_max_damage = 18
    base_armor = 1
    crit_chance = 0.3
    crit_damage = 1.6
    drop_chance = 0.6
    regular_drop = {"feather": 3}
    probability = 0.24
    max_entities = 150
    max_entities_total = 300
    herd_probability = 0.5
    min_level = 15
    max_level = 45
    experience_value = 35
    evasion_chance = 0.2

    def roll_damage(self):
        if random.random() < self.evasion_chance:
            return {"damage": 0, "message": "evaded"}
        return super().roll_damage()

class Orc(Enemy):
    type = "orc"
    base_hp = 120
    base_min_damage = 10
    base_max_damage = 18
    base_armor = 4
    crit_chance = 0.12
    crit_damage = 1.8
    drop_chance = 0.6
    regular_drop = {"orc_tusk": 1}
    probability = 0.24
    max_entities = 150
    max_entities_total = 300
    herd_probability = 0.4
    min_level = 20
    max_level = 50
    experience_value = 50

class Spider(Enemy):
    type = "spider"
    base_hp = 65
    base_min_damage = 6
    base_max_damage = 12
    base_armor = 2
    crit_chance = 0.18
    crit_damage = 1.7
    drop_chance = 0.5
    regular_drop = {"spider_silk": 1, "venom_sac": 1}
    probability = 0.24
    max_entities = 180
    max_entities_total = 360
    herd_probability = 0.6
    min_level = 12
    max_level = 40
    experience_value = 30
    poison_chance = 0.15
    poison_duration = 3
    poison_damage = 2

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < self.poison_chance:
            damage_info["message"] += f" and poisoned for {self.poison_damage} damage over {self.poison_duration} turns"
        return damage_info

class Rat(Enemy):
    type = "rat"
    base_hp = 20
    base_min_damage = 1
    base_max_damage = 2
    crit_chance = 0.05
    crit_damage = 1.3
    drop_chance = 0.2
    regular_drop = {"rat_tail": 1}
    probability = 0.24
    max_entities = 1000
    max_entities_total = 2000
    herd_probability = 0.8
    min_level = 1
    max_level = 10
    experience_value = 5

class Minotaur(Enemy):
    type = "minotaur"
    base_hp = 300
    base_min_damage = 25
    base_max_damage = 40
    base_armor = 10
    crit_chance = 0.15
    crit_damage = 2.2
    drop_chance = 0.8
    regular_drop = {"minotaur_horn": 1}
    probability = 0.24
    max_entities = 50
    max_entities_total = 100
    herd_probability = 0.1
    min_level = 35
    max_level = 80
    experience_value = 100

    def __init__(self, level: int):
        super().__init__(level)
        self.charge_cooldown = 0

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
    base_hp = 50
    base_min_damage = 5
    base_max_damage = 10
    base_armor = 2
    crit_chance = 0.2
    crit_damage = 1.5
    drop_chance = 0.5
    regular_drop = {"bone": 2}
    probability = 0.24
    max_entities = 300
    max_entities_total = 600
    herd_probability = 0.4
    min_level = 5
    max_level = 30
    experience_value = 20
    reassemble_chance = 0.2

    def roll_damage(self):
        damage_info = super().roll_damage()
        if self.hp <= 0 and random.random() < self.reassemble_chance:
            self.hp = self.calculate_hp() // 2  # Reassemble with half HP
            damage_info["message"] += " (skeleton reassembled)"
        return damage_info

class Wraith(Enemy):
    type = "wraith"
    base_hp = 120
    base_min_damage = 18
    base_max_damage = 25
    crit_chance = 0.25
    crit_damage = 1.9
    drop_chance = 0.7
    regular_drop = {"soul_essence": 1}
    probability = 0.24
    max_entities = 120
    max_entities_total = 240
    herd_probability = 0.3
    min_level = 30
    max_level = 70
    experience_value = 75
    phase_chance = 0.3

    def roll_damage(self):
        damage_info = super().roll_damage()
        if random.random() < self.phase_chance:
            damage_info["damage"] = int(damage_info["damage"] * 1.5)  # Wraith phases through armor
            damage_info["message"] += " (phased)"
        return damage_info

class Dragon(Enemy):
    type = "dragon"
    base_hp = 500
    base_min_damage = 40
    base_max_damage = 60
    base_armor = 20
    crit_chance = 0.2
    crit_damage = 2.5
    drop_chance = 1.0
    regular_drop = {"dragon_scale": 3, "dragon_tooth": 1}
    probability = 0.12
    max_entities = 10
    max_entities_total = 20
    herd_probability = 0
    min_level = 60
    max_level = 100
    experience_value = 500

    def __init__(self, level: int):
        super().__init__(level)
        self.breath_attack_cooldown = 0

    def roll_damage(self):
        if self.breath_attack_cooldown == 0:
            # Use breath attack
            damage = random.randint(int(self.max_damage * 2), int(self.max_damage * 3))
            self.breath_attack_cooldown = 3
            return {"damage": damage, "message": "devastating breath attack"}
        else:
            # Normal attack
            damage_info = super().roll_damage()
            self.breath_attack_cooldown -= 1
            return damage_info

class Scenery:
    probability = 0

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type
        }

class Forest(Scenery):
    type = "forest"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "chop", "action": "/chop?amount=1"},
            {"name": "chop 10", "action": "/chop?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Mountain(Scenery):
    type = "mountain"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "mine", "action": "/mine?amount=1"},
            {"name": "mine 10", "action": "/mine?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Wall(Scenery):
    type = "wall"

def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)])

# Automatically collect all entity classes
entity_classes = get_all_subclasses(Enemy) | get_all_subclasses(Scenery)

# Create the entity_types dictionary
entity_types = {}
for cls in entity_classes:
    if hasattr(cls, 'type'):
        entity_types[cls.type] = cls
    else:
        print(f"Warning: {cls.__name__} does not have a 'type' attribute.")

# Optionally, you can print out the collected entity types for verification
print("Collected entity types:")
for entity_type, entity_class in entity_types.items():
    print(f"{entity_type}: {entity_class.__name__}")