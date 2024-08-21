import json
import sqlite3
import threading

from backend import get_user, map_lock
from user import get_users_at_coords


def get_tile_map(x, y, mapdb):
    map_entities = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)
    if not isinstance(map_entities, list):
        map_entities = [map_entities] if map_entities else []
    return map_entities


def get_tile_users(x, y, user, usersdb):
    user_entities = get_users_at_coords(
        x_pos=x,
        y_pos=y,
        user=user,
        users_dict=usersdb,
        include_construction=False,
        include_self=False,
    )
    if not isinstance(user_entities, list):
        user_entities = [user_entities] if user_entities else []
    return user_entities


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


def owned_by(x, y, control, mapdb):
    entity_map = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)

    if entity_map:
        entity = entity_map.get(f"{x},{y}")

        if entity and entity.get("control") == control:
            return True

    return False


def update_map_data(update_data, map_data_dict):
    with map_lock:
        coords = list(update_data.keys())[0]
        tile_data = update_data[coords]
        if coords in map_data_dict:
            for key, value in tile_data.items():
                map_data_dict[coords][key] = value
        else:
            raise KeyError(f"No data found at the given coordinates {coords}.")


def remove_from_map(coords, entity_type, map_data_dict):
    with map_lock:
        print("remove_from_map", coords, entity_type)

        # Create a key using the coordinates
        key = coords

        # Check if the key exists in the map_data_dict
        if key in map_data_dict:
            # Check if the type matches
            if map_data_dict[key].get("type") == entity_type:
                # Remove the key from the map_data_dict
                del map_data_dict[key]
                print(
                    f"Entity of type {entity_type} at coordinates {coords} has been removed."
                )
            else:
                print(
                    f"Entity of type {entity_type} not found at the given coordinates {coords}."
                )
        else:
            print(f"No data found at the given coordinates {coords}.")


def insert_map_data(existing_data, new_data):
    with map_lock:
        print("insert_map_data", new_data)

        for coord, construction_info in new_data.items():
            if coord in existing_data:
                # If the coordinate already exists, update its values
                existing_data[coord].update(construction_info)
            else:
                # If the coordinate doesn't exist, create a new entry
                existing_data[coord] = construction_info


def is_visible(x1, y1, x2, y2, distance):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 <= distance ** 2

def get_map_data_limit(x_pos, y_pos, map_data_dict, distance=5):
    filtered_data = {}
    for coords, data in map_data_dict.items():
        x_map, y_map = map(int, coords.split(","))
        if is_visible(x_pos, y_pos, x_map, y_map, distance):
            filtered_data[coords] = data
    return filtered_data

def get_users_data_limit(x_pos, y_pos, usersdb, distance=5):
    filtered_data = {}
    for username, data in usersdb.items():
        x_map = data['x_pos']
        y_map = data['y_pos']
        if is_visible(x_pos, y_pos, x_map, y_map, distance):
            filtered_data[username] = data
    return filtered_data

def get_buildings(user_data):
    if user_data is None:
        return []

    construction = user_data.get("construction")

    if construction is None:
        return []

    return list(construction.values())

def is_surrounded_by(x, y, entity_type, mapdb, diameter=1):
    for i in range(x - diameter, x + diameter + 1):
        for j in range(y - diameter, y + diameter + 1):
            if i == x and j == y:
                continue
            if f"{i},{j}" in mapdb and mapdb[f"{i},{j}"]['type'] == entity_type:
                return True
    return False

def get_surrounding_map_and_user_data(user, user_data_dict, map_data_dict, distance):
    if user not in user_data_dict:
        return {"error": "User not found."}

    user_x_pos = user_data_dict[user]["x_pos"]
    user_y_pos = user_data_dict[user]["y_pos"]

    user_map_data_dict = get_map_data_limit(
        user_x_pos,
        user_y_pos,
        map_data_dict=map_data_dict,
        distance=distance
    )

    result = {
        "users": get_users_data_limit(user_x_pos, user_y_pos, user_data_dict, distance=distance),
        "construction": user_map_data_dict,
    }

    return result


def get_coords(entry):
    return list(entry.keys())[0]


def save_map_data(map_data_dict, x_pos, y_pos, data):
    # Use a string coordinate key like 'x,y'
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data

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


def get_map_at_coords(x_pos, y_pos, map_data_dict):
    """returns map data at a specific coordinate"""
    key = f"{x_pos},{y_pos}"

    # Check if the key exists in the map_data_dict
    if key in map_data_dict:
        return {key: map_data_dict[key]}

    # Return None if no data was found for the given coordinates
    return None

sql_lock = threading.Lock()

def save_map_from_memory(map_data_dict):
    with sql_lock:
        print("saving map to drive")
        conn_map = sqlite3.connect("db/map_data.db")
        cursor_map = conn_map.cursor()

        for key, data in map_data_dict.items():
            x_map, y_map = map(int, key.split(','))
            data_str = json.dumps(data)

            cursor_map.execute("SELECT 1 FROM map_data WHERE x_pos = ? AND y_pos = ?", (x_map, y_map))
            exists = cursor_map.fetchone()

            if exists:
                cursor_map.execute("UPDATE map_data SET data = ? WHERE x_pos = ? AND y_pos = ?", (data_str, x_map, y_map))
            else:
                cursor_map.execute("INSERT INTO map_data (x_pos, y_pos, data) VALUES (?, ?, ?)", (x_map, y_map, data_str))

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


def strip_usersdb(usersdb):
    # strip usersdb of non-displayed data
    keys_to_keep = ['x_pos', 'y_pos', 'exp', 'hp', 'armor', 'img', 'online', 'type']
    new_usersdb = {}
    for username, user_data in usersdb.items():
        new_usersdb[username] = {k: v for k, v in user_data.items() if k in keys_to_keep}
    return new_usersdb
    # strip usersdb of non-displayed data
