import random
import math
from backend import calculate_level

class Weapon:
    def __init__(self, min_level, max_level, weapon_id, level=None):
        self.type = self.__class__.__name__.lower()
        self.min_level = min_level
        self.max_level = max_level
        self.level = level if level else random.randint(min_level, max_level)
        self.id = weapon_id
        self.role = "weapon"
        self.slot = self.SLOT
        self._set_damage()
        self._set_attributes()

    def _set_damage(self):
        base_min, base_max = self.BASE_DAMAGE

        # Reduce the scaling factor to decrease overall damage
        scaling_factor = 1.09 ** (self.level - 1)  # Reduced from 1.15

        # Calculate potential damage range with 40% reduction
        min_potential = base_min * scaling_factor * 0.6
        max_potential = base_max * scaling_factor * 0.9  # Reduced maximum potential

        # Use logarithmic distribution for damage
        self.min_damage = calculate_level(int(min_potential), int(max_potential))
        self.max_damage = calculate_level(self.min_damage + 1, int(max_potential))

        # Occasional chance for exceptional items (slightly reduced boost)
        if random.random() < 0.01:  # 1% chance
            exceptional_boost = random.uniform(1.1, 1.3)  # Reduced from (1.2, 1.5)
            self.min_damage = int(self.min_damage * exceptional_boost)
            self.max_damage = int(self.max_damage * exceptional_boost)

    def _set_attributes(self):
        level_factor = (self.level - self.min_level) / max(1, (self.max_level - self.min_level))

        # Linear scaling for attributes
        self.accuracy = self.MIN_ACCURACY + int((self.MAX_ACCURACY - self.MIN_ACCURACY) * level_factor)
        self.crit_dmg_pct = self.MIN_CRIT_DMG + int((self.MAX_CRIT_DMG - self.MIN_CRIT_DMG) * level_factor)
        self.crit_chance = self.MIN_CRIT_CHANCE + int((self.MAX_CRIT_CHANCE - self.MIN_CRIT_CHANCE) * level_factor)

        if self.RANGE == "ranged":
            self.crit_chance = min(self.crit_chance * 2, 100)

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
            "slot": self.slot,
            "display_name": self.DISPLAY_NAME
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
    DISPLAY_NAME = "Sword"

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
    DISPLAY_NAME = "Bow"

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
    DISPLAY_NAME = "Spear"

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
    DISPLAY_NAME = "Dagger"

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
    DISPLAY_NAME = "Mace"

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
    DISPLAY_NAME = "Axe"

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
    DISPLAY_NAME = "Crossbow"

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
    DISPLAY_NAME = "Rapier"

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
    DISPLAY_NAME = "War Hammer"

class Sling(Weapon):
    SLOT = "right_hand"
    DESCRIPTION = "A simple ranged weapon with low damage but extremely high critical potential."
    BASE_DAMAGE = (1, 4)
    RANGE = "ranged"
    MIN_ACCURACY = 40
    MAX_ACCURACY = 80
    MIN_CRIT_DMG = 300
    MAX_CRIT_DMG = 600
    MIN_CRIT_CHANCE = 14
    MAX_CRIT_CHANCE = 24
    DISPLAY_NAME = "Sling"

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
    DISPLAY_NAME = "Katana"

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
    DISPLAY_NAME = "Throwing Knives"

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
    DISPLAY_NAME = "Halberd"

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
    DISPLAY_NAME = "Scythe"

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
    DISPLAY_NAME = "Chakram"