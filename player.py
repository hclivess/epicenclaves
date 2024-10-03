import random
from typing import List, Dict, Any, Tuple, Optional
from item_generator import generate_armor, generate_weapon, generate_tool


class User:
    HP_BONUS_PER_EXP = 350
    MANA_BONUS_PER_EXP = 500

    def __init__(self, username: str, x_pos: int, y_pos: int, profile_pic: str = "", **kwargs):
        self.username = username
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.type = "player"
        self.age = 0
        self.img = profile_pic
        self.exp = 0
        self.score = 0
        self.units = []
        self.spells = []
        self.spell_queue = []
        self.skills = []
        self.deaths = 0
        self.homicides = 0
        self.sorcery = 0
        self.physique = 0
        self.research = 0
        self.base_hp = 100  # Base HP value
        self.base_mana = 100  # Base mana value
        self.armor = 0
        self.action_points = 500
        self.army_deployed = 0
        self.army_free = 0
        self.peasants = 0
        self.ingredients = {
            "wood": 500,
            "food": 500,
            "bismuth": 500
        }
        self.equipped = []
        self.unequipped = []
        self.alive = True
        self.online = True
        self.construction = {}

        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_hp_bonus(self):
        return int(self.exp / self.HP_BONUS_PER_EXP)

    def get_mana_bonus(self):
        return int(self.exp / self.MANA_BONUS_PER_EXP)

    def get_total_hp(self):
        return self.base_hp + self.get_hp_bonus()

    def get_total_mana(self):
        return self.base_mana + self.get_mana_bonus()

    def get_actions(self, current_user: str) -> List[Dict[str, str]]:
        if self.username != current_user:
            if not self.alive:
                return [
                    {"name": "drag up", "action": f"/drag?target={self.username}&direction=up"},
                    {"name": "drag down", "action": f"/drag?target={self.username}&direction=down"},
                    {"name": "drag left", "action": f"/drag?target={self.username}&direction=left"},
                    {"name": "drag right", "action": f"/drag?target={self.username}&direction=right"}
                ]
            else:
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
            "score": self.score,
            "units": self.units,
            "skills": self.skills,
            "spells": self.spells,
            "spell_queue": self.spell_queue,
            "research": self.research,
            "hp": self.get_total_hp(),
            "mana": self.get_total_mana(),
            "base_hp": self.base_hp,
            "armor": self.armor,
            "action_points": self.action_points,
            "army_deployed": self.army_deployed,
            "army_free": self.army_free,
            "peasants": self.peasants,
            "ingredients": self.ingredients,
            "equipped": self.equipped,
            "unequipped": self.unequipped,
            "alive": self.alive,
            "online": self.online,
            "construction": self.construction
        }


def create_user(user_data_dict: Dict[str, Dict[str, Any]], user: str, mapdb: Dict[str, Any], profile_pic: str = "",
                league="game") -> None:
    print(f"Creating {user} in league {league}")

    x_pos, y_pos = find_open_space(mapdb[league])

    # Generate initial weak armor for each slot
    initial_armor = [generate_armor(max_level=1, slot=slot) for slot in ["head", "body", "arms", "legs", "feet"]]

    # Generate a hatchet as the starting weapon
    starting_hatchet = generate_tool(max_level=1, tool_type="hatchet")
    starting_pickaxe = generate_tool(max_level=1, tool_type="pickaxe")

    # Create a new User instance
    new_user = User(user, x_pos, y_pos, profile_pic)

    # Set initial equipment
    new_user.equipped = [starting_hatchet] + initial_armor
    new_user.unequipped = [starting_pickaxe, generate_weapon(max_level=1)]

    # Calculate total initial armor value
    new_user.armor = sum(armor["protection"] for armor in initial_armor)

    user_data_dict[league][user] = new_user.to_dict()


def calculate_total_hp(base_hp: int, exp: int) -> int:
    return base_hp + int(exp / User.HP_BONUS_PER_EXP)

def calculate_total_mana(base_mana: int, exp: int) -> int:
    return base_mana + int(exp / User.MANA_BONUS_PER_EXP)

def calculate_population_limit(user_data):
    base_limit = 0
    house_bonus = 0
    barracks_bonus = 0

    if 'construction' in user_data:
        for building in user_data['construction'].values():
            if building.get('type') == 'house':
                # Base population increase for a house
                house_bonus += 10
                # Additional population for each level above 1
                level = building.get('level', 1)
                house_bonus += 10 * (level - 1)
            elif building.get('type') == 'barracks':
                # Assuming barracks provide 5 housing per level
                level = building.get('level', 1)
                barracks_bonus += 5 * level

    return base_limit + house_bonus + barracks_bonus


def has_item_equipped(player: Dict, item_type: str) -> bool:
    return any(item.get("type") == item_type for item in player.get("equipped", []))


def drop_random_item(player: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    inventory = player.get("unequipped", [])
    equipped_items = [item for item in player.get("equipped", []) if item["type"] != "empty"]

    all_items = inventory + equipped_items
    if not all_items:
        return None, None

    dropped_item = random.choice(all_items)
    if dropped_item in inventory:
        player["unequipped"].remove(dropped_item)
        return dropped_item, "unequipped"
    else:
        player["equipped"] = [item for item in player["equipped"] if item != dropped_item]
        return dropped_item, dropped_item["slot"]


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
