from typing import Dict, Any, List, Tuple
from backend import update_user_data
from map import occupied_by, owned_by, get_user_data


def check_alchemist_access(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any]) -> Tuple[bool, str]:
    user_data = get_user_data(user, usersdb)
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    proper_tile = occupied_by(x_pos, y_pos, what="alchemist", mapdb=mapdb)
    under_control = owned_by(x_pos, y_pos, control=user, mapdb=mapdb)

    if not proper_tile:
        return False, "You cannot access alchemist functions here. An alchemist is required."
    elif not under_control:
        return False, "This alchemist is not under your control."

    return True, ""


POTION_RECIPES = {
    "health_potion": {
        "ingredients": {"wood": 10, "food": 5},
        "effect": {"hp": 50},
        "description": "Restores 50 HP"
    },
    "mana_potion": {
        "ingredients": {"bismuth": 5, "food": 5},
        "effect": {"mana": 30},
        "description": "Restores 30 Mana"
    }
}


def get_available_potions() -> List[Dict[str, Any]]:
    return [{"name": name, **recipe} for name, recipe in POTION_RECIPES.items()]


def craft_potion(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any], potion_name: str) -> Tuple[bool, str]:
    access_granted, message = check_alchemist_access(user, usersdb, mapdb)
    if not access_granted:
        return False, message

    user_data = get_user_data(user, usersdb)

    if potion_name not in POTION_RECIPES:
        return False, "Invalid potion recipe"

    recipe = POTION_RECIPES[potion_name]

    # Check if user has the required ingredients
    for ingredient, amount in recipe["ingredients"].items():
        if user_data["ingredients"].get(ingredient, 0) < amount:
            return False, f"Not enough {ingredient}. You need {amount}."

    # Deduct ingredients and add potion to inventory
    for ingredient, amount in recipe["ingredients"].items():
        user_data["ingredients"][ingredient] -= amount

    user_data[potion_name] = user_data.get(potion_name, 0) + 1

    update_user_data(user, user_data, usersdb)
    return True, f"Successfully crafted {potion_name}"


def use_potion(user: str, usersdb: Dict[str, Any], potion_name: str) -> Tuple[bool, str]:
    user_data = get_user_data(user, usersdb)

    if user_data.get(potion_name, 0) <= 0:
        return False, f"You don't have any {potion_name}"

    if potion_name not in POTION_RECIPES:
        return False, "Invalid potion"

    effect = POTION_RECIPES[potion_name]["effect"]

    for stat, value in effect.items():
        if stat == "hp":
            user_data["hp"] = min(user_data["hp"] + value, user_data["base_hp"])
        elif stat == "mana":
            user_data["mana"] = min(user_data["mana"] + value, 100)  # Assuming max mana is 100

    user_data[potion_name] -= 1
    update_user_data(user, user_data, usersdb)
    return True, f"Used {potion_name}. {POTION_RECIPES[potion_name]['description']}"