import random

class Armor:
    def __init__(self, level, armor_id):
        self.type = self.__class__.__name__.lower()
        self.slot = self.SLOT
        self.level = level
        self.id = armor_id
        self.role = "armor"
        self._set_attributes()

    def _set_attributes(self):
        # Calculate protection, ensuring it's at least 1
        base_protection = int(self.BASE_PROTECTION * random.uniform(0.8, 1.2) * self.level)
        self.protection = max(1, base_protection)  # Ensure minimum protection is 1
        self.durability = random.randint(30, 50) * self.level
        self.max_durability = self.durability
        self.efficiency = random.randint(80, 100)

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
    SLOT = "head"
    BASE_PROTECTION = 2

class Chestplate(Armor):
    SLOT = "body"
    BASE_PROTECTION = 3

class Gauntlets(Armor):
    SLOT = "arms"
    BASE_PROTECTION = 1

class Leggings(Armor):
    SLOT = "legs"
    BASE_PROTECTION = 2

class Boots(Armor):
    SLOT = "feet"
    BASE_PROTECTION = 1