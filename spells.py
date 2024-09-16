from typing import Dict, List

class Spell:
    def __init__(self, spell_id: int):
        self.type = self.__class__.__name__.lower()
        self.id = spell_id
        self.role = "spell"

    def format_cost(self, cost: Dict[str, int]) -> str:
        image_map = {
            "wood": "img/assets/wood.png",
            "bismuth": "img/assets/bismuth.png",
            "gold": "img/assets/gold.png",
            "food": "img/assets/food.png",
            "mana": "img/assets/mana.png"
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
            "formatted_cost": self.format_cost(self.COST),
            "image_source": self.IMAGE_SOURCE,
            "damage": self.DAMAGE,
            "mana_cost": self.MANA_COST
        }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": f"Cast {self.DISPLAY_NAME}", "action": f"/cast?spell={self.type}"},
        ]

class Fireball(Spell):
    DISPLAY_NAME = "Fireball"
    DESCRIPTION = "Hurls a fiery ball of magic at your enemies, dealing damage."
    COST = {"research": 100}
    IMAGE_SOURCE = "fireball.png"
    DAMAGE = 50
    MANA_COST = 20

spell_types = {
    cls.__name__.lower(): cls for name, cls in globals().items()
    if isinstance(cls, type) and issubclass(cls, Spell) and cls != Spell
}