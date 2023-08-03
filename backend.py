import sqlite3
from hashlib import blake2b
import string
import os
import json
import random

users_db = sqlite3.connect("users.db")
users_db_cursor = users_db.cursor()


def generate_entities(entity_type, probability, additional_entity_data=None, size=101, every=10):
    if not os.path.exists("environment/entities.json"):
        # Initialize a new list of entities
        entities = []

        # Generate entities
        for x_pos in range(1, size, every):  # Starting from 1 and assuming the environment has a width of 100 blocks
            for y_pos in range(1, size,
                               every):  # Starting from 1 and assuming the environment has a height of 100 blocks
                if random.random() <= probability:
                    # Add the new entity to the list
                    new_entity = {"type": entity_type,
                                  "x_pos": x_pos,
                                  "y_pos": y_pos,
                                  "control": "N/A",
                                  **additional_entity_data}
                    entities.append(new_entity)

        # Write the new list of entities to a file
        with open("environment/entities.json", "w") as outfile:
            json.dump({"construction": entities}, outfile, indent=2)


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
    on_tile = []

    for folder in ["users", "environment"]:
        for file in os.listdir(folder):
            with open(os.path.join(folder, file), "r") as infile:
                contents = json.load(infile)
                for entry in contents["construction"]:
                    if entry["y_pos"] == y and entry["x_pos"] == x:
                        on_tile.append(entry)

    return on_tile


def has_item(player, item_name):
    with open(f"users/{hashify(player)}.json", "r") as infile:
        contents = json.load(infile)
        for item in contents["items"]:
            if item.get("type") == item_name:
                return True
        return False


def has_ap(player):
    with open(f"users/{hashify(player)}.json", "r") as infile:
        contents = json.load(infile)
        if contents["action_points"] > 0:
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
        "actions": [],
        "control": user,

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
            "action_points": 5000,
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


def update_user_file(user, updated_values):
    file_path = f"users/{hashify(user)}.json"
    with open(file_path, "r") as infile:
        file = json.load(infile)

    # Update the resources
    if "resources" in updated_values:
        for key in updated_values["resources"]:
            file["resources"][key] = updated_values["resources"][key]

    # Update the action points
    if "action_points" in updated_values:
        file["action_points"] = updated_values["action_points"]

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
