import os
import random
from hashlib import blake2b

from sqlite import get_map_at_coords, save_map_data

if not os.path.exists("db"):
    os.mkdir("db")


def death_roll(hit_chance):
    if hit_chance < 0 or hit_chance > 1:
        raise ValueError("Hit chance should be between 0 and 1 inclusive.")
    return random.random() < hit_chance


def generate_entities(entity_class, probability, mapdb, start_x=1, start_y=1, size=101, every=10, max_entities=None):
    generated_count = 0
    entity_instance = entity_class()

    additional_entity_data = {
        "control": "nobody",
        "type": getattr(entity_instance, "type", entity_class.__name__),
        **({"hp": entity_instance.hp} if hasattr(entity_instance, "hp") else {}),
        **({"armor": entity_instance.armor} if hasattr(entity_instance, "armor") else {}),
        **({"max_damage": entity_instance.max_damage} if hasattr(entity_instance, "max_damage") else {})
    }

    for x_pos in range(start_x, size, every):
        for y_pos in range(start_y, size, every):
            if max_entities is not None and generated_count >= max_entities:
                return
            if random.random() <= probability:
                data = {"type": entity_class.__name__}
                data.update(additional_entity_data)
                print(f"Generating {data} on {x_pos}, {y_pos}")
                save_map_data(x_pos=x_pos, y_pos=y_pos, data=data, map_data_dict=mapdb)
                generated_count += 1


def hashify(data):
    hashified = blake2b(data.encode(), digest_size=15).hexdigest()
    return hashified


def get_tile(x, y, mapdb):
    print("get_tile", x, y)

    # Use the get_map_data function to retrieve data for the given position
    map_entities = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)

    # If map_entities is not a list (either a single dict or None), convert it into a list
    if not isinstance(map_entities, list):
        map_entities = [map_entities] if map_entities else []

    # If no entities are found at the given position, provide a default "empty" entity
    if not map_entities:
        map_entities = [{
            f"{x},{y}": {
                "type": "empty",
                "control": "nobody",
                "hp": 0,  # CLUTCH todo
            }
        }]

    for entity in map_entities:
        print("entity", entity)

    return map_entities


def get_user_data(user, usersdb):
    data = get_user(user, usersdb)
    username = list(data.keys())[0]
    user_data = data[username]
    return user_data


def occupied_by(x, y, what, mapdb):
    # Use the get_map_data function to check if the given position is occupied by the specified entity type
    entity_map = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)

    if entity_map:
        # Access the entity at the specified position
        entity = entity_map.get(f"{x},{y}")

        if entity and entity.get("type") == what:
            return True

    return False


def has_resources(user_data, cost):
    for resource, amount in cost.items():
        if user_data.get(resource, 0) < amount:
            return False
    return True


# Defining cost structures for entities
building_costs = {
    "house": {"wood": 50},
    "inn": {"wood": 50},
    # Add more entities and their cost structures here
}


class Enemy:
    def __init__(self, hp, armor, min_damage=0, max_damage=2, alive=True, kill_chance=0.01):
        self.hp = hp
        self.armor = armor
        self.alive = alive
        self.kill_chance = kill_chance
        self.min_damage = min_damage
        self.max_damage = max_damage

    def is_alive(self):
        return self.alive

    def roll_damage(self):
        return random.randint(self.min_damage, self.max_damage)


class Boar(Enemy):
    def __init__(self):
        super().__init__(hp=100, max_damage=1, armor=0)
        self.type = "boar"


class Scenery:
    def __init__(self, hp):
        self.hp = hp
        self.type = "forest"


class Tree(Scenery):
    def __init__(self):
        super().__init__(hp=100)


