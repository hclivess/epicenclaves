from typing import Dict, List
import random
import math

class Building:
    def __init__(self, building_id: int):
        self.type = self.__class__.__name__.lower()
        self.id = building_id
        self.role = "building"

    def format_cost(self, cost: Dict[str, int]) -> str:
        image_map = {
            "wood": "img/assets/wood.png",
            "bismuth": "img/assets/bismuth.png",
            "gold": "img/assets/gold.png",
            "food": "img/assets/food.png"
        }
        return " ".join(f"<img class='resource-icon' src='{image_map.get(resource, resource)}' width='32' height='32' alt='{resource}'>{amount}" for resource, amount in cost.items())

    def to_dict(self):
        return {
            "type": self.type,
            "display_name": self.DISPLAY_NAME,
            "description": self.DESCRIPTION,
            "role": self.role,
            "id": self.id,
            "cost": self.COST,
            "formatted_cost": self.format_cost(self.COST["ingredients"]),
            "image_source": self.IMAGE_SOURCE,
            "upgrade_costs": self.UPGRADE_COSTS,
            "formatted_upgrade_costs": {level: self.format_cost(cost["ingredients"]) for level, cost in self.UPGRADE_COSTS.items()}
        }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
            {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
            {"name": "upgrade", "action": f"/upgrade"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
            {"name": "demolish", "action": f"/demolish"},
        ]

class House(Building):
    DISPLAY_NAME = "House"
    DESCRIPTION = "Increases population limit by 10."
    COST = {"ingredients": {"wood": 50, "bismuth": 20}}
    IMAGE_SOURCE = "house.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 75, "bismuth": 30}},
        3: {"ingredients": {"wood": 100, "bismuth": 40}},
        4: {"ingredients": {"wood": 150, "bismuth": 60}},
        5: {"ingredients": {"wood": 225, "bismuth": 90}}
    }

class Inn(Building):
    DISPLAY_NAME = "Inn"
    DESCRIPTION = "Allows user to rest and restore health."
    COST = {"ingredients": {"wood": 100, "bismuth": 50}}
    IMAGE_SOURCE = "inn.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 150, "bismuth": 75}},
        3: {"ingredients": {"wood": 225, "bismuth": 112}},
        4: {"ingredients": {"wood": 337, "bismuth": 168}},
        5: {"ingredients": {"wood": 506, "bismuth": 252}}
    }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        actions = super().get_actions(user)
        actions.extend([
            {"name": "sleep 10 hours", "action": "/rest?hours=10"},
            {"name": "sleep until rested", "action": "/rest?hours=all"},
        ])
        return actions

class Farm(Building):
    DISPLAY_NAME = "Farm"
    DESCRIPTION = "Generates food and peasants if housing is available."
    COST = {"ingredients": {"wood": 75, "bismuth": 30}}
    IMAGE_SOURCE = "farm.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 112, "bismuth": 45}},
        3: {"ingredients": {"wood": 168, "bismuth": 67}},
        4: {"ingredients": {"wood": 252, "bismuth": 100}},
        5: {"ingredients": {"wood": 378, "bismuth": 150}}
    }

class Barracks(Building):
    DISPLAY_NAME = "Barracks"
    DESCRIPTION = "Turns peasants into army units. Costs 2 <img class='resource-icon' src='img/assets/food.png' alt='Food' width='32' height='32'> per turn. Provides additional housing."
    COST = {"ingredients": {"wood": 150, "bismuth": 75}}
    IMAGE_SOURCE = "barracks.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 225, "bismuth": 112}},
        3: {"ingredients": {"wood": 337, "bismuth": 168}},
        4: {"ingredients": {"wood": 506, "bismuth": 252}},
        5: {"ingredients": {"wood": 759, "bismuth": 378}}
    }

class Outpost(Building):
    DISPLAY_NAME = "Outpost"
    DESCRIPTION = "Destroys enemy siege deployments in a perimeter of 10 tiles."
    COST = {"ingredients": {"wood": 150, "bismuth": 75}}
    IMAGE_SOURCE = "outpost.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 225, "bismuth": 112}},
        3: {"ingredients": {"wood": 337, "bismuth": 168}},
        4: {"ingredients": {"wood": 506, "bismuth": 252}},
        5: {"ingredients": {"wood": 759, "bismuth": 378}}
    }

