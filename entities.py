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
        return random.randint(self.min_damage, self.max_damage)


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


class Scenery:
    def __init__(self, hp):
        self.hp = hp
        self.type = "scenery"
        self.role = "scenery"


class Tree(Scenery):
    def __init__(self):
        super().__init__(hp=100)
        self.type = "forest"
        self.role = "scenery"


class Wall(Scenery):
    def __init__(self):
        super().__init__(hp=200)
        self.type = "wall"
        self.role = "obstacle"
