import random
import math

class Armor:
    def __init__(self, max_level, armor_id, level):
        self.type = self.__class__.__name__.lower()
        self.slot = self.SLOT
        self.max_level = max_level
        self.level =  self._generate_level() if not level else level
        self.id = armor_id
        self.role = "armor"
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

    def _set_attributes(self):
        # Calculate protection using logarithmic scaling
        if self.max_level == 1:
            log_factor = 1
        else:
            log_factor = math.log(self.level, 2) / math.log(self.max_level, 2)
        base_protection = int(self.BASE_PROTECTION * (1 + log_factor * (self.max_level - 1)) * random.uniform(0.8, 1.2))
        self.protection = max(1, base_protection)  # Ensure minimum protection is 1

        # Calculate durability using logarithmic scaling
        min_durability = 30
        max_durability = 50 * self.max_level
        self.durability = self._log_scale(min_durability, max_durability)
        self.max_durability = self.durability

        # Calculate efficiency using logarithmic scaling
        self.efficiency = self._log_scale(20, 100)

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