import random
import math

class Weapon:
    def __init__(self, max_level, weapon_id):
        self.type = self.__class__.__name__.lower()
        self.max_level = max_level
        self.level = self._generate_level()
        self.id = weapon_id
        self.role = "right_hand"
        self._set_damage()
        self._set_attributes()

    def _generate_level(self):
        # Generate a random number between 0 and 1
        r = random.random()
        # Use logarithmic distribution to skew towards lower levels
        level = int(math.exp(r * math.log(self.max_level))) + 1
        return min(level, self.max_level)  # Ensure we don't exceed max_level

    def _log_scale(self, min_val, max_val):
        if self.level == 1:
            return min_val
        log_factor = math.log(self.level, 2) / math.log(self.max_level, 2)
        return min_val + int((max_val - min_val) * log_factor)

    def _set_damage(self):
        base_min, base_max = self.BASE_DAMAGE
        log_factor = math.log(self.level, 2) / math.log(self.max_level, 2)

        self.min_damage = int(base_min * (1 + log_factor * (self.max_level - 1)) * random.uniform(0.8, 1.2))
        self.max_damage = int(base_max * (1 + log_factor * (self.max_level - 1)) * random.uniform(0.8, 1.2))

        if self.max_damage <= self.min_damage:
            self.max_damage = self.min_damage + 1

    def _set_attributes(self):
        self.accuracy = self._log_scale(self.MIN_ACCURACY, self.MAX_ACCURACY)
        self.crit_dmg_pct = self._log_scale(self.MIN_CRIT_DMG, self.MAX_CRIT_DMG)
        self.crit_chance = self._log_scale(self.MIN_CRIT_CHANCE, self.MAX_CRIT_CHANCE)

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
    BASE_DAMAGE = (3, 7)
    RANGE = "melee"
    MIN_ACCURACY = 40
    MAX_ACCURACY = 55
    MIN_CRIT_DMG = 80
    MAX_CRIT_DMG = 130
    MIN_CRIT_CHANCE = 3
    MAX_CRIT_CHANCE = 6

class Bow(Weapon):
    BASE_DAMAGE = (1, 8)
    RANGE = "ranged"
    MIN_ACCURACY = 25
    MAX_ACCURACY = 45
    MIN_CRIT_DMG = 100
    MAX_CRIT_DMG = 150
    MIN_CRIT_CHANCE = 5
    MAX_CRIT_CHANCE = 8

class Spear(Weapon):
    BASE_DAMAGE = (4, 6)
    RANGE = "melee"
    MIN_ACCURACY = 45
    MAX_ACCURACY = 60
    MIN_CRIT_DMG = 70
    MAX_CRIT_DMG = 110
    MIN_CRIT_CHANCE = 2
    MAX_CRIT_CHANCE = 4

class Dagger(Weapon):
    BASE_DAMAGE = (2, 4)
    RANGE = "melee"
    MIN_ACCURACY = 50
    MAX_ACCURACY = 70
    MIN_CRIT_DMG = 120
    MAX_CRIT_DMG = 200
    MIN_CRIT_CHANCE = 7
    MAX_CRIT_CHANCE = 12

class Mace(Weapon):
    BASE_DAMAGE = (5, 7)
    RANGE = "melee"
    MIN_ACCURACY = 35
    MAX_ACCURACY = 50
    MIN_CRIT_DMG = 90
    MAX_CRIT_DMG = 160
    MIN_CRIT_CHANCE = 2
    MAX_CRIT_CHANCE = 5