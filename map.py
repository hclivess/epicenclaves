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


def get_map_data_limit(x_pos, y_pos, map_data_dict, distance=500):
    for coords, data_str in map_data_dict.items():
        x_map, y_map = map(int, coords.split(","))
        if (x_map - x_pos) ** 2 + (y_map - y_pos) ** 2 <= distance**2:
            map_data_dict[coords] = data_str
    return map_data_dict


def get_buildings(user_data):
    if user_data is None:
        return []

    construction = user_data.get("construction")

    if construction is None:
        return []

    return list(construction.values())


def get_surrounding_map_and_user_data(user, user_data_dict, map_data_dict):
    # Check if the specified user is in the user_data_dict
    if user not in user_data_dict:
        return {"error": "User not found."}

    # Fetch the map data for the specified user and transform it into a dictionary indexed by "x:y"
    user_map_data_dict = get_map_data_limit(
        user_data_dict[user]["x_pos"],
        user_data_dict[user]["y_pos"],
        map_data_dict=map_data_dict,
    )

    # Prepare the final result as a dictionary with two keys
    result = {
        "users": user_data_dict,  # Include all users' data
        "construction": user_map_data_dict,  # This is now a dictionary indexed by "x:y"
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


def save_map_from_memory(map_data_dict):
    sql_lock = threading.Lock
    with sql_lock:
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
