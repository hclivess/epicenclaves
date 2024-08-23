import random

class Tool:
    def __init__(self, level=1):
        self.level = level
        self.slot = "right_hand"  # Default slot for tools
        self.accuracy = 100  # Default accuracy

    def to_dict(self):
        return {
            "type": self.__class__.__name__,
            "class": getattr(self, 'CLASS', 'tool'),
            "level": self.level,
            "slot": self.slot,
            "accuracy": self.accuracy,
            "description": getattr(self, 'DESCRIPTION', 'A useful tool.')
        }

class Hatchet(Tool):
    BASE_DAMAGE = (1, 3)  # Minimum and maximum base damage
    CLASS = "tool"
    DESCRIPTION = "A small, sharp axe useful for chopping wood and self-defense."

    def __init__(self, level=1):
        super().__init__(level)
        self.min_damage, self.max_damage = self.calculate_damage()

    def calculate_damage(self):
        min_damage = max(1, self.BASE_DAMAGE[0] + self.level - 1)
        max_damage = max(min_damage, self.BASE_DAMAGE[1] + self.level - 1)
        return min_damage, max_damage

    def to_dict(self):
        tool_dict = super().to_dict()
        tool_dict.update({
            "min_damage": self.min_damage,
            "max_damage": self.max_damage,
        })
        return tool_dict