from backend import has_resources, update_user_data
from map import get_tile_map, insert_map_data
from buildings import building_types

def build(user, user_data, entity, name, mapdb, usersdb):
    print(f"Attempting to build: {entity}")
    print(f"Available building types: {list(building_types.keys())}")

    if user_data is None:
        return f"User {user} not found."

    if user_data["action_points"] < 1:
        return "Not enough action points to build"

    on_tile = get_tile_map(user_data["x_pos"], user_data["y_pos"], mapdb)

    # Check if there's already a building or scenery on the tile
    if any(entry.get(f"{user_data['x_pos']},{user_data['y_pos']}", {}).get("role") in ["building", "scenery"] for entry in on_tile):
        return "Cannot build here"

    if entity not in building_types:
        return f"Building type '{entity}' not recognized. Available types: {', '.join(building_types.keys())}"

    building_class = building_types[entity]
    building_instance = building_class(1)  # Create an instance with ID 1 (you might want to generate a unique ID)
    building_data = building_instance.to_dict()

    # Check building limit
    user_buildings = user_data.get("construction", {})
    if sum(1 for b in user_buildings.values() if b["type"] == entity) >= 10:
        return f"Cannot have more than 10 {building_data['display_name']} buildings"

    if not has_resources(user_data, building_data["cost"]):
        return f"Not enough resources to build {building_data['display_name']}"

    # Deduct resources
    ingredients = user_data.get("ingredients", {})
    for resource, amount in building_data["cost"]["ingredients"].items():
        if resource in ingredients:
            ingredients[resource] -= amount

    # Update user data
    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "ingredients": ingredients,
    }
    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

    # Prepare building data for insertion
    entity_data = {
        "type": entity,
        "name": name,
        "level": 1,
        "control": user,
        "role": "building",
        "army": 0,
        "display_name": building_data["display_name"],
        "description": building_data["description"],
        "image_source": building_data["image_source"],
        "upgrade_costs": building_data["upgrade_costs"],
    }

    # Update construction data
    construction_data = user_data.get("construction", {})
    construction_data[f"{user_data['x_pos']},{user_data['y_pos']}"] = entity_data
    update_user_data(user=user, updated_values={"construction": construction_data}, user_data_dict=usersdb)

    # Insert into map database
    insert_map_data(mapdb, {f"{user_data['x_pos']},{user_data['y_pos']}": entity_data})

    return f"Successfully built {building_data['display_name']}"