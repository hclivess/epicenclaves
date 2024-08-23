import random
#todo untangle this, let weapon classes define their everything

class Weapon:
    def __init__(self, level, weapon_id):
        self.type = self.__class__.__name__.lower()
        self.level = level
        self.id = weapon_id
        self.role = "right_hand"
        self._set_damage()
        self._set_attributes()

    def _set_damage(self):
        base_min, base_max = self.BASE_DAMAGE
        self.min_damage = int(base_min * random.uniform(0.8, 1.2) * self.level)
        self.max_damage = int(base_max * random.uniform(0.8, 1.2) * self.level)
        if self.max_damage <= self.min_damage:
            self.max_damage = self.min_damage + 1

    def _set_attributes(self):
        if self.RANGE == "ranged":
            self.accuracy = 50
            self.crit_dmg_pct = 200
            self.crit_chance = 100
        else:
            self.accuracy = random.randint(30, 100)
            self.crit_dmg_pct = random.randint(100, 400)
            self.crit_chance = random.randint(1, 10)

    def to_dict(self):
        return {
            "type": self.type,
            "range": self.RANGE,
            "min_damage": self.min_damage,
            "max_damage": self.max_damage,
            "role": self.role,
            "id": self.id,
            "level": self.level,
            "accuracy": self.accuracy,
            "crit_dmg_pct": self.crit_dmg_pct,
            "crit_chance": self.crit_chance
        }

class Sword(Weapon):
    BASE_DAMAGE = (7, 12)
    RANGE = "melee"

class Axe(Weapon):
    BASE_DAMAGE = (1, 3)
    RANGE = "melee"

class Bow(Weapon):
    BASE_DAMAGE = (10, 20)
    RANGE = "ranged"

class Spear(Weapon):
    BASE_DAMAGE = (6, 11)
    RANGE = "melee"

class Dagger(Weapon):
    BASE_DAMAGE = (3, 7)
    RANGE = "melee"

class Mace(Weapon):
    BASE_DAMAGE = (8, 13)
    RANGE = "melee"