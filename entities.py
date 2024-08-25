import random
import math

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
                 map_size=101,
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
        return int(self.base_hp * (1 + 0.1 * (self.level - 1)))

    def calculate_damage(self):
        scaling_factor = 1 + 0.05 * (self.level - 1)  # 5% increase per level
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

class Valenthis(Enemy):
    type = "valenthis"

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
                         map_size=200,
                         max_entities=1,
                         max_entities_total=1,
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
                         map_size=200,
                         max_entities=50,
                         max_entities_total=100,
                         herd_probability=0.7)

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
                         map_size=200,
                         max_entities=30,
                         max_entities_total=60,
                         herd_probability=0.8)

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
                         map_size=200,
                         max_entities=20,
                         max_entities_total=40,
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
                         map_size=200,
                         max_entities=10,
                         max_entities_total=20,
                         herd_probability=0.3)

    def roll_damage(self):
        damage_info = super().roll_damage()
        if damage_info["message"] == "critical hit":
            # Specters drain health on critical hits
            self.hp += damage_info["damage"] // 2
        return damage_info

class DragonWhelp(Enemy):
    type = "dragon_whelp"

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
                         map_size=200,
                         max_entities=5,
                         max_entities_total=10,
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

class Scenery:
    def __init__(self, hp):
        self.hp = hp
        self.type = "scenery"
        self.role = "scenery"

class Forest(Scenery):
    type = "forest"

    def __init__(self):
        super().__init__(hp=100)
        self.type = "forest"
        self.role = "scenery"
        self.probability = 0

class Mountain(Scenery):
    type = "mountain"

    def __init__(self):
        super().__init__(hp=100)
        self.type = "mountain"
        self.role = "scenery"
        self.probability = 0

class Wall(Scenery):
    def __init__(self):
        super().__init__(hp=200)
        self.type = "wall"
        self.role = "obstacle"
        self.probability = 0