from backend import has_resources, update_user_data
from map import get_tile_map, get_user_data, insert_map_data
from costs import building_costs


def build(entity, name, user, mapdb, usersdb):
    user_data = get_user_data(user, usersdb)
    on_tile = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)

    if user_data["action_points"] < 1:
        return "Not enough action points to build"

    building_count = {}
    for key, value in user_data.get("construction", {}).items():
        building_type = value.get("type")
        if building_type:
            building_count[building_type] = building_count.get(building_type, 0) + 1

    if building_count.get(entity, 0) >= 10:
        return "Cannot have more than 10 of the same building type"

    building_or_scenery_exists = False
    for entry in on_tile:
        tile_data = entry.get(f"{user_data['x_pos']},{user_data['y_pos']}")
        if tile_data and (tile_data["role"] == "building" or tile_data["role"] == "scenery"):
            building_or_scenery_exists = True
            break

    if building_or_scenery_exists:
        return "Cannot build here"

    if entity not in building_costs:
        return "Building procedure not defined"

    if not has_resources(user_data, building_costs[entity]):
        return f"Not enough resources to build {entity}"

    for resource, amount in building_costs[entity].items():
        user_data[resource] -= amount

    if entity == "house":
        user_data["pop_lim"] += 10

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "wood": user_data["wood"],
        "pop_lim": user_data.get("pop_lim", None),
    }

    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

    entity_data = {
        "type": entity,
        "name": name,
        "level": 1,
        "control": user,
        "role": "building",
        "army": 0,
    }

    data = {f"{user_data['x_pos']},{user_data['y_pos']}": entity_data}
    update_user_data(user=user, updated_values={"construction": data}, user_data_dict=usersdb)
    insert_map_data(mapdb, data)

    return f"Successfully built {entity}"
