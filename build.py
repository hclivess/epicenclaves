from backend import has_resources, update_user_data
from map import get_tile_map, insert_map_data, is_surrounded_by
from buildings import building_types

def build(user, user_data, entity, name, mapdb, usersdb):
    print(f"Attempting to build: {entity}")
    print(f"Available building types: {list(building_types.keys())}")

    if user_data is None:
        return f"User {user} not found."

    if user_data["action_points"] < 1:
        return "Not enough action points to build"

    x, y = user_data["x_pos"], user_data["y_pos"]
    on_tile = get_tile_map(x, y, mapdb)

    tile_key = f"{x},{y}"
    if any(entry.get(tile_key, {}).get("role") in ["building", "scenery"] for entry in on_tile):
        return "Cannot build here"

    if entity not in building_types:
        return f"Building type '{entity}' not recognized. Available types: {', '.join(building_types.keys())}"

    building_class = building_types[entity]
    building_instance = building_class(1)  # Create an instance with ID 1 (you might want to generate a unique ID)
    building_data = building_instance.to_dict()

    # Check building restrictions
    if entity == "sawmill":
        if not is_surrounded_by(x, y, "forest", mapdb, diameter=1):
            return "Sawmills can only be built on tiles surrounding forests"
    elif entity == "mine":
        if not is_surrounded_by(x, y, "mountain", mapdb, diameter=1):
            return "Mines can only be built on tiles adjacent to mountains"

    # Check building limit
    user_buildings = user_data.get("construction", {})
    if sum(1 for b in user_buildings.values() if b["type"] == entity and not b["type"] == "palisade") >= 10:
        return f"Cannot have more than 10 {building_data['display_name']} buildings"

    if not has_resources(user_data, {"ingredients": building_data["cost"]["ingredients"]}):
        return f"Not enough resources to build {building_data['display_name']}"

    # Deduct resources
    ingredients = user_data.get("ingredients", {})
    for resource, amount in building_data["cost"]["ingredients"].items():
        if resource in ingredients:
            ingredients[resource] -= amount

    # Prepare building data for insertion
    entity_data = {
        "type": entity,
        "name": name,
        "level": 1,
        "control": user,
        "role": "building",
        "army": 0,
    }

    # Add HP for buildings that have it
    if hasattr(building_instance, 'HP'):
        entity_data["hp"] = building_instance.HP

    # Update construction data
    construction_data = user_data.get("construction", {})
    construction_data[tile_key] = entity_data

    # Update user data
    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "ingredients": ingredients,
        "construction": construction_data
    }
    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

    # Insert into map database
    insert_map_data(mapdb, {tile_key: entity_data})

    return f"Successfully built {building_data['display_name']}"