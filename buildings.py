from typing import Dict

class Building:
    def __init__(self, building_id: int):
        self.type = self.__class__.__name__.lower()
        self.id = building_id
        self.role = "building"

    def to_dict(self):
        return {
            "type": self.type,
            "display_name": self.DISPLAY_NAME,
            "description": self.DESCRIPTION,
            "role": self.role,
            "id": self.id,
            "cost": self.COST,
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
    DESCRIPTION = "Turns peasants into army for 2 food per turn and additional housing. Army is the only deployable unit."
    COST = {"wood": 150, "bismuth": 75}
    IMAGE_SOURCE = "barracks.png"

class Sawmill(Building):
    DISPLAY_NAME = "Sawmill"
    DESCRIPTION = "Passively produces 🪵1 per turn per every sawmill level and forest."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "sawmill.png"

class Mine(Building):
    DISPLAY_NAME = "Mine"
    DESCRIPTION = "Passively produces 🪨1 per turn per every mine level and forest."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "mine.png"

class ArcheryRange(Building):
    DISPLAY_NAME = "Archery Range"
    DESCRIPTION = "Allows you to train army into archers."
    COST = {"wood": 200, "bismuth": 100}
    IMAGE_SOURCE = "archery_range.png"

class Laboratory(Building):
    DISPLAY_NAME = "Laboratory"
    DESCRIPTION = "Turns peasants into researchers to generate research points."
    COST = {"wood": 250, "bismuth": 125}
    IMAGE_SOURCE = "laboratory.png"

class Blacksmith(Building):
    DISPLAY_NAME = "Blacksmith"
    DESCRIPTION = "Allows you to restore durability of your items."
    COST = {"wood": 150, "bismuth": 75}
    IMAGE_SOURCE = "blacksmith.png"