def build(entity, name, user, mapdb, usersdb):
    user_data = get_user_data(user, usersdb)
    occupied = get_tile(user_data["x_pos"], user_data["y_pos"], mapdb)

    for entry in occupied:
        if user_data["action_points"] < 1:
            return "Not enough action points to build"
        elif entry[f"{user_data['x_pos']},{user_data['y_pos']}"]["type"] != "empty":
            return "Cannot build here"

        if entity not in building_costs:
            return "Building procedure not yet defined"

        if not has_resources(user_data, building_costs[entity]):
            return f"Not enough resources to build {entity}"

        # Deduct resources
        for resource, amount in building_costs[entity].items():
            user_data[resource] -= amount

        # Conditionally increase the pop_lim based on the entity
        if entity == "house":
            user_data["pop_lim"] += 10

        # Update user's data
        updated_values = {
            "action_points": user_data["action_points"] - 1,
            "wood": user_data["wood"],
            "pop_lim": user_data.get("pop_lim", None)  # Only update if the key exists
        }

        update_user_data(user=user,
                         updated_values=updated_values,
                         user_data_dict=usersdb)

        # Prepare and update the map data for the entity
        entity_data = {
            "type": entity,
            "name": name,
            "hp": 100,
            "size": 1,
            "control": user,
        }
        data = {f"{user_data['x_pos']},{user_data['y_pos']}": entity_data}
        update_user_data(user=user,
                         updated_values={"construction": data},
                         user_data_dict=usersdb)
        insert_map_data(mapdb, data)

        return f"Successfully built {entity}"


def move(user, entry, axis_limit, user_data, users_dict):
    move_map = {
        "left": (-1, "x_pos"),
        "right": (1, "x_pos"),
        "down": (1, "y_pos"),
        "up": (-1, "y_pos")
    }

    if entry in move_map:
        direction, axis_key = move_map[entry]
        new_pos = user_data.get(axis_key, 0) + direction

        if user_data.get("action_points", 0) > 0 and 1 <= new_pos <= axis_limit:
            update_user_data(user, {axis_key: new_pos, "action_points": user_data["action_points"] - 1}, users_dict)
            return True
    return False


def attempt_rest(user, user_data, hours_arg, usersdb, mapdb):
    hours = int(hours_arg)
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
    proper_tile = occupied_by(x_pos, y_pos, what="inn", mapdb=mapdb)

    # Check if the user is able to rest
    can_rest = proper_tile and user_data["action_points"] >= hours and user_data["hp"] < 100

    if can_rest:
        new_hp = min(user_data["hp"] + hours, 100)  # Ensures HP doesn't exceed 100
        new_ap = user_data["action_points"] - hours
        update_user_data(user=user,
                         updated_values={"hp": new_hp, "action_points": new_ap},
                         user_data_dict=usersdb)
        return "You feel more rested"

    elif user_data["hp"] >= 100:
        return "You are already fully rested"
    elif not proper_tile:
        return "You cannot rest here, inn required"
    else:
        return "Out of action points to rest"


class TileActions:
    def get(self, type):
        if type == "inn":
            actions = [{"name": "sleep 10 hours", "action": "/rest?hours=10"},
                       {"name": "sleep 20 hours", "action": "/rest?hours=20"},
                       {"name": "conquer", "action": f"/conquer?target={type}"}]
        elif type == "forest":
            actions = [{"name": "chop", "action": "/chop"},
                       {"name": "conquer", "action": f"/conquer?target={type}"}]
        elif type == "house":
            actions = [{"name": "conquer", "action": f"/conquer?target={type}"}]
        elif type == "boar":
            actions = [{"name": "slay", "action": f"/fight?target={type}"}]
        else:
            actions = []

        return actions


class Descriptions:
    def get(self, type):
        if type == "axe":
            description = "A tool to cut wood with in the forest."
        elif type == "house":
            description = "A place for people to live in. Building a house increases your population limit. Cost: 🪵50"
        elif type == "inn":
            description = "A place to rest and restore health."
        else:
            description = "Description missing."

        return description


def has_item(data, item_type):
    items = data.get('items', [])

    for item in items:
        if item.get("type") == item_type:
            return True

    return False


