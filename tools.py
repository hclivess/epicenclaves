import random

class Tool:
    def __init__(self, min_level, max_level, tool_id, level=None):
        self.type = self.__class__.__name__.lower()
        self.min_level = min_level
        self.max_level = max_level
        self.level = level if level else self.calculate_level()
        self.id = tool_id
        self.role = "tool"
        self.slot = self.SLOT
        self.accuracy = 100

    def calculate_level(self):
        return random.randint(self.min_level, self.max_level)

    def to_dict(self):
        return {
            "type": self.type,
            "level": self.level,
            "role": self.role,
            "accuracy": self.accuracy,
            "description": getattr(self, 'DESCRIPTION', 'A useful tool.'),
            "slot": self.slot,
            "id": self.id,
            "display_name": self.DISPLAY_NAME
        }

class Hatchet(Tool):
    SLOT = "right_hand"
    BASE_DAMAGE = (1, 3)  # Minimum and maximum base damage
    DESCRIPTION = "A small, versatile axe for chopping wood and other materials."
    DISPLAY_NAME = "Hatchet"

    def __init__(self, min_level, max_level, tool_id, level=None):
        super().__init__(min_level, max_level, tool_id, level)
        self.min_damage, self.max_damage = self.calculate_damage()

    def calculate_damage(self):
        if self.min_level == self.max_level:
            level_factor = 1
        else:
            level_factor = (self.level - self.min_level) / (self.max_level - self.min_level)

        base_min, base_max = self.BASE_DAMAGE
        min_damage = base_min * (1 + level_factor * (self.max_level - self.min_level))
        max_damage = base_max * (1 + level_factor * (self.max_level - self.min_level))

        # Apply reduced randomness
        variation = 0.1  # 10% variation
        min_damage = int(min_damage * (1 + random.uniform(-variation, variation)))
        max_damage = int(max_damage * (1 + random.uniform(-variation, variation)))

        # Ensure minimum damage is at least 1 and max_damage is greater than min_damage
        min_damage = max(1, min_damage)
        max_damage = max(min_damage + 1, max_damage)

        return min_damage, max_damage

    def to_dict(self):
        tool_dict = super().to_dict()
        tool_dict.update({
            "min_damage": self.min_damage,
            "max_damage": self.max_damage
        })
        return tool_dict

class Pickaxe(Tool):
    SLOT = "right_hand"
    BASE_DAMAGE = (1, 3)  # Minimum and maximum base damage
    DESCRIPTION = "A small, versatile pickaxe for mining ores."
    DISPLAY_NAME = "Pickaxe"

    def __init__(self, min_level, max_level, tool_id, level=None):
        super().__init__(min_level, max_level, tool_id, level)
        self.min_damage, self.max_damage = self.calculate_damage()

    def calculate_damage(self):
        if self.min_level == self.max_level:
            level_factor = 1
        else:
            level_factor = (self.level - self.min_level) / (self.max_level - self.min_level)

        base_min, base_max = self.BASE_DAMAGE
        min_damage = base_min * (1 + level_factor * (self.max_level - self.min_level))
        max_damage = base_max * (1 + level_factor * (self.max_level - self.min_level))

        # Apply reduced randomness
        variation = 0.1  # 10% variation
        min_damage = int(min_damage * (1 + random.uniform(-variation, variation)))
        max_damage = int(max_damage * (1 + random.uniform(-variation, variation)))

        # Ensure minimum damage is at least 1 and max_damage is greater than min_damage
        min_damage = max(1, min_damage)
        max_damage = max(min_damage + 1, max_damage)

        return min_damage, max_damage

    def to_dict(self):
        tool_dict = super().to_dict()
        tool_dict.update({
            "min_damage": self.min_damage,
            "max_damage": self.max_damage
        })
        return tool_dict