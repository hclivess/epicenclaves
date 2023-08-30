import json
import sqlite3

from weapon_generator import id_generator


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
        "research": 0,
        "hp": 100,
        "armor": 0,
        "action_points": 200,
        "army_deployed": 0,
        "army_free": 0,
        "peasants": 0,
        "wood": 500,
        "food": 500,
        "bismuth": 500,
        "equipped": [{"type": "axe", "min_damage": 1, "max_damage": 1, "durability": 100, "range": "melee", "role": "right_hand", "id": id_generator()}],
        "unequipped": [{"type": "dagger", "min_damage": 1, "max_damage": 2, "durability": 100, "range": "melee", "role": "right_hand", "id": id_generator()}],
        "pop_lim": 0,
        "alive": True,
        "online": True,
    }

    # Insert or update user data in the passed dictionary
    user_data_dict[user] = data


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
