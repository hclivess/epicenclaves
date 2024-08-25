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

    right_entity = None

    for entry in on_tile:
        tile_data = entry.get(f"{user_data['x_pos']},{user_data['y_pos']}")
        if tile_data and tile_data["role"] == "building":
            right_entity = tile_data
            break

    if not right_entity:
        return "No building found to upgrade"

    if right_entity["control"] != user:
        return "You do not own this building"

    building_type = building_types.get(right_entity["type"].lower())
    if not building_type:
        return f"Upgrade procedure not defined for {right_entity['type']}"

    current_level = right_entity.get("level", 1)
    next_level = current_level + 1
    upgrade_cost = building_type.UPGRADE_COSTS.get(next_level)

    if not upgrade_cost:
        return f"Maximum level reached for {right_entity['type']}"

    if not has_resources(user_data, upgrade_cost):
        return f"Not enough resources to upgrade {right_entity['type']}"

    for resource, amount in upgrade_cost.items():
        user_data[resource] -= amount
    right_entity["level"] = next_level

    if right_entity["type"].lower() == "house":
        user_data["pop_lim"] = user_data.get("pop_lim", 0) + 10

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "wood": user_data["wood"],
        "bismuth": user_data["bismuth"],
        "pop_lim": user_data.get("pop_lim", 0),
    }

    # Filter out None values
    updated_values = {k: v for k, v in updated_values.items() if v is not None}

    print("updated_values", updated_values)
    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

    entity_data = {
        "type": right_entity["type"],
        "name": right_entity["type"],
        "level": right_entity["level"],
        "control": user,
        "role": "building",
        "army": right_entity.get("army", 0)
    }
    data = {f"{user_data['x_pos']},{user_data['y_pos']}": entity_data}
    update_user_data(
        user=user, updated_values={"construction": data}, user_data_dict=usersdb
    )
    insert_map_data(mapdb, data)
    return f"Successfully upgraded {right_entity['type']} to level {next_level}"