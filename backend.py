import json
import os
import random
import sqlite3
import string
from hashlib import blake2b

import sqlite

users_db = sqlite3.connect("db/auth.db")
users_db_cursor = users_db.cursor()


def generate_entities(entity_type, probability, additional_entity_data=None, size=101, every=10):
    for x_pos in range(1, size, every):
        for y_pos in range(1, size, every):
            if random.random() <= probability:
                data = {"type": entity_type}
                print(f"Generating {data} on {x_pos}, {y_pos}")
                if additional_entity_data:
                    data.update(additional_entity_data)
                sqlite.save_map_data(x_pos=x_pos, y_pos=y_pos, data=data)


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
    entities = sqlite.get_map_data(x_pos=x, y_pos=y)

    entity_data_list = []
    for entity in entities:
        if "data" in entity:
            entity_data_list.append({
                "x_pos": entity["x_pos"],
                "y_pos": entity["y_pos"],
                "data": entity["data"],
            })

    return entity_data_list



def has_item(player, item_name):
    # Connect to the database
    conn = sqlite3.connect("db/user_data.db")
    cursor = conn.cursor()

    # Get the row for the specified player from the user_data table
    cursor.execute("SELECT data FROM user_data WHERE username=?", (player,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    if result:
        data_str = result[0]
        data = json.loads(data_str)
        items = data.get('items', [])

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
    entities = sqlite.get_map_data(x_pos=x, y_pos=y)
    for entity in entities:
        if entity["data"].get("type") == what:
            return True
    return False


def insert_map_data(db_file, data):
    # Connect to the database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Prepare the data dictionary to be stored as a JSON string
    data_str = json.dumps({
        "name": data["name"],
        "hp": data["hp"],
        "size": data["size"],
        "control": data["control"],
        "type": data["type"]
    })

    # Prepare and execute the SQL query to insert data into the map_data table
    cursor.execute(
        "INSERT OR REPLACE INTO map_data (x_pos, y_pos, data) VALUES (?, ?, ?)",
        (data['x_pos'], data['y_pos'], data_str)
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
        "control": user,
        **entity_data
    }

    update_user_data(user=user, updated_values={"construction": data})
    insert_map_data("db/map_data.db", data)


def create_user_file(user):
    # Connect to the database
    conn = sqlite3.connect("db/user_data.db")
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                        username TEXT PRIMARY KEY,
                        x_pos INTEGER,
                        y_pos INTEGER,
                        data TEXT
                      )''')

    # Convert the position tuple to a string representation
    x_pos, y_pos = 1, 1  # Replace these with the actual x_pos and y_pos values

    # Prepare the data dictionary
    data = {
        "type": "player",
        "age": "0",
        "img": "img/pp.png",
        "exp": 0,
        "hp": 100,
        "armor": 0,
        "action_points": 5000,
        "wood": 0,
        "food": 0,
        "bismuth": 0,
        "items": [{"type": "axe"}],
        "construction": [],
        "pop_lim": 0
    }
    data_str = json.dumps(data)

    # Insert the user data into the database
    cursor.execute('''INSERT OR IGNORE INTO user_data (username, x_pos, y_pos, data)
                      VALUES (?, ?, ?, ?)''',
                   (user, x_pos, y_pos, data_str))

    # Commit changes and close the connection
    conn.commit()
    conn.close()






class Actions:
    def get(self, type):
        if type == "inn":
            actions = [{"name": "sleep 10 hours", "action": "/rest?hours=10"},
                       {"name": "sleep 20 hours", "action": "/rest?hours=20"}]
        elif type == "forest":
            actions = [{"name": "chop", "action": "/chop"}]
        else:
            actions = []

        return actions


class Descriptions:
    def get(self, type):
        if type == "axe":
            description = "A tool to cut wood with in the forest."
        elif type == "house":
            description = "A place for people to live in. Building a house increases your population limit."
        elif type == "inn":
            description = "A place to rest and restore health."
        else:
            description = "Description missing."

        return description


def load_user_data(user):
    # Connect to the database
    conn = sqlite3.connect("db/user_data.db")
    cursor = conn.cursor()

    # Retrieve the user data for the given username
    cursor.execute("SELECT * FROM user_data WHERE username=?", (user,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    if result:
        username, x_pos, y_pos, data_str = result

        # Convert the data string back to a dictionary
        data = json.loads(data_str)

        # Prepare the final result
        user_data = {
            "username": username,
            "x_pos": x_pos,
            "y_pos": y_pos
        }
        user_data.update(data)

        return user_data
    else:
        return None


def load_map(user):
    users_data = []  # Create an empty list to store user data

    # Load data from db/user_data.db
    conn_user = sqlite3.connect("db/user_data.db")
    cursor_user = conn_user.cursor()
    cursor_user.execute("SELECT * FROM user_data WHERE username = ?", (user,))
    result_user = cursor_user.fetchone()

    if not result_user:
        print("User not found")
        return

    username, x_pos, y_pos, data_str = result_user

    # Convert the data string back to a dictionary
    data = json.loads(data_str)

    # Prepare the user_data dictionary
    user_data = {
        "username": username,
        "x_pos": x_pos,
        "y_pos": y_pos
    }
    user_data.update(data)  # This will add the data from 'data' to 'user_data'

    users_data.append(user_data)

    conn_user.close()

    # Load data from db/map_data.db
    conn_map = sqlite3.connect("db/map_data.db")
    cursor_map = conn_map.cursor()

    # Calculate the square of the distance
    distance_squared = 500 ** 2

    # Query to fetch map data within a distance of 500 from the user
    cursor_map.execute("""
        SELECT x_pos, y_pos, data 
        FROM map_data 
        WHERE ((x_pos - ?)*(x_pos - ?) + (y_pos - ?)*(y_pos - ?)) <= ?
    """, (x_pos, x_pos, y_pos, y_pos, distance_squared))

    results_map = cursor_map.fetchall()

    map_data = []
    for result_map in results_map:
        x_map, y_map, data_str = result_map
        data = json.loads(data_str)

        map_info = {
            "x_pos": x_map,
            "y_pos": y_map,
            **data  # Use the unpacking operator to merge the 'data' dictionary into 'map_info'
        }

        map_data.append(map_info)

    conn_map.close()

    # Combine users_data and map_data into a single list
    total_data = users_data + [{"construction": map_data}]
    return total_data





def add_user(user, password):
    users_db.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user, hash_password(password)))
    users_db.commit()


def exists_user(user):
    users_db_cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
    result = users_db_cursor.fetchall()

    return bool(result)

def update_user_data(user, updated_values):
    # Connect to the database
    conn = sqlite3.connect("db/user_data.db")
    cursor = conn.cursor()

    # Fetch the current user data from the database
    cursor.execute("SELECT data FROM user_data WHERE username=?", (user,))
    result = cursor.fetchone()

    if not result:
        print("User not found")
        return

    data_str = result[0]
    # Convert the data string back to a dictionary
    data = json.loads(data_str)

    # Iterate over the updated values and update them in the data dictionary
    for key, value in updated_values.items():
        # Check if key is 'construction'
        if key == "construction" and key in data and isinstance(data[key], list):
            # Append the new value to the existing list
            data[key].append(value)
        else:
            data[key] = value  # else just update the value

    # Convert the updated data back to a JSON string
    updated_data_str = json.dumps(data)

    # Update the user data in the database
    cursor.execute("UPDATE user_data SET data=? WHERE username=?", (updated_data_str, user))

    # Commit changes and close the connection
    conn.commit()
    conn.close()



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
