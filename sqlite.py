import json
import os
import sqlite3
from hashlib import blake2b
from contextlib import closing

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


def get_map_data(x_pos, y_pos, map_data_dict):
    key = f"{x_pos},{y_pos}"

    # Check if the key exists in the map_data_dict
    if key in map_data_dict:
        return {key: map_data_dict[key]}

    # Return None if no data was found for the given coordinates
    return None


# Initialize a connection pool
conn_pool = SQLiteConnectionPool("db/map_data.db")


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


def create_user_db():
    # Connect to the database
    conn = sqlite3.connect("db/user_data.db")
    cursor = conn.cursor()

    # Create the table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_data (
                        username TEXT PRIMARY KEY,
                        x_pos INTEGER,
                        y_pos INTEGER,
                        data TEXT,
                        construction TEXT
                      )''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def create_user(user_data_dict, user, x_pos=1, y_pos=1):
    # Prepare the data dictionary
    data = {
        "x_pos": x_pos,
        "y_pos": y_pos,
        "type": "player",
        "age": 0,
        "img": "img/pp.png",
        "exp": 0,
        "hp": 100,
        "armor": 0,
        "action_points": 200,
        "wood": 500,
        "food": 500,
        "bismuth": 500,
        "items": [{"type": "axe", "damage": 1, "durability": 100}],
        "pop_lim": 0,
        "alive": True,
        "online": True
    }

    # Insert or update user data in the passed dictionary
    user_data_dict[user] = data


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


def auth_login_validate(user, password):
    users_db_cursor.execute("SELECT * FROM users WHERE username = ? AND passhash = ?", (user, hash_password(password)))
    result = users_db_cursor.fetchall()

    return bool(result)


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


def auth_add_user(user, password):
    users_db.execute("INSERT OR IGNORE INTO users VALUES (?,?)", (user, hash_password(password)))
    users_db.commit()


def auth_exists_user(user):
    users_db_cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
    result = users_db_cursor.fetchall()

    return bool(result)


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


def get_map_data_limit(x_pos, y_pos, map_data_dict, distance=500):
    for coords, data_str in map_data_dict.items():
        x_map, y_map = map(int, coords.split(","))
        if (x_map - x_pos) ** 2 + (y_map - y_pos) ** 2 <= distance ** 2:
            map_data_dict[coords] = data_str
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


def auth_check_users_db():
    users_db.execute("CREATE TABLE IF NOT EXISTS users (username STRING PRIMARY KEY, passhash STRING)")
    users_db.commit()