class Sawmill(Building):
    DISPLAY_NAME = "Sawmill"
    DESCRIPTION = "Produces <img class='resource-icon' src='img/assets/wood.png' alt='Wood' width='32' height='32'>1 per turn for each sawmill level and adjacent forest."
    COST = {"ingredients": {"wood": 100, "bismuth": 50}}
    IMAGE_SOURCE = "sawmill.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 150, "bismuth": 75}},
        3: {"ingredients": {"wood": 225, "bismuth": 112}},
        4: {"ingredients": {"wood": 337, "bismuth": 168}},
        5: {"ingredients": {"wood": 506, "bismuth": 252}}
    }

class Mine(Building):
    DISPLAY_NAME = "Mine"
    DESCRIPTION = "Produces <img class='resource-icon' src='img/assets/bismuth.png' alt='Bismuth' width='32' height='32'>1 per turn for each mine level and adjacent mountain."
    COST = {"ingredients": {"wood": 100, "bismuth": 50}}
    IMAGE_SOURCE = "mine.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 150, "bismuth": 75}},
        3: {"ingredients": {"wood": 225, "bismuth": 112}},
        4: {"ingredients": {"wood": 337, "bismuth": 168}},
        5: {"ingredients": {"wood": 506, "bismuth": 252}}
    }

class Palisade(Building):
    DISPLAY_NAME = "Palisade"
    DESCRIPTION = "Serves as a protection against invaders."
    COST = {"ingredients": {"wood": 10, "bismuth": 10}}
    IMAGE_SOURCE = "palisade.png"
    HP = 1000
    UPGRADE_COSTS = {}

class Siege(Building):
    DISPLAY_NAME = "Siege"
    DESCRIPTION = "Lay siege to a palisade in order to destroy it. Perimeter of 1."
    COST = {"ingredients": {"wood": 100, "bismuth": 100}}
    IMAGE_SOURCE = "siege.png"
    HP = 250
    UPGRADE_COSTS = {}

"""
class ArcheryRange(Building):
    DISPLAY_NAME = "Archery Range"
    DESCRIPTION = "Allows training army units into archers."
    COST = {"ingredients": {"wood": 200, "bismuth": 100}}
    IMAGE_SOURCE = "archery_range.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 300, "bismuth": 150}},
        3: {"ingredients": {"wood": 450, "bismuth": 225}},
        4: {"ingredients": {"wood": 675, "bismuth": 337}},
        5: {"ingredients": {"wood": 1012, "bismuth": 506}}
    }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        actions = super().get_actions(user)
        actions.extend([
            {"name": "train 1 archer", "action": "/train?type=archer&amount=1"},
            {"name": "train 10 archers", "action": "/train?type=archer&amount=10"},
        ])
        return actions
"""
class Laboratory(Building):
    DISPLAY_NAME = "Laboratory"
    DESCRIPTION = "Turns peasants into researchers, generating research points."
    COST = {"ingredients": {"wood": 250, "bismuth": 125}}
    IMAGE_SOURCE = "laboratory.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 375, "bismuth": 187}},
        3: {"ingredients": {"wood": 562, "bismuth": 280}},
        4: {"ingredients": {"wood": 843, "bismuth": 420}},
        5: {"ingredients": {"wood": 1264, "bismuth": 630}}
    }

class Blacksmith(Building):
    DISPLAY_NAME = "Blacksmith"
    DESCRIPTION = "Allows restoration of item durability."
    COST = {"ingredients": {"wood": 150, "bismuth": 75}}
    IMAGE_SOURCE = "blacksmith.png"
    UPGRADE_COSTS = {
        2: {"ingredients": {"wood": 225, "bismuth": 112}},
        3: {"ingredients": {"wood": 337, "bismuth": 168}},
        4: {"ingredients": {"wood": 506, "bismuth": 252}},
        5: {"ingredients": {"wood": 759, "bismuth": 378}}
    }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        actions = super().get_actions(user)
        actions.append({"name": "repair all gear", "action": "/repair?type=all"})
        return actions

building_types = {
    cls.__name__.lower(): cls for name, cls in globals().items()
    if isinstance(cls, type) and issubclass(cls, Building) and cls != Building
}