def update_map_data(update_data, map_data_dict):
    print("update_map_data", update_data)

    # Get coordinates and data from the provided input
    coords = list(update_data.keys())[0]
    tile_data = update_data[coords]

    # Split the coords into x and y positions
    x, y = map(int, coords.split(','))

    # Create a key using the coordinates
    key = f"{x},{y}"

    # Check if the key exists in the map_data_dict
    if key in map_data_dict:
        # Update only the 'control' key
        map_data_dict[key]["control"] = tile_data["control"]
    else:
        print(f"No data found at the given coordinates {x, y}.")


def remove_from_map(coords, entity_type, map_data_dict):
    print("remove_from_map", coords, entity_type)

    # Create a key using the coordinates
    key = coords

    # Check if the key exists in the map_data_dict
    if key in map_data_dict:
        # Check if the type matches
        if map_data_dict[key].get("type") == entity_type:
            # Remove the key from the map_data_dict
            del map_data_dict[key]
            print(f"Entity of type {entity_type} at coordinates {coords} has been removed.")
        else:
            print(f"Entity of type {entity_type} not found at the given coordinates {coords}.")
    else:
        print(f"No data found at the given coordinates {coords}.")


def insert_map_data(existing_data, new_data):
    print("insert_map_data", new_data)

    for coord, construction_info in new_data.items():
        if coord in existing_data:
            # If the coordinate already exists, update its values
            existing_data[coord].update(construction_info)
        else:
            # If the coordinate doesn't exist, create a new entry
            existing_data[coord] = construction_info


def get_user(user, user_data_dict, get_construction=True):
    # Check if the user exists in the user_data_dict
    if user not in user_data_dict:
        print(f"User {user} not found in the dictionary.")
        return None

    user_entry = user_data_dict[user]

    # Extract x_pos, y_pos, and other data from user_entry
    x_pos = user_entry.get("x_pos", 0)
    y_pos = user_entry.get("y_pos", 0)
    data = {k: v for k, v in user_entry.items() if k not in ["x_pos", "y_pos", "construction"]}

    # get the "construction" data only if get_construction is True
    construction = user_entry["construction"] if get_construction and "construction" in user_entry else {}

    user_data = {
        user: {
            "x_pos": x_pos,
            "y_pos": y_pos,
            **data,
            "construction": construction
        }
    }

    return user_data


def update_user_data(user, updated_values, user_data_dict):
    print("update_user_data", user, updated_values)

    if user not in user_data_dict:
        print("User not found")
        return

    user_entry = user_data_dict[user]

    for key, value in updated_values.items():
        if key == "construction" and "construction" in user_entry and isinstance(value, dict):
            for coord, construction_info in value.items():
                user_entry["construction"][coord] = construction_info
        else:
            user_entry[key] = value


def remove_from_user(user, construction_coordinates, user_data_dict):
    key = f"{construction_coordinates['x_pos']},{construction_coordinates['y_pos']}"

    if user not in user_data_dict:
        print("User not found")
        return

    user_data = user_data_dict[user]

    if "construction" in user_data and isinstance(user_data["construction"], dict):
        user_data["construction"].pop(key, None)


def get_map_data_limit(x_pos, y_pos, map_data_dict, distance=500):
    for coords, data_str in map_data_dict.items():
        x_map, y_map = map(int, coords.split(","))
        if (x_map - x_pos) ** 2 + (y_map - y_pos) ** 2 <= distance ** 2:
            map_data_dict[coords] = data_str
    return map_data_dict


def get_surrounding_map_and_user_data(user, user_data_dict, map_data_dict):
    # Check if the specified user is in the user_data_dict
    if user not in user_data_dict:
        return {"error": "User not found."}

    # Fetch the map data for the specified user and transform it into a dictionary indexed by "x:y"
    user_map_data_dict = get_map_data_limit(user_data_dict[user]['x_pos'],
                                            user_data_dict[user]['y_pos'],
                                            map_data_dict=map_data_dict)

    # Prepare the final result as a dictionary with two keys
    result = {
        "users": user_data_dict,  # Include all users' data
        "construction": user_map_data_dict  # This is now a dictionary indexed by "x:y"
    }

    return result
