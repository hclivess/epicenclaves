import sqlite3
from hashlib import blake2b
import string
import os
import json
import random
import sqlite

users_db = sqlite3.connect("users.db")
users_db_cursor = users_db.cursor()


def generate_entities(entity_type, probability, additional_entity_data=None, size=101, every=10):
    for x_pos in range(1, size, every):
        for y_pos in range(1, size, every):
            if random.random() <= probability:
                data = {"type": entity_type}
                if additional_entity_data:
                    data.update(additional_entity_data)
                sqlite.save_map_data(position=(x_pos, y_pos), data=data, control=None)


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
    # Use the get_map_data function to retrieve data for the given position
    entities = sqlite.get_map_data(position=(x, y))

    entity_data_list = []
    for entity in entities:
        if "data" in entity:
            entity_data_list.append({"x_pos": entity["x_pos"],
                                     "y_pos": entity["y_pos"],
                                     "data": entity["data"],
                                     "control": entity["control"]})

    return entity_data_list


def has_item(player, item_name):
    # Connect to the database
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Get the row for the specified player from the user_data table
    cursor.execute("SELECT items FROM user_data WHERE username=?", (player,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    if result:
        items_str = result[0]
        items = json.loads(items_str)
        for item in items:
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
    # Use the get_map_data function to check if the given position is occupied by the specified entity type
    data = sqlite.get_map_data(position=(x, y))
    return data and data["data"].get("type") == what


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
    # Connect to the database
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                        username TEXT PRIMARY KEY,
                        type TEXT,
                        age TEXT,
                        img TEXT,
                        x_pos INTEGER,
                        y_pos INTEGER,
                        exp INTEGER,
                        hp INTEGER,
                        armor INTEGER,
                        action_points INTEGER,
                        wood INTEGER,
                        food INTEGER,
                        bismuth INTEGER,
                        items TEXT,
                        construction TEXT
                      )''')

    # Convert the position tuple to a string representation
    x_pos, y_pos = 1, 1  # Replace these with the actual x_pos and y_pos values

    # Convert items dictionary to a JSON string
    items_data = [{"type": "axe", "desc": "A tool to cut wood with in the forest"}]
    items_str = json.dumps(items_data)

    # Insert the user data into the database
    cursor.execute('''INSERT OR IGNORE INTO user_data (username, type, age, img, x_pos, y_pos, exp, hp, armor, action_points, wood, food, bismuth, items, construction)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                   (user, "player", "0", "img/pp.png", x_pos, y_pos, 0, 100, 0, 5000, 0, 0, 0, items_str, "[]"))

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def load_user_file(user):
    # Connect to the database
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Retrieve the user data for the given username
    cursor.execute("SELECT * FROM user_data WHERE username=?", (user,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    if result:
        username, user_type, age, img, x_pos, y_pos, exp, hp, armor, action_points, wood, food, bismuth, items_str, construction_str = result

        # Convert the items string back to a list of dictionaries
        items = json.loads(items_str)

        # Convert the construction string back to a list
        construction = json.loads(construction_str)

        return {
            "username": username,
            "type": user_type,
            "age": age,
            "img": img,
            "x_pos": x_pos,
            "y_pos": y_pos,
            "exp": exp,
            "hp": hp,
            "armor": armor,
            "action_points": action_points,
            "wood": wood,
            "food": food,
            "bismuth": bismuth,
            "items": items,
            "construction": construction
        }
    else:
        return None


def load_files():
    all_files = []

    # Load data from user_data.db
    conn_user = sqlite3.connect("user_data.db")
    cursor_user = conn_user.cursor()
    cursor_user.execute("SELECT * FROM user_data")
    results_user = cursor_user.fetchall()

    for result_user in results_user:
        username, user_type, age, img, x_pos, y_pos, exp, hp, armor, action_points, wood, food, bismuth, items_str, construction_str = result_user

        # Convert the items string back to a list of dictionaries
        items = json.loads(items_str)

        # Convert the construction string back to a list
        construction = json.loads(construction_str)

        user_data = {
            "username": username,
            "type": user_type,
            "age": age,
            "img": img,
            "x_pos": x_pos,
            "y_pos": y_pos,
            "exp": exp,
            "hp": hp,
            "armor": armor,
            "action_points": action_points,
            "wood": wood,
            "food": food,
            "bismuth": bismuth,
            "items": items,
            "construction": construction
        }

        all_files.append(user_data)

    conn_user.close()

    # Load data from map_data.db
    conn_map = sqlite3.connect("map_data.db")
    cursor_map = conn_map.cursor()
    cursor_map.execute("SELECT * FROM map_data")
    results_map = cursor_map.fetchall()

    for result_map in results_map:
        position_str, data_str, controlled_by = result_map
        data = json.loads(data_str)
        x_pos, y_pos = map(int, position_str.split(","))
        map_data = {"position": (x_pos, y_pos), "data": data, "controlled_by": controlled_by}
        all_files.append(map_data)

    conn_map.close()

    return all_files



def update_user_file(user, updated_values):
    # Use the save_map_data function to update user data in the SQLite database
    sqlite.save_map_data(position=user,
                         data=updated_values,
                         control=None)


def append_user_file(user, append_values, what):
    # Use the get_map_data function to retrieve existing user data and then append the new values
    data = sqlite.get_map_data(position=user)
    if data:
        data["data"][what].append(append_values)
        sqlite.save_map_data(position=user,
                             data=data["data"],
                             control=None)


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
