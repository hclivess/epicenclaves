from typing import Dict, Any, List, Tuple
from backend import update_user_data
from map import occupied_by, owned_by, get_user_data
from potions import potion_types

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

def get_available_potions() -> List[Dict[str, Any]]:
    return [potion_class.to_dict() for potion_class in potion_types.values()]

def craft_potion(user: str, usersdb: Dict[str, Any], mapdb: Dict[str, Any], potion_name: str) -> Tuple[bool, str]:
    access_granted, message = check_alchemist_access(user, usersdb, mapdb)
    if not access_granted:
        return False, message

    user_data = get_user_data(user, usersdb)

    if potion_name not in potion_types:
        return False, "Invalid potion recipe"

    potion_class = potion_types[potion_name]

    # Check if user has the required ingredients
    for ingredient, amount in potion_class.INGREDIENTS.items():
        if user_data.get("ingredients", {}).get(ingredient, 0) < amount:
            return False, f"Not enough {ingredient}. You need {amount}."

    # Deduct ingredients and add potion to inventory
    for ingredient, amount in potion_class.INGREDIENTS.items():
        user_data[ingredient] = user_data.get(ingredient, 0) - amount

    user_data[potion_name] = user_data.get(potion_name, 0) + 1

    update_user_data(user, user_data, usersdb)
    return True, f"Successfully crafted {potion_class.DISPLAY_NAME}"

def use_potion(user: str, usersdb: Dict[str, Any], potion_name: str) -> Tuple[bool, str]:
    user_data = get_user_data(user, usersdb)

    if user_data.get(potion_name, 0) <= 0:
        return False, f"You don't have any {potion_name}"

    if potion_name not in potion_types:
        return False, "Invalid potion"

    potion_class = potion_types[potion_name]
    effect_result = potion_class.effect(user_data)

    user_data[potion_name] -= 1
    update_user_data(user, user_data, usersdb)
    return True, effect_result["message"]

def get_user_potions(user: str, usersdb: Dict[str, Any]) -> Dict[str, int]:
    user_data = get_user_data(user, usersdb)
    return {potion_name: user_data.get(potion_name, 0) for potion_name in potion_types.keys()}