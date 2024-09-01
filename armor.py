import random
import math
from backend import calculate_level

class Armor:
    def __init__(self, min_level, max_level, armor_id, level=None):
        self.type = self.__class__.__name__.lower()
        self.slot = self.SLOT
        self.min_level = min_level
        self.max_level = max_level
        self.level = level if level else calculate_level(min_level, max_level)
        self.id = armor_id
        self.role = "armor"
        self._set_attributes()

    def _set_attributes(self):
        # Handle the case where min_level and max_level are the same
        if self.min_level == self.max_level:
            level_factor = 1
        else:
            level_factor = (self.level - self.min_level) / (self.max_level - self.min_level)

        # Calculate protection
        base_protection = int(self.BASE_PROTECTION * (1 + level_factor * (self.max_level - self.min_level)) * random.uniform(0.8, 1.2))
        self.protection = max(1, base_protection)  # Ensure minimum protection is 1

        # Calculate durability
        min_durability = 30
        max_durability = 50 * self.max_level
        self.durability = min_durability + int((max_durability - min_durability) * level_factor)
        self.max_durability = self.durability

        # Calculate efficiency
        min_efficiency = 20
        max_efficiency = 100
        self.efficiency = min_efficiency + int((max_efficiency - min_efficiency) * level_factor)

    def to_dict(self):
        return {
            "type": self.type,
            "slot": self.slot,
            "protection": self.protection,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "efficiency": self.efficiency,
            "role": self.role,
            "id": self.id,
            "level": self.level
        }

class Helmet(Armor):
    DESCRIPTION = "Protective headgear that reduces damage taken to the head."
    SLOT = "head"
    BASE_PROTECTION = 2

class Chestplate(Armor):
    DESCRIPTION = "Armor that covers the torso and provides substantial protection."
    SLOT = "body"
    BASE_PROTECTION = 3

class Gauntlets(Armor):
    DESCRIPTION = "Armored gloves that protect the hands and forearms."
    SLOT = "arms"
    BASE_PROTECTION = 1

class Leggings(Armor):
    DESCRIPTION = "Armor that covers the legs, providing mobility and protection."
    SLOT = "legs"
    BASE_PROTECTION = 2

class Boots(Armor):
    DESCRIPTION = "Sturdy footwear that protects the feet and enhances movement."
    SLOT = "feet"
    BASE_PROTECTION = 1