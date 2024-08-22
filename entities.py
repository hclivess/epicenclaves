import random


class Enemy:
    def __init__(self,
                 hp,
                 armor,
                 role="enemy",
                 level=1,
                 min_damage=0,
                 max_damage=2,
                 crit_chance=0.0,
                 crit_damage=0,
                 alive=True,
                 kill_chance=0.01,
                 experience=1,
                 regular_drop=None,
                 drop_chance=0.1,
                 probability=0.01,
                 size=101,
                 max_entities=None,
                 max_entities_total=None,
                 herd_probability=0.5):
        if regular_drop is None:
            regular_drop = {}

        self.hp = hp
        self.armor = armor
        self.alive = alive
        self.level = level
        self.kill_chance = kill_chance
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.crit_chance = crit_chance
        self.crit_damage = crit_damage
        self.role = role
        self.experience = experience
        self.regular_drop = regular_drop
        self.drop_chance = drop_chance
        self.probability = probability
        self.size = size
        self.max_entities = max_entities
        self.max_entities_total = max_entities_total
        self.herd_probability = herd_probability

    def roll_damage(self):
        damage = random.randint(self.min_damage, self.max_damage)
        message = "normal hit"
        if random.random() < self.crit_chance:
            damage = self.crit_damage
            message = "critical hit"
        return {"damage": damage, "message": message}

class Valenthis(Enemy):
    type = "valenthis"

    def __init__(self):
        super().__init__(hp=350,
                         min_damage=25,
                         max_damage=25,
                         crit_chance=0.4,
                         crit_damage=300,
                         armor=0,
                         level=1,
                         experience=100,
                         drop_chance=0.4,
                         regular_drop={"bismuth": 50},
                         probability=0.001,
                         size=200,
                         max_entities=1,
                         max_entities_total=1,
                         herd_probability=1)

class Boar(Enemy):
    type = "boar"

    def __init__(self):
        super().__init__(hp=30,
                         min_damage=1,
                         max_damage=1,
                         crit_chance=0.1,
                         crit_damage=3,
                         armor=0,
                         level=1,
                         experience=1,
                         drop_chance=0.1,
                         regular_drop={"food": 1},
                         probability=0.05,
                         size=200,
                         max_entities=50,
                         max_entities_total=100,
                         herd_probability=0.7)


class Wolf(Enemy):
    type = "wolf"

    def __init__(self):
        super().__init__(hp=60,
                         min_damage=1,
                         max_damage=3,
                         crit_chance=0.25,
                         crit_damage=5,
                         armor=0,
                         level=1,
                         experience=2,
                         drop_chance=0.15,
                         regular_drop={"food": 1},
                         probability=0.03,
                         size=200,
                         max_entities=30,
                         max_entities_total=60,
                         herd_probability=0.8)


class Goblin(Enemy):
    type = "goblin"

    def __init__(self):
        super().__init__(hp=40,
                         min_damage=2,
                         max_damage=5,
                         crit_chance=0.15,
                         crit_damage=8,
                         armor=1,
                         level=1,
                         experience=3,
                         drop_chance=0.2,
                         regular_drop={"gold": 5},
                         probability=0.02,
                         size=200,
                         max_entities=20,
                         max_entities_total=40,
                         herd_probability=0.6)


class Specter(Enemy):
    type = "specter"

    def __init__(self):
        super().__init__(hp=80,
                         min_damage=5,
                         max_damage=10,
                         crit_chance=0.3,
                         crit_damage=20,
                         armor=0,
                         level=2,
                         experience=10,
                         drop_chance=0.3,
                         regular_drop={"ectoplasm": 1},
                         probability=0.01,
                         size=200,
                         max_entities=10,
                         max_entities_total=20,
                         herd_probability=0.3)

    def roll_damage(self):
        damage = super().roll_damage()
        if damage["message"] == "critical hit":
            # Specters drain health on critical hits
            self.hp += damage["damage"] // 2
        return damage


class DragonWhelp(Enemy):
    type = "dragon_whelp"

    def __init__(self):
        super().__init__(hp=150,
                         min_damage=10,
                         max_damage=20,
                         crit_chance=0.2,
                         crit_damage=40,
                         armor=5,
                         level=3,
                         experience=25,
                         drop_chance=0.5,
                         regular_drop={"dragon_scale": 1},
                         probability=0.005,
                         size=200,
                         max_entities=5,
                         max_entities_total=10,
                         herd_probability=0.2)
        self.breath_attack_cooldown = 0

    def roll_damage(self):
        if self.breath_attack_cooldown == 0:
            # Use breath attack
            damage = random.randint(30, 50)
            self.breath_attack_cooldown = 3
            return {"damage": damage, "message": "breath attack"}
        else:
            # Normal attack
            damage = super().roll_damage()
            self.breath_attack_cooldown -= 1
            return damage

class Scenery:
    def __init__(self, hp):
        self.hp = hp
        self.type = "scenery"
        self.role = "scenery"


class Forest(Scenery):
    type = "Forest"

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