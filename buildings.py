from typing import Dict, List
import random
import math

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
            "image_source": self.IMAGE_SOURCE,
            "upgrade_costs": self.UPGRADE_COSTS,
            "formatted_upgrade_costs": {level: self.format_cost(cost) for level, cost in self.UPGRADE_COSTS.items()}
        }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "deploy army", "action": f"/deploy?type=soldiers&action=add"},
            {"name": "remove army", "action": f"/deploy?type=soldiers&action=remove"},
            {"name": "upgrade", "action": f"/upgrade"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class House(Building):
    DISPLAY_NAME = "House"
    DESCRIPTION = "Increases population limit by 10."
    COST = {"wood": 50, "bismuth": 20}
    IMAGE_SOURCE = "house.png"
    UPGRADE_COSTS = {
        2: {"wood": 75, "bismuth": 30},
        3: {"wood": 100, "bismuth": 40},
        4: {"wood": 150, "bismuth": 60},
        5: {"wood": 225, "bismuth": 90}
    }

class Inn(Building):
    DISPLAY_NAME = "Inn"
    DESCRIPTION = "Allows user to rest and restore health."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "inn.png"
    UPGRADE_COSTS = {
        2: {"wood": 150, "bismuth": 75},
        3: {"wood": 225, "bismuth": 112},
        4: {"wood": 337, "bismuth": 168},
        5: {"wood": 506, "bismuth": 252}
    }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        actions = super().get_actions(user)
        actions.extend([
            {"name": "sleep 10 hours", "action": "/rest?hours=10"},
            {"name": "sleep 20 hours", "action": "/rest?hours=20"},
        ])
        return actions

class Farm(Building):
    DISPLAY_NAME = "Farm"
    DESCRIPTION = "Generates food and peasants if housing is available."
    COST = {"wood": 75, "bismuth": 30}
    IMAGE_SOURCE = "farm.png"
    UPGRADE_COSTS = {
        2: {"wood": 112, "bismuth": 45},
        3: {"wood": 168, "bismuth": 67},
        4: {"wood": 252, "bismuth": 100},
        5: {"wood": 378, "bismuth": 150}
    }

class Barracks(Building):
    DISPLAY_NAME = "Barracks"
    DESCRIPTION = "Turns peasants into army units. Costs 2 🍖 per turn. Provides additional housing."
    COST = {"wood": 150, "bismuth": 75}
    IMAGE_SOURCE = "barracks.png"
    UPGRADE_COSTS = {
        2: {"wood": 225, "bismuth": 112},
        3: {"wood": 337, "bismuth": 168},
        4: {"wood": 506, "bismuth": 252},
        5: {"wood": 759, "bismuth": 378}
    }

class Sawmill(Building):
    DISPLAY_NAME = "Sawmill"
    DESCRIPTION = "Produces 🪵1 per turn for each sawmill level and nearby forest."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "sawmill.png"
    UPGRADE_COSTS = {
        2: {"wood": 150, "bismuth": 75},
        3: {"wood": 225, "bismuth": 112},
        4: {"wood": 337, "bismuth": 168},
        5: {"wood": 506, "bismuth": 252}
    }

class Mine(Building):
    DISPLAY_NAME = "Mine"
    DESCRIPTION = "Produces 🪨1 per turn for each mine level and nearby mountain."
    COST = {"wood": 100, "bismuth": 50}
    IMAGE_SOURCE = "mine.png"
    UPGRADE_COSTS = {
        2: {"wood": 150, "bismuth": 75},
        3: {"word": 225, "bismuth": 112},
        4: {"word": 337, "bismuth": 168},
        5: {"word": 506, "bismuth": 252}
    }

class ArcheryRange(Building):
    DISPLAY_NAME = "Archery Range"
    DESCRIPTION = "Allows training army units into archers."
    COST = {"wood": 200, "bismuth": 100}
    IMAGE_SOURCE = "archery_range.png"
    UPGRADE_COSTS = {
        2: {"wood": 300, "bismuth": 150},
        3: {"wood": 450, "bismuth": 225},
        4: {"wood": 675, "bismuth": 337},
        5: {"wood": 1012, "bismuth": 506}
    }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        actions = super().get_actions(user)
        actions.extend([
            {"name": "train 1 archer", "action": "/train?type=archer&amount=1"},
            {"name": "train 10 archers", "action": "/train?type=archer&amount=10"},
        ])
        return actions

class Laboratory(Building):
    DISPLAY_NAME = "Laboratory"
    DESCRIPTION = "Turns peasants into researchers, generating research points."
    COST = {"wood": 250, "bismuth": 125}
    IMAGE_SOURCE = "laboratory.png"
    UPGRADE_COSTS = {
        2: {"wood": 375, "bismuth": 187},
        3: {"wood": 562, "bismuth": 280},
        4: {"wood": 843, "bismuth": 420},
        5: {"wood": 1264, "bismuth": 630}
    }

class Blacksmith(Building):
    DISPLAY_NAME = "Blacksmith"
    DESCRIPTION = "Allows restoration of item durability."
    COST = {"wood": 150, "bismuth": 75}
    IMAGE_SOURCE = "blacksmith.png"
    UPGRADE_COSTS = {
        2: {"wood": 225, "bismuth": 112},
        3: {"wood": 337, "bismuth": 168},
        4: {"wood": 506, "bismuth": 252},
        5: {"wood": 759, "bismuth": 378}
    }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        actions = super().get_actions(user)
        actions.append({"name": "repair all gear", "action": "/repair?type=all"})
        return actions

building_types = {
    cls.__name__.lower(): cls for name, cls in globals().items()
    if isinstance(cls, type) and issubclass(cls, Building) and cls != Building
}