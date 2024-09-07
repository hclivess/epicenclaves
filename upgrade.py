import time
from typing import Dict, Any

from backend import has_resources, update_user_data
from map import get_tile_map, get_user_data, insert_map_data
from buildings import building_types


def upgrade(user: str, mapdb: Any, usersdb: Any) -> str:
    user_data = get_user_data(user, usersdb)
    on_tile = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)

    if user_data["action_points"] < 1:
        return "Not enough action points to upgrade"

    tile_key = f"{user_data['x_pos']},{user_data['y_pos']}"
    right_entity = None

    for entry in on_tile:
        if tile_key in entry and entry[tile_key]["role"] == "building":
            right_entity = entry[tile_key]
            break

    if not right_entity:
        return "No building found to upgrade"

    if right_entity["control"] != user:
        return "You do not own this building"

    building_class = building_types.get(right_entity["type"].lower())
    if not building_class:
        return f"Upgrade procedure not defined for {right_entity['type']}"

    building_instance = building_class(right_entity.get("id", 1))
    current_level = right_entity.get("level", 1)
    next_level = current_level + 1

    if next_level not in building_instance.UPGRADE_COSTS:
        return f"Maximum level reached for {right_entity['type']}"

    upgrade_cost = building_instance.UPGRADE_COSTS[next_level]

    print(f"Debug: upgrade_cost = {upgrade_cost}")
    print(f"Debug: upgrade_cost type = {type(upgrade_cost)}")
    print(f"Debug: user_data['ingredients'] = {user_data.get('ingredients', {})}")

    # Extract the inner dictionary if upgrade_cost is nested
    cost_to_check = upgrade_cost.get('ingredients', upgrade_cost)

    if not has_resources(user_data, {"ingredients": cost_to_check}):
        return f"Not enough resources to upgrade {right_entity['type']}"

    ingredients = user_data.get("ingredients", {})
    for resource, amount in cost_to_check.items():
        ingredients[resource] -= amount
    right_entity["level"] = next_level

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "ingredients": ingredients,
    }

    # Update the construction data in user_data
    construction_data = user_data.get("construction", {})
    construction_data[tile_key] = right_entity
    updated_values["construction"] = construction_data

    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

    # Update the map data
    insert_map_data(mapdb, {tile_key: right_entity})

    return f"Successfully upgraded {right_entity['type']} to level {next_level}"