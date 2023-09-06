import time

from backend import has_resources, update_user_data
from map import get_tile_map, get_user_data, insert_map_data
from costs import building_costs

def upgrade(user, mapdb, usersdb):
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

    if right_entity and right_entity["control"] != user:
        return "You do not own this tile"

    if right_entity and not has_resources(user_data, building_costs[right_entity["type"]]):
        return f"Not enough resources to upgrade {right_entity['type']}"

    if right_entity:
        for resource, amount in building_costs[right_entity["type"]].items():
            user_data[resource] -= int(amount / 2)
        right_entity["size"] += 1
        if right_entity["type"] == "house":
            user_data["pop_lim"] += 10

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "wood": user_data["wood"],
        "pop_lim": user_data.get("pop_lim", 0),
    }

    # Filter out None values
    updated_values = {k: v for k, v in updated_values.items() if v is not None}

    print("updated_values", updated_values)
    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)
    name = right_entity["type"] if right_entity else "building"

    if right_entity:
        entity_data = {
            "type": right_entity["type"],
            "name": name,
            "size": right_entity["size"],
            "control": user,
            "role": "building",
            "soldiers": right_entity.get("soldiers", 0)
        }
        data = {f"{user_data['x_pos']},{user_data['y_pos']}": entity_data}
        update_user_data(
            user=user, updated_values={"construction": data}, user_data_dict=usersdb
        )
        insert_map_data(mapdb, data)
        return f"Successfully upgraded {right_entity['type']}"
    else:
        return "No building found to upgrade"

