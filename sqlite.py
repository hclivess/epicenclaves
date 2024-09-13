import json
import os
import sqlite3
from hashlib import blake2b
from typing import Dict, Any
from map import get_chunk_key

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


def check_table_exists(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    table_exists = cursor.fetchone() is not None
    conn.close()
    return table_exists


def init_databases(league="game"):
    map_db_path = "db/map_data.db"
    user_db_path = "db/user_data.db"

    map_exists = os.path.exists(map_db_path) and check_table_exists(map_db_path, league)
    user_exists = os.path.exists(user_db_path) and check_table_exists(user_db_path, league)

    if not map_exists:
        create_map_database(league)
    if not user_exists:
        create_users_db(league)

    return {"map_exists": map_exists, "user_exists": user_exists}


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


def save_users_from_memory(user_data_dict: Dict[str, Dict[str, Any]], league="game") -> None:
    print(f"Saving users to drive for league {league}")
    conn_user = None
    try:
        conn_user = sqlite3.connect("db/user_data.db")
        cursor_user = conn_user.cursor()

        for username, user_data in user_data_dict[league].copy().items():
            print(f"Processing user: {username}")
            #print(f"User data: {user_data}")

            x_pos = user_data.get("x_pos")
            y_pos = user_data.get("y_pos")

            if x_pos is None or y_pos is None:
                print(f"Warning: Missing x_pos or y_pos for user {username}. Using default values.")
                x_pos = x_pos if x_pos is not None else 0
                y_pos = y_pos if y_pos is not None else 0

            data_copy = user_data.copy()
            data_copy.pop("x_pos", None)
            data_copy.pop("y_pos", None)

            data_str = json.dumps(data_copy)

            cursor_user.execute(f"""
                INSERT OR REPLACE INTO {league}_user_data (username, x_pos, y_pos, data)
                VALUES (?, ?, ?, ?)
            """, (username, x_pos, y_pos, data_str))

        conn_user.commit()
        print(f"Saved data for {len(user_data_dict[league])} users")

    except sqlite3.Error as e:
        print(f"SQLite error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        if conn_user:
            conn_user.close()


def create_users_db(league="game"):
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
    print(f"saving map to drive for league {league}")
    conn_map = sqlite3.connect("db/map_data.db")
    cursor_map = conn_map.cursor()

    # First, remove all existing gnomes from the database
    cursor_map.execute(f"DELETE FROM {league} WHERE json_extract(data, '$.type') = 'gnomes'")

    for key, data in map_data_dict[league].copy().items():
        x_map, y_map = map(int, key.split(','))
        data_str = json.dumps(data)

        cursor_map.execute(f"INSERT OR REPLACE INTO {league} (x_pos, y_pos, data) VALUES (?, ?, ?)", (x_map, y_map, data_str))

    conn_map.commit()
    conn_map.close()

    print(f"Map saved for league {league}. Total entities: {len(map_data_dict[league])}")
    print(f"Gnome count after save: {sum(1 for tile in map_data_dict[league].values() if tile['type'] == 'gnomes')}")


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