from typing import Dict, List, Callable, Any
from player import calculate_total_hp, calculate_total_mana


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
            "mana": "img/assets/mana.png",
            "research": "img/assets/research.png"
        }
        return " ".join(
            f"<img class='resource-icon' src='{image_map.get(resource, resource)}' width='32' height='32' alt='{resource}'>{amount}"
            for resource, amount in cost.items())

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
            "mana_cost": self.MANA_COST
        }

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": f"Cast {self.DISPLAY_NAME}", "action": f"/cast?spell={self.type}"},
        ]

    def effect(self, caster: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement this method")


class Fireball(Spell):
    DISPLAY_NAME = "Fireball"
    DESCRIPTION = "Hurls a fiery ball of magic at your enemies, dealing damage."
    COST = {"research": 100}
    IMAGE_SOURCE = "fireball.png"
    MANA_COST = 20

    def effect(self, caster: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        base_damage = 50
        magic_bonus = caster.get("sorcery", 0)
        total_damage = base_damage + magic_bonus

        target["hp"] = max(0, target.get("hp", 0) - total_damage)

        return {
            "damage_dealt": total_damage,
            "message": f"Fireball hits the target for {total_damage} damage!"
        }


class Heal(Spell):
    DISPLAY_NAME = "Heal"
    DESCRIPTION = "Channels healing energy to restore your own health."
    COST = {"research": 120}
    IMAGE_SOURCE = "heal.png"
    MANA_COST = 25

    def effect(self, caster: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        base_healing = 1
        magic_bonus = caster.get("sorcery", 0)
        total_healing = base_healing + int(magic_bonus / 10)

        max_hp = calculate_total_hp(caster.get("base_hp", 100), caster.get("exp", 0))
        old_hp = caster.get("hp", 0)
        caster["hp"] = min(max_hp, old_hp + total_healing)

        actual_healing = caster["hp"] - old_hp

        return {
            "healing_done": actual_healing,
            "message": f"Heal restores {actual_healing} health to you!"
        }


class ManaSwap(Spell):
    DISPLAY_NAME = "Mana Swap"
    DESCRIPTION = "Switches your current mana with your current HP."
    COST = {"research": 150}
    IMAGE_SOURCE = "manaswap.png"
    MANA_COST = 0

    def effect(self, caster: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        current_hp = caster.get("hp", 0)
        current_mana = caster.get("mana", 0)
        max_hp = calculate_total_hp(caster.get("base_hp", 100), caster.get("exp", 0))
        max_mana = calculate_total_mana(100, caster.get("exp", 0))

        caster["hp"] = min(current_mana, max_hp)
        caster["mana"] = min(current_hp, max_mana)

        return {
            "message": f"You swap your HP and mana! New HP: {caster['hp']}, New Mana: {caster['mana']}"
        }


class LifeSwap(Spell):
    DISPLAY_NAME = "Life Swap"
    DESCRIPTION = "Exchanges your current HP with your opponent's."
    COST = {"research": 200}
    IMAGE_SOURCE = "lifeswap.png"
    MANA_COST = 50

    def effect(self, caster: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        caster_hp = caster.get("hp", 0)
        target_hp = target.get("hp", 0)

        caster_max_hp = calculate_total_hp(caster.get("base_hp", 100), caster.get("exp", 0))
        target_max_hp = calculate_total_hp(target.get("base_hp", 100), target.get("exp", 0))

        caster["hp"] = min(target_hp, caster_max_hp)
        target["hp"] = min(caster_hp, target_max_hp)

        return {
            "message": f"You swap HP with your opponent! Your new HP: {caster['hp']}, Opponent's new HP: {target['hp']}"
        }


class ConjureMana(Spell):
    DISPLAY_NAME = "Conjure Mana"
    DESCRIPTION = "Magically creates additional mana for the caster."
    COST = {"research": 180}
    IMAGE_SOURCE = "conjuremana.png"
    MANA_COST = 0

    def effect(self, caster: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
        base_mana = 30
        magic_bonus = caster.get("sorcery", 0)
        total_mana_gained = base_mana + int(magic_bonus / 5)

        max_mana = calculate_total_mana(100, caster.get("exp", 0))
        old_mana = caster.get("mana", 0)
        caster["mana"] = min(max_mana, old_mana + total_mana_gained)

        actual_mana_gained = caster["mana"] - old_mana

        return {
            "mana_gained": actual_mana_gained,
            "message": f"You conjure {actual_mana_gained} mana! Your new mana total: {caster['mana']}"
        }


spell_types = {
    cls.__name__.lower(): cls for name, cls in globals().items()
    if isinstance(cls, type) and issubclass(cls, Spell) and cls != Spell
}