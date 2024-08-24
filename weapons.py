import random
import math


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
        log_factor = math.log(self.level + 1, 2)  # +1 to avoid log(0)

        self.min_damage = int(base_min * random.uniform(0.8, 1.2) * log_factor * self.level)
        self.max_damage = int(base_max * random.uniform(0.8, 1.2) * log_factor * self.level)

        if self.max_damage <= self.min_damage:
            self.max_damage = self.min_damage + 1

    def _set_attributes(self):
        log_factor = math.log(self.level + 1, 2)  # +1 to avoid log(0)

        self.accuracy = int(random.randint(self.MIN_ACCURACY, self.MAX_ACCURACY) * log_factor)
        self.crit_dmg_pct = int(random.randint(self.MIN_CRIT_DMG, self.MAX_CRIT_DMG) * log_factor)
        self.crit_chance = int(random.randint(self.MIN_CRIT_CHANCE, self.MAX_CRIT_CHANCE) * log_factor)

        # Ensure attributes don't exceed their maximum values
        self.accuracy = min(self.accuracy, self.MAX_ACCURACY)
        self.crit_dmg_pct = min(self.crit_dmg_pct, self.MAX_CRIT_DMG)
        self.crit_chance = min(self.crit_chance, self.MAX_CRIT_CHANCE)

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
    MIN_ACCURACY = 70
    MAX_ACCURACY = 90
    MIN_CRIT_DMG = 150
    MAX_CRIT_DMG = 250
    MIN_CRIT_CHANCE = 5
    MAX_CRIT_CHANCE = 10

class Bow(Weapon):
    BASE_DAMAGE = (1, 11)
    RANGE = "ranged"
    MIN_ACCURACY = 40
    MAX_ACCURACY = 60
    MIN_CRIT_DMG = 175
    MAX_CRIT_DMG = 225
    MIN_CRIT_CHANCE = 8
    MAX_CRIT_CHANCE = 12

class Spear(Weapon):
    BASE_DAMAGE = (6, 11)
    RANGE = "melee"
    MIN_ACCURACY = 75
    MAX_ACCURACY = 95
    MIN_CRIT_DMG = 125
    MAX_CRIT_DMG = 200
    MIN_CRIT_CHANCE = 3
    MAX_CRIT_CHANCE = 7

class Dagger(Weapon):
    BASE_DAMAGE = (3, 7)
    RANGE = "melee"
    MIN_ACCURACY = 80
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 200
    MAX_CRIT_DMG = 400
    MIN_CRIT_CHANCE = 10
    MAX_CRIT_CHANCE = 20

class Mace(Weapon):
    BASE_DAMAGE = (8, 13)
    RANGE = "melee"
    MIN_ACCURACY = 60
    MAX_ACCURACY = 80
    MIN_CRIT_DMG = 175
    MAX_CRIT_DMG = 300
    MIN_CRIT_CHANCE = 4
    MAX_CRIT_CHANCE = 8