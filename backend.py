import os
import random
import sqlite3
import string
from hashlib import blake2b

import sqlite
from sqlite import insert_map_data, update_user_data

if not os.path.exists("db"):
    os.mkdir("db")


def generate_entities(entity_type, probability, additional_entity_data=None, size=101, every=10):
    for x_pos in range(1, size, every):
        for y_pos in range(1, size, every):
            if random.random() <= probability:
                data = {"type": entity_type}
                print(f"Generating {data} on {x_pos}, {y_pos}")
                if additional_entity_data:
                    data.update(additional_entity_data)
                sqlite.save_map_data(x_pos=x_pos, y_pos=y_pos, data=data)


def hashify(data):
    hashified = blake2b(data.encode(), digest_size=15).hexdigest()
    return hashified


def load_tile(x, y):
    print("load_tile", x, y)

    # Use the get_map_data function to retrieve data for the given position
    entities_from_db = sqlite.get_map_data(x_pos=x, y_pos=y)

    # If entities_from_db is not a list (either a single dict or None), convert it into a list
    if not isinstance(entities_from_db, list):
        entities_from_db = [entities_from_db] if entities_from_db else []

    # If no entities are found at the given position, provide a default "empty" entity
    if not entities_from_db:
        entities_from_db = [{
            f"{x},{y}": {
                "type": "empty",
                "control": "nobody",
                "hp": 0,  # CLUTCH todo
            }
        }]

    for entity in entities_from_db:
        print("entity", entity)

    return entities_from_db



from sqlite import load_user


def get_user_data(user):
    data = load_user(user)
    username = list(data.keys())[0]
    user_data = data[username]
    return user_data


def occupied_by(x, y, what):
    # Use the get_map_data function to check if the given position is occupied by the specified entity type
    entity_map = sqlite.get_map_data(x_pos=x, y_pos=y)

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
    "inn": {"wood": 50, "stone": 10},
    # Add more entities and their cost structures here
}


def build(entity, name, user):
    user_data = get_user_data(user)
    occupied = load_tile(user_data["x_pos"], user_data["y_pos"])

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
        if "stone" in user_data:
            updated_values["stone"] = user_data["stone"]

        update_user_data(user=user, updated_values=updated_values)

        # Prepare and update the map data for the entity
        entity_data = {
            "type": entity,
            "name": name,
            "hp": 100,
            "size": 1,
            "control": user,
        }
        data = {f"{user_data['x_pos']},{user_data['y_pos']}": entity_data}
        update_user_data(user=user, updated_values={"construction": data})
        insert_map_data("db/map_data.db", data)

        return f"Successfully built {entity}"


def move(user, entry, axis_limit, user_data):
    move_map = {
        "left": (-1, "x_pos"),
        "right": (1, "x_pos"),
        "down": (1, "y_pos"),
        "up": (-1, "y_pos")
    }

    if entry in move_map:
        direction, axis_key = move_map[entry]
        new_pos = user_data[axis_key] + direction
        if user_data["action_points"] > 0 and 1 <= new_pos <= axis_limit:
            update_user_data(user, {axis_key: new_pos, "action_points": user_data["action_points"] - 1})
            return True
    return False


def attempt_rest(user, user_data, hours_arg):
    hours = int(hours_arg)
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]
    proper_tile = occupied_by(x_pos, y_pos, what="inn")

    # Check if the user is able to rest
    can_rest = proper_tile and user_data["action_points"] >= hours and user_data["hp"] < 100

    if can_rest:
        new_hp = min(user_data["hp"] + hours, 100)  # Ensures HP doesn't exceed 100
        new_ap = user_data["action_points"] - hours
        update_user_data(user=user, updated_values={"hp": new_hp, "action_points": new_ap})
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


def cookie_get():
    filename = "cookie_secret"
    if not os.path.exists(filename):
        cookie_secret = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(30))
        with open(filename, "w") as infile:
            infile.write(cookie_secret)
    else:
        with open(filename) as infile:
            cookie_secret = infile.read()
    return cookie_secret
