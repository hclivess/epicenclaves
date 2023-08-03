import json
import os
import random
import sqlite3
import string
from hashlib import blake2b

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
    entities = sqlite.get_map_data(position=(x, y))
    for entity in entities:
        if entity["data"].get("type") == what:
            return True
    return False



def insert_map_data(db_file, data):
    # Connect to the database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Prepare and execute the SQL query to insert data into the map_data table
    cursor.execute(
        "INSERT INTO map_data (position, data, control) VALUES (?, ?, ?)",
        (f"{data['x_pos']},{data['y_pos']}",
         f'{{"name": "{data["name"]}", "hp": {data["hp"]}, "size": {data["size"]}, "actions": {data["actions"]}, "control": "{data["control"]}", "type": "{data["type"]}"}}',
         data["control"])
    )

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def build(entity, name, user, file):
    # Prepare the entity data based on the entity type
    entity_data = {
        "type": entity,
    }

    # Update user data
    data = {
        "x_pos": file["x_pos"],
        "y_pos": file["y_pos"],
        "name": name,
        "hp": 100,
        "size": 1,
        "actions": [],
        "control": user,
        **entity_data
    }

    update_user_file(user, data, column="construction")
    insert_map_data("map_data.db", data)


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


import sqlite3


def load_files():
    all_files = {}

    # Load data from user_data.db
    conn_user = sqlite3.connect("user_data.db")
    cursor_user = conn_user.cursor()
    cursor_user.execute("SELECT * FROM user_data")
    results_user = cursor_user.fetchall()

    users_data = []
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
            "resources": {"bismuth": bismuth, "wood": wood, "food": food},
            "items": items,
            "construction": construction
        }

        users_data.append(user_data)

    all_files["user_data"] = users_data
    conn_user.close()

    # Load data from map_data.db
    conn_map = sqlite3.connect("map_data.db")
    cursor_map = conn_map.cursor()
    cursor_map.execute("SELECT position, data, control FROM map_data")
    results_map = cursor_map.fetchall()

    map_data = []
    for result_map in results_map:
        position_str, data_str, control = result_map
        data = json.loads(data_str)

        x_pos, y_pos = map(int, position_str.split(","))
        map_info = {
            "x_pos": x_pos,
            "y_pos": y_pos,
            "data": data
        }

        try:
            map_info["control"] = json.loads(control) if control else None
        except json.JSONDecodeError:
            map_info["control"] = None

        map_data.append(map_info)

    all_files["construction"] = map_data
    conn_map.close()

    return all_files

def update_user_file(user, updated_values, column):
    # Connect to the database
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()

    # Retrieve the existing data for the user
    cursor.execute(f"SELECT {column} FROM user_data WHERE username=?", (user,))
    result = cursor.fetchone()

    # Convert the column string back to a list
    column_str = result[0]
    column_data = json.loads(column_str)

    # Update the data with the new values
    column_data.append(updated_values)

    # Serialize the updated data list back to a string for storage
    updated_column_str = json.dumps(column_data)

    # Update the specified column with the new data
    cursor.execute(f"UPDATE user_data SET {column}=? WHERE username=?", (updated_column_str, user))

    # Commit changes and close the connection
    conn.commit()
    conn.close()




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
