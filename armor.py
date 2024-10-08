import random
import math
from backend import calculate_level


class Armor:
    def __init__(self, min_level, max_level, armor_id, level=None):
        self.type = self.__class__.__name__.lower()
        self.min_level = min_level
        self.max_level = max_level
        self.level = level if level else random.randint(min_level, max_level)
        self.id = armor_id
        self.role = "armor"
        self.slot = self.SLOT
        self._set_attributes()

    def _set_attributes(self):
        # Adjust the scaling factor
        scaling_factor = 1.11 ** (self.level - 1)  # Slightly reduced from 1.12

        # Calculate potential protection range with 15% decrease from the previous 30% increase
        min_potential = self.BASE_PROTECTION * scaling_factor * 1.105  # 1.3 * 0.85 = 1.105
        max_potential = self.BASE_PROTECTION * scaling_factor * 1.445  # 1.7 * 0.85 = 1.445

        # Use logarithmic distribution for protection
        self.protection = calculate_level(int(min_potential), int(max_potential))

        # Occasional chance for exceptional items
        if random.random() < 0.01:  # 1% chance
            exceptional_boost = random.uniform(1.15, 1.35)  # Slightly reduced from (1.2, 1.4)
            self.protection = int(self.protection * exceptional_boost)

        # Calculate durability and efficiency (unchanged)
        level_factor = (self.level - self.min_level) / max(1, (self.max_level - self.min_level))

        min_durability = 30
        max_durability = 50 * self.max_level
        self.durability = min_durability + int((max_durability - min_durability) * level_factor)
        self.max_durability = self.durability

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
            "level": self.level,
            "display_name": self.DISPLAY_NAME
        }

class Helmet(Armor):
    DESCRIPTION = "Protective headgear that reduces damage taken to the head."
    SLOT = "head"
    BASE_PROTECTION = 2
    DISPLAY_NAME = "Helmet"

class Chestplate(Armor):
    DESCRIPTION = "Armor that covers the torso and provides substantial protection."
    SLOT = "body"
    BASE_PROTECTION = 3
    DISPLAY_NAME = "Chestplate"

class Gauntlets(Armor):
    DESCRIPTION = "Armored gloves that protect the hands and forearms."
    SLOT = "arms"
    BASE_PROTECTION = 1
    DISPLAY_NAME = "Gauntlets"

class Leggings(Armor):
    DESCRIPTION = "Armor that covers the legs, providing mobility and protection."
    SLOT = "legs"
    BASE_PROTECTION = 2
    DISPLAY_NAME = "Leggings"

class Boots(Armor):
    DESCRIPTION = "Sturdy footwear that protects the feet and enhances movement."
    SLOT = "feet"
    BASE_PROTECTION = 1
    DISPLAY_NAME = "Boots"