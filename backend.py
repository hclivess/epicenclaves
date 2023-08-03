import sqlite3
from hashlib import blake2b
import os
import string
import json
import random

users_db = sqlite3.connect("users.db")
users_db_cursor = users_db.cursor()

import os
import json
import random


def generate_entities(entity_type, probability, entity_data, size=101, every=10):
    # Check if the entity file already exists, if not, create it with an empty list of entities.
    if not os.path.exists("environment/entities.json"):
        with open("environment/entities.json", "w") as outfile:
            json.dump({"construction": []}, outfile, indent=2)

    # Load the existing entity file
    with open("environment/entities.json", "r") as infile:
        entity_data = json.load(infile)

    # Create a set to keep track of grid fields where entities have already been generated
    generated_positions = {(item["x_pos"], item["y_pos"]) for item in entity_data["construction"]}

    # Generate and add new entities to the entity data
    for x_pos in range(1, size, every):  # Starting from 1 and assuming the environment has a width of 100 blocks
        for y_pos in range(1, size, every):  # Starting from 1 and assuming the environment has a height of 100 blocks
            # Skip generating if entity already exists on this grid field
            if (x_pos, y_pos) in generated_positions:
                continue

            if random.random() <= probability:
                # Add the new entity to the entity data
                new_entity = {"type": entity_type, "x_pos": x_pos, "y_pos": y_pos}
                entity_data["construction"].append(new_entity)
                # Add the position to the set of generated positions
                generated_positions.add((x_pos, y_pos))

    # Save the updated entities back to the file
    with open("environment/entities.json", "w") as outfile:
        json.dump(entity_data, outfile, indent=2)


def check_users_db():
    users_db.execute("CREATE TABLE IF NOT EXISTS users (username STRING PRIMARY KEY, passhash STRING)")
    users_db.commit()


def hash_password(password):
    salt = "vGY13MMUH4khKGscQOOg"
    passhash = blake2b(digest_size=30)
    passhash.update((password + salt).encode())
    return passhash.hexdigest()


def hashify(data):
    hashified = blake2b(data.encode(), digest_size=15).hexdigest()
    return hashified


def on_tile(x, y):
    """in the future consider map index"""
    on_tile = None

    for folder in ["users", "environment"]:
        for file in os.listdir(folder):
            with open(os.path.join(folder, file), "r") as infile:
                contents = json.load(infile)
                for entry in contents["construction"]:
                    if entry["y_pos"] == y and entry["x_pos"] == x:
                        on_tile = entry
                        break

    return on_tile


def has_item(player, item_name):
    with open(f"users/{hashify(player)}.json", "r") as infile:
        contents = json.load(infile)
        for item in contents["items"]:
            if item.get("type") == item_name:
                return True
        return False


def occupied_by(x, y, what):
    """in the future consider map index"""
    for folder in ["users", "environment"]:
        for file in os.listdir(folder):
            with open(os.path.join(folder, file), "r") as infile:
                contents = json.load(infile)
                for entry in contents["construction"]:
                    if entry["y_pos"] == y and entry["x_pos"] == x and what == entry["type"]:
                        return True

    return False


def build(entity, name, user, file):
    entity_data = {
        "house": {"type": "house"},
        "mine": {"type": "mine"},
        "farm": {"type": "farm"},
        "barracks": {"type": "barracks"},
        "sawmill": {"type": "sawmill"},
        "blacksmith": {"type": "blacksmith"}
    }

    append_user_file(user, {
        "x_pos": file["x_pos"],
        "y_pos": file["y_pos"],
        "name": name,
        "hp": 100,
        "size": 1,
        **entity_data.get(entity, {})
    }, what="construction")


def create_user_file(user):
    if not os.path.exists("users"):
        os.mkdir("users")

    with open(f"users/{hashify(user)}.json", "w") as outfile:
        json.dump({
            "username": user,
            "type": "player",
            "age": "0",
            "img": "img/pp.png",
            "y_pos": 1,
            "x_pos": 1,
            "exp": 0,
            "hp": 100,
            "armor": 0,
            "construction": [],
            "action_points": 50,
            "resources": {
                "wood": 0,
                "food": 0,
                "bismuth": 0
            },
            "items": [{"type": "axe", "desc": "A tool to cut wood with in the forest"}]
        }, outfile, indent=2)


def load_user_file(user):
    with open(f"users/{hashify(user)}.json", "r") as infile:
        return json.load(infile)


def load_files():
    all_files = []
    for folder in ["users", "environment"]:
        for file in os.listdir(folder):
            with open(os.path.join(folder, file), "r") as infile:
                all_files.append(json.load(infile))

    return all_files


def update_user_file(user, values, updated_values):
    file_path = f"users/{hashify(user)}.json"
    with open(file_path, "r") as infile:
        file = json.load(infile)

    file[values] = updated_values

    with open(file_path, "w") as outfile:
        json.dump(file, outfile, indent=2)


def append_user_file(user, append_values, what):
    file_path = f"users/{hashify(user)}.json"
    with open(file_path, "r") as infile:
        file = json.load(infile)

    file[what].append(append_values)

    with open(file_path, "w") as outfile:
        json.dump(file, outfile, indent=2)


def add_user(user, password):
    users_db.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user, hash_password(password)))
    users_db.commit()


def exists_user(user):
    users_db_cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
    result = users_db_cursor.fetchall()

    return bool(result)


def login_validate(user, password):
    users_db_cursor.execute("SELECT * FROM users WHERE username = ? AND passhash = ?", (user, hash_password(password)))
    result = users_db_cursor.fetchall()

    return bool(result)


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
