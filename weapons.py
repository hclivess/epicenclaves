import random
import math

class Weapon:
    def __init__(self, max_level, weapon_id, level=None):
        self.type = self.__class__.__name__.lower()
        self.max_level = max_level
        self.level = self._generate_level() if not level else level
        self.id = weapon_id
        self.role = "weapon"
        self.slot = self.SLOT
        self._set_damage()
        self._set_attributes()

    def _generate_level(self):
        r = random.random()
        level = int(math.exp(r * math.log(self.max_level))) + 1
        return min(level, self.max_level)

    def _log_scale(self, min_val, max_val):
        if self.level == 1:
            return min_val
        log_factor = math.log(self.level, 2) / math.log(self.max_level, 2)
        return min_val + int((max_val - min_val) * log_factor)

    def _set_damage(self):
        base_min, base_max = self.BASE_DAMAGE

        if self.max_level == 1:
            log_factor = 1
        else:
            log_factor = math.log(self.level, 2) / math.log(self.max_level, 2)

        self.min_damage = int(base_min * (1 + log_factor * (self.max_level - 1)) * random.uniform(0.8, 1.2))
        self.max_damage = int(base_max * (1 + log_factor * (self.max_level - 1)) * random.uniform(0.8, 1.2))

        if self.max_damage <= self.min_damage:
            self.max_damage = self.min_damage + 1

    def _set_attributes(self):
        self.accuracy = self._log_scale(self.MIN_ACCURACY, self.MAX_ACCURACY)
        self.crit_dmg_pct = self._log_scale(self.MIN_CRIT_DMG, self.MAX_CRIT_DMG)
        self.crit_chance = self._log_scale(self.MIN_CRIT_CHANCE, self.MAX_CRIT_CHANCE)
        if self.RANGE == "ranged":
            self.crit_chance = min(self.crit_chance * 2, 100)  # Double crit chance for ranged weapons, capped at 100%

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
            "crit_chance": self.crit_chance,
            "slot": self.slot
        }

class Sword(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A versatile melee weapon with balanced stats."
    BASE_DAMAGE = (3, 7)
    RANGE = "melee"
    MIN_ACCURACY = 40
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 80
    MAX_CRIT_DMG = 130
    MIN_CRIT_CHANCE = 3
    MAX_CRIT_CHANCE = 6

class Bow(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A ranged weapon with high critical chance and damage."
    BASE_DAMAGE = (4, 7)
    RANGE = "ranged"
    MIN_ACCURACY = 35
    MAX_ACCURACY = 60
    MIN_CRIT_DMG = 100
    MAX_CRIT_DMG = 150
    MIN_CRIT_CHANCE = 10
    MAX_CRIT_CHANCE = 16

class Spear(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A melee weapon with good reach and high accuracy."
    BASE_DAMAGE = (4, 6)
    RANGE = "melee"
    MIN_ACCURACY = 45
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 70
    MAX_CRIT_DMG = 110
    MIN_CRIT_CHANCE = 2
    MAX_CRIT_CHANCE = 4

class Dagger(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A fast melee weapon with high critical damage and chance."
    BASE_DAMAGE = (2, 5)
    RANGE = "melee"
    MIN_ACCURACY = 50
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 120
    MAX_CRIT_DMG = 200
    MIN_CRIT_CHANCE = 8
    MAX_CRIT_CHANCE = 13

class Mace(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A heavy melee weapon with good damage and critical potential."
    BASE_DAMAGE = (4, 7)
    RANGE = "melee"
    MIN_ACCURACY = 35
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 90
    MAX_CRIT_DMG = 160
    MIN_CRIT_CHANCE = 2
    MAX_CRIT_CHANCE = 5

class Axe(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A powerful melee weapon with high damage and critical damage."
    BASE_DAMAGE = (5, 8)
    RANGE = "melee"
    MIN_ACCURACY = 30
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 100
    MAX_CRIT_DMG = 180
    MIN_CRIT_CHANCE = 3
    MAX_CRIT_CHANCE = 7

class Crossbow(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A strong ranged weapon with high base damage and good critical stats."
    BASE_DAMAGE = (7, 10)
    RANGE = "ranged"
    MIN_ACCURACY = 35
    MAX_ACCURACY = 55
    MIN_CRIT_DMG = 110
    MAX_CRIT_DMG = 170
    MIN_CRIT_CHANCE = 8
    MAX_CRIT_CHANCE = 14

class Rapier(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A precise melee weapon with high accuracy and good critical chance."
    BASE_DAMAGE = (2, 6)
    RANGE = "melee"
    MIN_ACCURACY = 55
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 90
    MAX_CRIT_DMG = 140
    MIN_CRIT_CHANCE = 6
    MAX_CRIT_CHANCE = 10

class WarHammer(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A massive melee weapon with the highest base damage and critical damage."
    BASE_DAMAGE = (7, 10)
    RANGE = "melee"
    MIN_ACCURACY = 25
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 130
    MAX_CRIT_DMG = 220
    MIN_CRIT_CHANCE = 2
    MAX_CRIT_CHANCE = 4

class Sling(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A simple ranged weapon with low damage but extremely high critical potential."
    BASE_DAMAGE = (1, 4)
    RANGE = "ranged"
    MIN_ACCURACY = 20
    MAX_ACCURACY = 40
    MIN_CRIT_DMG = 150
    MAX_CRIT_DMG = 250
    MIN_CRIT_CHANCE = 14
    MAX_CRIT_CHANCE = 24

class Katana(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "An elegant melee weapon with high damage and good critical stats."
    BASE_DAMAGE = (4, 8)
    RANGE = "melee"
    MIN_ACCURACY = 45
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 110
    MAX_CRIT_DMG = 190
    MIN_CRIT_CHANCE = 5
    MAX_CRIT_CHANCE = 9

class ThrowingKnives(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "Ranged weapons with moderate damage but very high critical chance."
    BASE_DAMAGE = (2, 4)
    RANGE = "ranged"
    MIN_ACCURACY = 40
    MAX_ACCURACY = 60
    MIN_CRIT_DMG = 130
    MAX_CRIT_DMG = 210
    MIN_CRIT_CHANCE = 16
    MAX_CRIT_CHANCE = 28

class Halberd(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A versatile melee weapon with good damage and balanced stats."
    BASE_DAMAGE = (5, 9)
    RANGE = "melee"
    MIN_ACCURACY = 35
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 95
    MAX_CRIT_DMG = 155
    MIN_CRIT_CHANCE = 3
    MAX_CRIT_CHANCE = 6

class Scythe(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A menacing melee weapon with high damage and critical damage."
    BASE_DAMAGE = (6, 10)
    RANGE = "melee"
    MIN_ACCURACY = 30
    MAX_ACCURACY = 100
    MIN_CRIT_DMG = 120
    MAX_CRIT_DMG = 200
    MIN_CRIT_CHANCE = 4
    MAX_CRIT_CHANCE = 8

class Chakram(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A unique ranged weapon with moderate damage and high critical chance."
    BASE_DAMAGE = (4, 7)
    RANGE = "ranged"
    MIN_ACCURACY = 45
    MAX_ACCURACY = 70
    MIN_CRIT_DMG = 90
    MAX_CRIT_DMG = 150
    MIN_CRIT_CHANCE = 8
    MAX_CRIT_CHANCE = 16