from typing import Dict

class Building:
    def __init__(self, building_id: int):
        self.type = self.__class__.__name__.lower()
        self.id = building_id
        self.role = "building"

    @staticmethod
    def format_cost(cost: Dict[str, int]) -> str:
        emoji_map = {"wood": "🪵", "bismuth": "🪨", "gold": "💰"}
        return " ".join(f"{emoji_map.get(resource, resource)}{amount}" for resource, amount in cost.items())

    def to_dict(self):
        return {
            "type": self.type,
            "display_name": self.DISPLAY_NAME,
            "description": self.DESCRIPTION,
            "role": self.role,
            "id": self.id,
            "cost": self.COST,
            "formatted_cost": self.format_cost(self.COST),
            "image_source": self.IMAGE_SOURCE
        }

class House(Building):
    DISPLAY_NAME = "House"
    DESCRIPTION = "Increases population limit by 10."
    COST = {"wood": 50, "bismuth": 20}
    IMAGE_SOURCE = "house.png"

class Inn(Building):
    DISPLAY_NAME = "Inn"
    DESCRIPTION = "Allows user to rest and restore health."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "inn.png"

class Farm(Building):
    DISPLAY_NAME = "Farm"
    DESCRIPTION = "Generates food and peasants if housing is available."
    COST = {"wood": 75, "bismuth": 30}
    IMAGE_SOURCE = "farm.png"

class Barracks(Building):
    DISPLAY_NAME = "Barracks"
    DESCRIPTION = "Turns peasants into army units. Costs 2 🍖 per turn. Provides additional housing."
    COST = {"wood": 150, "bismuth": 75}
    IMAGE_SOURCE = "barracks.png"

class Sawmill(Building):
    DISPLAY_NAME = "Sawmill"
    DESCRIPTION = "Produces 🪵1 per turn for each sawmill level and nearby forest."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "sawmill.png"

class Mine(Building):
    DISPLAY_NAME = "Mine"
    DESCRIPTION = "Produces 🪨1 per turn for each mine level and nearby mountain."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "mine.png"

class ArcheryRange(Building):
    DISPLAY_NAME = "Archery Range"
    DESCRIPTION = "Allows training army units into archers."
    COST = {"wood": 200, "bismuth": 100}
    IMAGE_SOURCE = "archery_range.png"

class Laboratory(Building):
    DISPLAY_NAME = "Laboratory"
    DESCRIPTION = "Turns peasants into researchers, generating research points."
    COST = {"wood": 250, "bismuth": 125}
    IMAGE_SOURCE = "laboratory.png"

class Blacksmith(Building):
    DISPLAY_NAME = "Blacksmith"
    DESCRIPTION = "Allows restoration of item durability."
    COST = {"wood": 150, "bismuth": 75}
    IMAGE_SOURCE = "blacksmith.png"