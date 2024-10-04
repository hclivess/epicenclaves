import os
from typing import Dict, Any
from player import calculate_total_mana, calculate_total_hp


class Potion:
    DEFAULT_ICON = "default.png"

    @classmethod
    def get_image_source(cls):
        if hasattr(cls, 'IMAGE_SOURCE') and os.path.exists(f"img/assets/{cls.IMAGE_SOURCE}"):
            return cls.IMAGE_SOURCE
        return cls.DEFAULT_ICON

    @staticmethod
    def format_ingredients(ingredients: Dict[str, int]) -> str:
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
            icon = image_map.get(resource, Potion.DEFAULT_ICON)
            if not os.path.exists(f"img/assets/{icon}"):
                icon = Potion.DEFAULT_ICON
            formatted.append(f"<img class='resource-icon' src='/img/assets/{icon}' width='32' height='32' alt='{resource}'>{amount}")
        return " ".join(formatted)

    @classmethod
    def to_dict(cls):
        return {
            "type": cls.__name__.lower(),
            "display_name": cls.DISPLAY_NAME,
            "description": cls.DESCRIPTION,
            "ingredients": cls.INGREDIENTS,
            "formatted_ingredients": cls.format_ingredients(cls.INGREDIENTS),
            "image_source": cls.get_image_source()
        }

    @classmethod
    def effect(cls, user: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement this method")

class HealthPotion(Potion):
    DISPLAY_NAME = "Health Potion"
    DESCRIPTION = "Restores a portion of your health."
    INGREDIENTS = {"rat tail": 2, "food": 5}
    IMAGE_SOURCE = "health_potion.png"

    @classmethod
    def effect(cls, user: Dict[str, Any]) -> Dict[str, Any]:
        healing = 50  # You can adjust this value
        max_hp = calculate_total_hp(user.get("base_hp", 100), user.get("exp", 0))
        old_hp = user.get("hp", 0)
        user["hp"] = min(old_hp + healing, max_hp)
        actual_healing = user["hp"] - old_hp
        return {
            "message": f"You used a Health Potion and restored {actual_healing} HP.",
            "healing": actual_healing
        }

class ManaPotion(Potion):
    DISPLAY_NAME = "Mana Potion"
    DESCRIPTION = "Restores a portion of your mana."
    INGREDIENTS = {"ectoplasm": 1, "food": 5}
    IMAGE_SOURCE = "mana_potion.png"

    @classmethod
    def effect(cls, user: Dict[str, Any]) -> Dict[str, Any]:
        mana_restore = 30  # You can adjust this value
        max_mana = calculate_total_mana(user.get("base_mana", 100), user.get("exp", 0))
        user["mana"] = min(user.get("mana", 0) + mana_restore, max_mana)
        return {
            "message": f"You used a Mana Potion and restored {mana_restore} Mana.",
            "mana_restored": mana_restore
        }

potion_types = {
    cls.__name__.lower(): cls for name, cls in globals().items()
    if isinstance(cls, type) and issubclass(cls, Potion) and cls != Potion
}