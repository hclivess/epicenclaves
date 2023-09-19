import random


class Enemy:
    def __init__(self,
                 hp,
                 armor,
                 role="enemy",
                 min_damage=0,
                 max_damage=2,
                 crit_chance=0.0,
                 crit_damage=0,
                 alive=True,
                 kill_chance=0.01,
                 exp_gain=1,
                 regular_drop=None,
                 drop_chance=0.1):
        if regular_drop is None:
            regular_drop = {}

        self.hp = hp
        self.armor = armor
        self.alive = alive
        self.kill_chance = kill_chance
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.crit_chance = crit_chance
        self.crit_damage = crit_damage
        self.role = role
        self.exp_gain = exp_gain
        self.regular_drop = regular_drop
        self.drop_chance = drop_chance

    def roll_damage(self):
        damage = random.randint(self.min_damage, self.max_damage)
        message = "normal hit"
        if random.random() < self.crit_chance:
            damage = self.crit_damage
            message = "critical hit"
        return {"damage": damage, "message": message}


class Boar(Enemy):
    type = "boar"

    def __init__(self):
        super().__init__(hp=20,
                         min_damage=1,
                         max_damage=1,
                         crit_chance=0.1,
                         crit_damage=3,
                         armor=0,
                         exp_gain=1,
                         drop_chance=0.1,
                         regular_drop={"food": 1})


class Wolf(Enemy):
    type = "wolf"

    def __init__(self):
        super().__init__(hp=40,
                         min_damage=1,
                         max_damage=3,
                         crit_chance=0.25,
                         crit_damage=5,
                         armor=0,
                         exp_gain=2,
                         drop_chance=0.15,
                         regular_drop={"food": 1})


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


class Mountain(Scenery):
    type = "Mountain"

    def __init__(self):
        super().__init__(hp=100)
        self.type = "mountain"
        self.role = "scenery"


class Wall(Scenery):
    def __init__(self):
        super().__init__(hp=200)
        self.type = "wall"
        self.role = "obstacle"
