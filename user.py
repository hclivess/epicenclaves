import json
import sqlite3
import random
from typing import List, Dict, Any
from item_generator import id_generator, generate_armor, generate_weapon, generate_tool
import threading

user_lock = threading.Lock()

class User:
    def __init__(self, username: str, x_pos: int, y_pos: int, profile_pic: str = ""):
        self.username = username
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.type = "player"
        self.age = 0
        self.img = profile_pic
        self.exp = 0
        self.units = []
        self.research = 0
        self.hp = 100
        self.armor = 0
        self.action_points = 500
        self.army_deployed = 0
        self.army_free = 0
        self.peasants = 0
        self.wood = 500
        self.food = 500
        self.bismuth = 500
        self.equipped = []
        self.unequipped = []
        self.pop_lim = 0
        self.alive = True
        self.online = True
        self.construction = {}

    def get_actions(self, current_user: str) -> List[Dict[str, str]]:
        if self.username != current_user:
            return [{"name": "challenge", "action": f"/fight?target=player&name={self.username}"}]
        return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "x_pos": self.x_pos,
            "y_pos": self.y_pos,
            "type": self.type,
            "age": self.age,
            "img": self.img,
            "exp": self.exp,
            "units": self.units,
            "research": self.research,
            "hp": self.hp,
            "armor": self.armor,
            "action_points": self.action_points,
            "army_deployed": self.army_deployed,
            "army_free": self.army_free,
            "peasants": self.peasants,
            "wood": self.wood,
            "food": self.food,
            "bismuth": self.bismuth,
            "equipped": self.equipped,
            "unequipped": self.unequipped,
            "pop_lim": self.pop_lim,
            "alive": self.alive,
            "online": self.online,
            "construction": self.construction
        }

def create_users_db():
    with user_lock:
        conn = sqlite3.connect("db/user_data.db")
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS user_data (username TEXT PRIMARY KEY, x_pos INTEGER, y_pos INTEGER, data TEXT)")
        conn.commit()
        conn.close()

def find_open_space(mapdb: Dict[str, Any]) -> tuple:
    x = random.randint(0, 100)
    y = random.randint(0, 100)

    while True:
        open_space = True

        for dx in range(-1, 2):  # Check within a 3x3 square
            for dy in range(-1, 2):
                check_x, check_y = x + dx, y + dy
                if f"{check_x},{check_y}" in mapdb:
                    open_space = False
                    break
            if not open_space:
                break

        if open_space:
            return x, y

        # Increment coordinates
        y += 1
        if y > 2 ** 31:
            x += 1
            y = 1
            if x > 2 ** 31:
                raise Exception("No open space found within available range.")

def create_user(user_data_dict: Dict[str, Any], user: str, mapdb: Dict[str, Any], profile_pic: str = "") -> None:
    print(f"Creating {user}")
    x_pos, y_pos = find_open_space(mapdb)

    # Generate initial weak armor for each slot
    initial_armor = [generate_armor(max_level=1, slot=slot) for slot in ["head", "body", "arms", "legs", "feet"]]

    # Generate a hatchet as the starting weapon
    starting_hatchet = generate_tool(max_level=1, tool_type="hatchet")

    # Create a new User instance
    new_user = User(user, x_pos, y_pos, profile_pic)

    # Set initial equipment
    new_user.equipped = [starting_hatchet] + initial_armor
    new_user.unequipped = [generate_weapon(max_level=1)]

    # Calculate total initial armor value
    new_user.armor = sum(armor["protection"] for armor in initial_armor)

    # Insert or update user data in the passed dictionary
    user_data_dict[user] = new_user.to_dict()
    print("User created")

def save_users_from_memory(user_data_dict: Dict[str, Any]) -> None:
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

def load_users_to_memory() -> Dict[str, Any]:
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

def get_users_at_coords(x_pos: int, y_pos: int, user: str, users_dict: Dict[str, Any], include_construction: bool = True, include_self: bool = True) -> List[Dict[str, Any]]:
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