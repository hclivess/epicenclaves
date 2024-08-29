import json
import os
import sqlite3
from hashlib import blake2b
from typing import Dict, Any

from map import sql_lock
from user import user_lock

if not os.path.exists("db"):
    os.mkdir("db")
users_db = sqlite3.connect("db/auth.db")
users_db_cursor = users_db.cursor()

def hash_password(password):
    salt = "vGY13MMUH4khKGscQOOg"
    passhash = blake2b(digest_size=30)
    passhash.update((password + salt).encode())
    return passhash.hexdigest()


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


# Initialize a connection pool
conn_pool = SQLiteConnectionPool("db/map_data.db")


def init_databases(league="game"):
    map_exists = os.path.exists("db/map_data.db")
    user_exists = os.path.exists("db/user_data.db")

    if not map_exists:
        create_map_database(league)
    if not user_exists:
        create_users_db(league)

    return {"map_exists": map_exists}


def load_users_to_memory(league="game") -> Dict[str, Any]:
    conn_user = sqlite3.connect("db/user_data.db")
    cursor_user = conn_user.cursor()

    cursor_user.execute(f"SELECT username, x_pos, y_pos, data FROM {league}_user_data")
    all_users_results = cursor_user.fetchall()
    conn_user.close()

    if not all_users_results:
        print(f"No users found in league {league}")
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


def save_users_from_memory(user_data_dict: Dict[str, Any], league="game") -> None:
    print(f"saving users to drive for league {league}")
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
        cursor_user.execute(f"SELECT 1 FROM {league}_user_data WHERE username = ?", (username,))
        exists = cursor_user.fetchone()

        # Update the existing user entry if it exists, else insert a new entry
        if exists:
            cursor_user.execute(f"UPDATE {league}_user_data SET x_pos = ?, y_pos = ?, data = ? WHERE username = ?",
                                (x_pos, y_pos, data_str, username))
        else:
            cursor_user.execute(f"INSERT INTO {league}_user_data (username, x_pos, y_pos, data) VALUES (?, ?, ?, ?)",
                                (username, x_pos, y_pos, data_str))

    # Commit the changes and close the database connection
    conn_user.commit()
    conn_user.close()


def create_users_db(league="game"):
    with user_lock:
        conn = sqlite3.connect("db/user_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {league}_user_data (username TEXT PRIMARY KEY, x_pos INTEGER, y_pos INTEGER, data TEXT)")
        conn.commit()
        conn.close()


def create_map_database(league="game") -> None:
    # Connect to the database or create one if it doesn't exist
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Create a table for the map data with columns: x_pos, y_pos, data
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS {league} (
                        x_pos INTEGER,
                        y_pos INTEGER,
                        data TEXT,
                        PRIMARY KEY (x_pos, y_pos)
                      )''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def save_map_from_memory(map_data_dict: Dict[str, Any], league="game") -> None:
    with sql_lock:
        print(f"saving map to drive for league {league}")
        conn_map = sqlite3.connect("db/map_data.db")
        cursor_map = conn_map.cursor()

        for key, data in map_data_dict.items():
            x_map, y_map = map(int, key.split(','))
            data_str = json.dumps(data)

            cursor_map.execute(f"SELECT 1 FROM {league} WHERE x_pos = ? AND y_pos = ?", (x_map, y_map))
            exists = cursor_map.fetchone()

            if exists:
                cursor_map.execute(f"UPDATE {league} SET data = ? WHERE x_pos = ? AND y_pos = ?", (data_str, x_map, y_map))
            else:
                cursor_map.execute(f"INSERT INTO {league} (x_pos, y_pos, data) VALUES (?, ?, ?)", (x_map, y_map, data_str))

        conn_map.commit()
        conn_map.close()


def load_map_to_memory(league="game") -> Dict[str, Any]:
    # Connect to the database and get a cursor
    conn_map = sqlite3.connect("db/map_data.db")
    cursor_map = conn_map.cursor()

    # Execute a query to fetch all records from the map_data table
    cursor_map.execute(f"SELECT x_pos, y_pos, data FROM {league}")

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