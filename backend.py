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


def tile_occupied(x, y):
    print("tile_occupied", x, y)
    # Use the get_map_data function to retrieve data for the given position
    entity = sqlite.get_map_data(x_pos=x, y_pos=y)

    # If an entity is found at the given position, return its data
    if not entity:
        entity = {f"{x},{y}": {
            "type": "empty",
            "control": "nobody",
            "hp": 0,  # CLUTCH todo
        }}

    print("entity", entity)
    # If there are no entities with "data", return a placeholder dict
    return entity


def occupied_by(x, y, what):
    # Use the get_map_data function to check if the given position is occupied by the specified entity type
    entity_map = sqlite.get_map_data(x_pos=x, y_pos=y)

    # Access the entity at the specified position
    entity = entity_map.get(f"{x},{y}")

    if entity and entity.get("type") == what:
        return True

    return False


def build(entity, name, user, user_data):
    print("build", entity, name, user, user_data)
    # Prepare the entity data based on the entity type
    entity_data = {
        "type": entity,
    }

    # Update user data
    data = {
        f"{user_data['x_pos']},{user_data['y_pos']}": {
            "name": name,
            "hp": 100,
            "size": 1,
            "control": user,
            **entity_data
        }
    }

    update_user_data(user=user, updated_values={"construction": data})
    insert_map_data("db/map_data.db", data)


class Actions:
    def get(self, type):
        if type == "inn":
            actions = [{"name": "sleep 10 hours", "action": "/rest?hours=10"},
                       {"name": "sleep 20 hours", "action": "/rest?hours=20"},
                       {"name": "conquer", "action": "/conquer"}]
        elif type == "forest":
            actions = [{"name": "chop", "action": "/chop"},
                       {"name": "conquer", "action": "/conquer"}]
        elif type == "house":
            actions = [{"name": "conquer", "action": "/conquer"}]
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
