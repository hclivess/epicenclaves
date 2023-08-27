import random


class Enemy:
    def __init__(self, hp, armor, role="enemy", min_damage=0, max_damage=2, alive=True, kill_chance=0.01):
        self.hp = hp
        self.armor = armor
        self.alive = alive
        self.kill_chance = kill_chance
        self.min_damage = min_damage
        self.max_damage = max_damage
        self.role = role

    def roll_damage(self):
        return random.randint(self.min_damage, self.max_damage)


class Boar(Enemy):
    def __init__(self):
        super().__init__(hp=100, max_damage=1, armor=0)
        self.type = "boar"


class Scenery:
    def __init__(self, hp):
        self.hp = hp
        self.type = "forest"
        self.role = "scenery"


class Tree(Scenery):
    def __init__(self):
        super().__init__(hp=100)
