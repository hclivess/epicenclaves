from typing import Dict, List, Any
from player import calculate_total_hp, calculate_total_mana
import os

class Potion:
    DEFAULT_ICON = "default.png"

    def __init__(self, potion_id: int):
        self.type = self.__class__.__name__.lower()
        self.id = potion_id
        self.role = "potion"

    def get_image_source(self):
        if hasattr(self, 'IMAGE_SOURCE') and os.path.exists(f"img/assets/{self.IMAGE_SOURCE}"):
            return self.IMAGE_SOURCE
        return self.DEFAULT_ICON

    def format_ingredients(self, ingredients: Dict[str, int]) -> str:
        image_map = {
            "wood": "wood.png",
            "bismuth": "bismuth.png",
            "gold": "gold.png",
            "food": "food.png",
            "rat tail": "rat_tail.png",
            "wolf pelt": "wolf_pelt.png",
            "dragon scale": "dragon_scale.png",
            "ectoplasm": "ectoplasm.png"
        }
        formatted = []
        for resource, amount in ingredients.items():
            icon = image_map.get(resource, self.DEFAULT_ICON)
            if not os.path.exists(f"img/assets/{icon}"):
                icon = self.DEFAULT_ICON
            formatted.append(f"<img class='resource-icon' src='/img/assets/{icon}' width='32' height='32' alt='{resource}'>{amount}")
        return " ".join(formatted)

    def to_dict(self):
        return {
            "type": self.type,
            "display_name": self.DISPLAY_NAME,
            "description": self.DESCRIPTION,
            "role": self.role,
            "id": self.id,
            "ingredients": self.INGREDIENTS,
            "formatted_ingredients": self.format_ingredients(self.INGREDIENTS),
            "image_source": self.get_image_source()
        }

class HealthPotion(Potion):
    DISPLAY_NAME = "Health Potion"
    DESCRIPTION = "Restores a portion of your health."
    INGREDIENTS = {"rat tail": 2, "food": 5}
    IMAGE_SOURCE = "health_potion.png"

    def effect(self, user: Dict[str, Any]) -> Dict[str, Any]:
        base_healing = 50
        max_hp = calculate_total_hp(user.get("base_hp", 100), user.get("exp", 0))
        old_hp = user.get("hp", 0)
        user["hp"] = min(max_hp, old_hp + base_healing)

        actual_healing = user["hp"] - old_hp

        return {
            "healing_done": actual_healing,
            "message": f"You drink the Health Potion and restore {actual_healing} health!"
        }

class ManaPotion(Potion):
    DISPLAY_NAME = "Mana Potion"
    DESCRIPTION = "Restores a portion of your mana."
    INGREDIENTS = {"ectoplasm": 1, "food": 5}
    IMAGE_SOURCE = "mana_potion.png"

    def effect(self, user: Dict[str, Any]) -> Dict[str, Any]:
        base_mana_restore = 30
        max_mana = calculate_total_mana(100, user.get("exp", 0))
        old_mana = user.get("mana", 0)
        user["mana"] = min(max_mana, old_mana + base_mana_restore)

        actual_mana_restored = user["mana"] - old_mana

        return {
            "mana_restored": actual_mana_restored,
            "message": f"You drink the Mana Potion and restore {actual_mana_restored} mana!"
        }

potion_types = {
    cls.__name__.lower(): cls for name, cls in globals().items()
    if isinstance(cls, type) and issubclass(cls, Potion) and cls != Potion
}