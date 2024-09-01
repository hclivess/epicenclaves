import random
from typing import List, Dict, Any
from item_generator import generate_armor, generate_weapon, generate_tool
import threading

class User:
    def __init__(self, username: str, x_pos: int, y_pos: int, profile_pic: str = "", **kwargs):
        self.username = username
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.type = "player"
        self.age = 0
        self.img = profile_pic
        self.exp = 0
        self.units = []
        self.research = 0
        self.base_hp = 100  # Base HP value
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

        for key, value in kwargs.items():
            setattr(self, key, value)

    def calculate_total_hp(self):
        return self.base_hp + self.calculate_hp_bonus()

    def calculate_hp_bonus(self):
        # This is a simple linear increase. You might want to adjust this formula
        # to balance your game mechanics.
        return int(self.exp / 10)  # 1 extra HP for every 10 exp

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
            "hp": self.calculate_total_hp(),  # Use the method here
            "base_hp": self.base_hp,
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


def create_user(user_data_dict: Dict[str, Dict[str, Any]], user: str, mapdb: Dict[str, Any], profile_pic: str = "",
                league="game") -> None:
    print(f"Creating {user} in league {league}")

    x_pos, y_pos = find_open_space(mapdb[league])

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

    user_data_dict[league][user] = new_user.to_dict()



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