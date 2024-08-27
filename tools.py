import random

class Tool:
    def __init__(self, level=1):
        self.type = self.__class__.__name__.lower()
        self.level = level
        self.slot = self.SLOT
        self.role = "tool"
        self.slot = self.SLOT
        self.accuracy = 100

    def to_dict(self):
        return {
            "type": self.type,  # This is now lowercase, matching Armor and Weapon classes
            "level": self.level,
            "role": self.role,
            "accuracy": self.accuracy,
            "description": getattr(self, 'DESCRIPTION', 'A useful tool.')
        }

class Hatchet(Tool):
    SLOT = "right_hand"
    BASE_DAMAGE = (1, 3)  # Minimum and maximum base damage
    DESCRIPTION = "A small, versatile axe for chopping wood and other materials."

    def __init__(self, level=1):
        super().__init__(level)
        self.min_damage, self.max_damage = self.calculate_damage()

    def calculate_damage(self):
        min_damage = max(1, self.BASE_DAMAGE[0] + self.level - 1)
        max_damage = max(min_damage, self.BASE_DAMAGE[1] + self.level - 1)
        return min_damage, max_damage

    def to_dict(self):
        return {
            "type": self.type,
            "level": self.level,
            "role": self.role,
            "accuracy": self.accuracy,
            "description": getattr(self, 'DESCRIPTION', 'A useful tool.'),
            "slot": self.slot
        }