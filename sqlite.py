import json
import sqlite3
from hashlib import blake2b
from contextlib import closing

users_db = sqlite3.connect("db/auth.db")
users_db_cursor = users_db.cursor()


def hash_password(password):
    salt = "vGY13MMUH4khKGscQOOg"
    passhash = blake2b(digest_size=30)
    passhash.update((password + salt).encode())
    return passhash.hexdigest()


def create_map_table():
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


def save_map_data(x_pos, y_pos, data):
    # Connect to the database
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Convert the data dictionary to a string for storage
    data_str = json.dumps(data)

    # Insert or replace data for the given position
    cursor.execute("INSERT OR REPLACE INTO map_data (x_pos, y_pos, data) VALUES (?, ?, ?)",
                   (x_pos, y_pos, data_str))

    # Commit changes and close the connection
    conn.commit()
    conn.close()


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


# Use prepared statements for SQL queries
def get_map_data(x_pos, y_pos):
    with closing(conn_pool.get_connection()) as conn:
        with closing(conn.cursor()) as cursor:
            cursor.execute("SELECT x_pos, y_pos, data FROM map_data WHERE x_pos = ? AND y_pos = ?", (x_pos, y_pos))
            result = cursor.fetchone()

    if result:
        x_pos, y_pos, data_str = result
        # Convert the data string back to a dictionary
        data = json.loads(data_str)
        return {"x_pos": x_pos, "y_pos": y_pos, **data}  # Unpacks the data dictionary

    # Return None if no entity was found
    return None


# Initialize a connection pool
conn_pool = SQLiteConnectionPool("db/map_data.db")


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


def update_map_data(update_data):
    # Extract x, y and new data from the update_data dict
    x = update_data.get('x_pos')
    y = update_data.get('y_pos')
    new_data = update_data.get('data')

    # Connect to the database
    conn = sqlite3.connect("db/map_data.db")
    cursor = conn.cursor()

    # Fetch the existing data
    cursor.execute("SELECT data FROM map_data WHERE x_pos=? AND y_pos=?", (x, y))
    row = cursor.fetchone()

    if row is not None:
        # Parse the JSON string into a Python dictionary
        data = json.loads(row[0])

        # Merge new data with the old data, new data takes precedence
        data.update(new_data)

        # Convert the updated data back into a JSON string
        data_str = json.dumps(data)

        # Update the row in the map_data table
        cursor.execute(
            "UPDATE map_data SET data = ? WHERE x_pos = ? AND y_pos = ?",
            (data_str, x, y)
        )

        # Commit the changes
        conn.commit()
    else:
        print("No data found at the given coordinates.")


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


def create_user(user):
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
        "action_points": 500000,
        "wood": 500,
        "food": 500,
        "bismuth": 500,
        "items": [{"type": "axe"}],
        "construction": [],
        "pop_lim": 0
    }
    data_str = json.dumps(data)

    # Insert the user data into the database
    cursor.execute('''INSERT OR IGNORE INTO user_data (username, x_pos, y_pos, data, construction)
                       VALUES (?, ?, ?, ?, ?)''',
                   (user, x_pos, y_pos, data_str, json.dumps([])))

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def load_user(user):
    conn = sqlite3.connect("db/user_data.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, x_pos, y_pos, data FROM user_data WHERE username=?", (user,))
    result = cursor.fetchone()

    conn.close()

    if result:
        username, x_pos, y_pos, data_str = result
        data = json.loads(data_str)

        user_data = {
            username: {
                "x_pos": x_pos,
                "y_pos": y_pos,
                **data
            }
        }

        return user_data
    else:
        return None


def login_validate(user, password):
    users_db_cursor.execute("SELECT * FROM users WHERE username = ? AND passhash = ?", (user, hash_password(password)))
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


def remove_construction(user, construction_coordinates):
    # Connect to the database

    # TODO CHANGE IN MAP INDEX TOO
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

    # Check if 'construction' key is in the data and is a list
    if "construction" in data and isinstance(data["construction"], list):
        # Iterate over the list and remove the construction with the given coordinates
        data["construction"] = [construction for construction in data["construction"]
                                if not (
                    construction['x_pos'] == construction_coordinates['x_pos'] and construction['y_pos'] ==
                    construction_coordinates['y_pos'])]

    # Convert the updated data back to a JSON string
    updated_data_str = json.dumps(data)

    # Update the user data in the database
    cursor.execute("UPDATE user_data SET data=? WHERE username=?", (updated_data_str, user))

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


def load_map_data(x_pos, y_pos):
    conn_map = sqlite3.connect("db/map_data.db")
    cursor_map = conn_map.cursor()

    distance_squared = 500 ** 2

    cursor_map.execute("""
        SELECT x_pos, y_pos, data 
        FROM map_data 
        WHERE ((x_pos - ?)*(x_pos - ?) + (y_pos - ?)*(y_pos - ?)) <= ?
    """, (x_pos, x_pos, y_pos, y_pos, distance_squared))

    results_map = cursor_map.fetchall()
    conn_map.close()

    map_data = []
    for result_map in results_map:
        x_map, y_map, data_str = result_map
        data = json.loads(data_str)

        map_info = {
            "x_pos": x_map,
            "y_pos": y_map,
            **data
        }

        map_data.append(map_info)

    return map_data


def load_all_user_data():
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



def load_all_map_data():
    user_data_dict = load_all_user_data()

    total_data = []
    for username, user_data in user_data_dict.items():
        user_construction = {"construction": load_map_data(user_data['x_pos'], user_data['y_pos'])}
        total_data.append({username: user_data})
        total_data.append(user_construction)

    return total_data

def check_users_db():
    users_db.execute("CREATE TABLE IF NOT EXISTS users (username STRING PRIMARY KEY, passhash STRING)")
    users_db.commit()
