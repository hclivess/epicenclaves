import json
import os
import random
import sqlite3
import string
from hashlib import blake2b

if not os.path.exists("db"):
    os.mkdir("db")
users_db = sqlite3.connect("db/auth.db")
users_db_cursor = users_db.cursor()


def create_game_database():
    # Create the 'db' directory if it doesn't exist
    if not os.path.exists('db'):
        os.makedirs('db')

    # Connect to the SQLite database
    db_path = os.path.join('db', 'game_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create the 'game' table with 'turn' column and insert default value
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game (
            turn INTEGER DEFAULT 0
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def update_turn(turn_value):
    # Connect to the SQLite database
    db_path = os.path.join('db', 'game_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Update the 'turn' value in the 'game' table
    cursor.execute('''
        UPDATE game
        SET turn = ?
    ''', (turn_value,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


def hash_password(password):
    salt = "vGY13MMUH4khKGscQOOg"
    passhash = blake2b(digest_size=30)
    passhash.update((password + salt).encode())
    return passhash.hexdigest()


def create_map_database():
    # Connect to the database or create one if it doesn't exist
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Create a table for the map data with columns: x_pos, y_pos, data
    cursor.execute('''CREATE TABLE IF NOT EXISTS map_data (
                        x_pos INTEGER,
                        y_pos INTEGER,
                        data TEXT,
                        PRIMARY KEY (x_pos, y_pos)
                      )''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def save_map_data(map_data_dict, x_pos, y_pos, data):
    # Use a string coordinate key like 'x,y'
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data


class SQLiteConnectionPool:
    def __init__(self, db_name):
        self.db_name = db_name
        self.pool = []

    def get_connection(self):
        if self.pool:
            return self.pool.pop()
        else:
            return sqlite3.connect(self.db_name)

    def return_connection(self, conn):
        self.pool.append(conn)


def get_map_at_coords(x_pos, y_pos, map_data_dict):
    """returns map data at a specific coordinate"""
    key = f"{x_pos},{y_pos}"

    # Check if the key exists in the map_data_dict
    if key in map_data_dict:
        return {key: map_data_dict[key]}

    # Return None if no data was found for the given coordinates
    return None


def get_users_at_coords(x_pos, y_pos, user, users_dict, include_construction=True, include_self=True):
    """Returns a list of user data at a specific coordinate"""

    users_at_coords = []

    for username, user_data in users_dict.items():
        # Skip this user if it's the same as the specified user and include_self is False
        if username == user and not include_self:
            continue

        if user_data["x_pos"] == x_pos and user_data["y_pos"] == y_pos:
            if not include_construction:
                user_data = user_data.copy()  # So we don't modify the original data
                user_data.pop('construction', None)  # Remove the construction data if present
            users_at_coords.append({username: user_data})

    # Return the list of users at the given coordinates (may be empty if no users found)
    return users_at_coords




# Initialize a connection pool
conn_pool = SQLiteConnectionPool("db/map_data.db")


def create_users_db():
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

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def create_user(user_data_dict, user, x_pos=1, y_pos=1, profile_pic=""):
    # Prepare the data dictionary
    data = {
        "x_pos": x_pos,
        "y_pos": y_pos,
        "type": "player",
        "age": 0,
        "img": profile_pic,
        "exp": 0,
        "hp": 100,
        "armor": 0,
        "action_points": 200,
        "army_deployed": 0,
        "army_free": 0,
        "peasants": 0,
        "wood": 500,
        "food": 500,
        "bismuth": 500,
        "equipped": [{"type": "axe", "damage": 1, "durability": 100, "cls": "main_attack", "id": id_generator()}],
        "unequipped": [{"type": "dagger", "damage": 2, "durability": 100, "cls": "main_attack", "id": id_generator()}],
        "pop_lim": 0,
        "alive": True,
        "online": True,
    }

    # Insert or update user data in the passed dictionary
    user_data_dict[user] = data


def save_map_from_memory(map_data_dict):
    print("saving map to drive")
    # Connect to the database and get a cursor
    conn_map = sqlite3.connect("db/map_data.db")
    cursor_map = conn_map.cursor()

    # Iterate over the map data dictionary and save the data to the SQLite database
    for key, data in map_data_dict.items():
        x_map, y_map = map(int, key.split(','))
        data_str = json.dumps(data)

        # Check if the entry exists
        cursor_map.execute("SELECT 1 FROM map_data WHERE x_pos = ? AND y_pos = ?", (x_map, y_map))
        exists = cursor_map.fetchone()

        # Update the existing entry if it exists, else insert a new entry
        if exists:
            cursor_map.execute("UPDATE map_data SET data = ? WHERE x_pos = ? AND y_pos = ?", (data_str, x_map, y_map))
        else:
            cursor_map.execute("INSERT INTO map_data (x_pos, y_pos, data) VALUES (?, ?, ?)", (x_map, y_map, data_str))

    # Commit the changes and close the database connection
    conn_map.commit()
    conn_map.close()


def load_map_to_memory():
    # Connect to the database and get a cursor
    conn_map = sqlite3.connect("db/map_data.db")
    cursor_map = conn_map.cursor()

    # Execute a query to fetch all records from the map_data table
    cursor_map.execute("SELECT x_pos, y_pos, data FROM map_data")

    # Fetch all results
    results_map = cursor_map.fetchall()

    # Close the database connection
    conn_map.close()

    # Convert the results to a dictionary
    map_data_dict = {}
    for result_map in results_map:
        x_map, y_map, data_str = result_map
        data = json.loads(data_str)

        key = f"{x_map},{y_map}"
        map_data_dict[key] = data

    return map_data_dict


def save_users_from_memory(user_data_dict):
    print("saving users to drive")
    conn_user = sqlite3.connect("db/user_data.db")
    cursor_user = conn_user.cursor()

    for username, user_data in user_data_dict.items():
        x_pos = user_data["x_pos"]
        y_pos = user_data["y_pos"]

        data_copy = user_data.copy()
        del data_copy["x_pos"]
        del data_copy["y_pos"]

        data_str = json.dumps(data_copy)

        # Check if the user entry exists
        cursor_user.execute("SELECT 1 FROM user_data WHERE username = ?", (username,))
        exists = cursor_user.fetchone()

        # Update the existing user entry if it exists, else insert a new entry
        if exists:
            cursor_user.execute("UPDATE user_data SET x_pos = ?, y_pos = ?, data = ? WHERE username = ?",
                                (x_pos, y_pos, data_str, username))
        else:
            cursor_user.execute("INSERT INTO user_data (username, x_pos, y_pos, data) VALUES (?, ?, ?, ?)",
                                (username, x_pos, y_pos, data_str))

    # Commit the changes and close the database connection
    conn_user.commit()
    conn_user.close()


def load_users_to_memory():
    conn_user = sqlite3.connect("db/user_data.db")
    cursor_user = conn_user.cursor()

    cursor_user.execute("SELECT username, x_pos, y_pos, data FROM user_data")
    all_users_results = cursor_user.fetchall()
    conn_user.close()

    if not all_users_results:
        print("No users found")
        return {}

    user_data_dict = {}
    for result_user in all_users_results:
        username, x_pos, y_pos, data_str = result_user
        data = json.loads(data_str)

        user_data = {
            "x_pos": x_pos,
            "y_pos": y_pos,
            **data
        }

        user_data_dict[username] = user_data

    return user_data_dict


def id_generator(length=10):
    """Generate a random alphanumeric string of given length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
