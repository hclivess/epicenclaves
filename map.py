import inspect
import random
from typing import List, Dict, Any, Optional, Tuple
from math import floor

from backend import get_user
from spawner import spawn_all_entities
from player import User
from buildings import Building
from scenery import scenery_types
from enemies import enemy_types

# Constants for chunking
CHUNK_SIZE = 16

# Get all subclasses of Enemy and Scenery
# Combine scenery_types and enemy_types
entity_types = {**scenery_types, **enemy_types}

# If you need the types in lowercase, you can create a new dictionary:
entity_types_lower = {k.lower(): v for k, v in entity_types.items()}

# Get all subclasses of Building
building_types = {cls.__name__.lower(): cls for cls in Building.__subclasses__()}

def get_chunk_key(x: int, y: int) -> Tuple[int, int]:
    return (floor(x / CHUNK_SIZE), floor(y / CHUNK_SIZE))

def get_tile_map(x: int, y: int, mapdb: Dict[str, Any]) -> List[Dict[str, Any]]:
    key = f"{x},{y}"
    if key in mapdb:
        return [{key: mapdb[key]}]
    return []

def get_tile_users(x: int, y: int, user: str, usersdb: Dict[str, Any]) -> List[Dict[str, Any]]:
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

def get_tile_actions(tile: Any, user: str) -> List[Dict[str, str]]:
    if isinstance(tile, dict):
        # Check if the tile is a user entry (it will have a single key-value pair)
        if len(tile) == 1:
            username, user_data = next(iter(tile.items()))
            return User(**user_data).get_actions(user)

        tile_type = tile.get('type', '').lower()
        if tile_type in entity_types:
            cls = entity_types[tile_type]
            valid_params = get_constructor_params(cls)
            filtered_tile = {k: v for k, v in tile.items() if k in valid_params}
            return cls(**filtered_tile).get_actions(user)
        elif tile_type in building_types:
            cls = building_types[tile_type]
            valid_params = get_constructor_params(cls)
            filtered_tile = {k: v for k, v in tile.items() if k in valid_params}
            if 'building_id' not in filtered_tile:
                filtered_tile['building_id'] = tile.get('id', 1)
            return cls(**filtered_tile).get_actions(user)
    elif isinstance(tile, (Building, Enemy, Scenery, User)):
        return tile.get_actions(user)
    return []

def get_constructor_params(cls):
    return set(inspect.signature(cls.__init__).parameters.keys()) - {'self'}

def get_user_data(user: str, usersdb: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = get_user(user, usersdb)
    if data is None:
        return None
    username = list(data.keys())[0]
    user_data = data[username]
    return user_data

def occupied_by(x: int, y: int, what: str, mapdb: Dict[str, Any], method="type") -> bool:
    entity_map = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)

    if entity_map:
        entity = entity_map.get(f"{x},{y}")

        if entity and entity.get(method) == what:
            return True

    return False

def owned_by(x: int, y: int, control: str, mapdb: Dict[str, Any]) -> bool:
    entity_map = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)

    if entity_map:
        entity = entity_map.get(f"{x},{y}")

        if entity and entity.get("control") == control:
            return True

    return False

def update_map_data(update_data: Dict[str, Any], map_data_dict: Dict[str, Any]) -> None:
    coords = list(update_data.keys())[0]
    tile_data = update_data[coords]

    if coords in map_data_dict:
        map_data_dict[coords].update(tile_data)
    else:
        raise KeyError(f"No data found at the given coordinates {coords}.")

def remove_from_map(coords: str, entity_type: str, map_data_dict: Dict[str, Any]) -> None:
    print("remove_from_map", coords, entity_type)

    if coords in map_data_dict:
        if map_data_dict[coords].get("type") == entity_type:
            del map_data_dict[coords]
            print(f"Entity of type {entity_type} at coordinates {coords} has been removed.")
        else:
            print(f"Entity of type {entity_type} not found at the given coordinates {coords}.")
    else:
        print(f"No data found at the given coordinates {coords}.")

def insert_map_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
    print("insert_map_data", new_data)

    for coord, construction_info in new_data.items():
        if coord in existing_data:
            existing_data[coord].update(construction_info)
        else:
            existing_data[coord] = construction_info

def is_visible(x1: int, y1: int, x2: int, y2: int, distance: int) -> bool:
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 <= distance ** 2

def get_map_data_limit(x_pos: int, y_pos: int, map_data_dict: Dict[str, Any], distance: int = 5) -> Dict[str, Any]:
    filtered_data = {}
    distance_squared = distance ** 2
    x_min, x_max = x_pos - distance, x_pos + distance
    y_min, y_max = y_pos - distance, y_pos + distance

    for coords, data in map_data_dict.copy().items():
        x_map, y_map = map(int, coords.split(","))
        if x_min <= x_map <= x_max and y_min <= y_map <= y_max:
            if (x_map - x_pos) ** 2 + (y_map - y_pos) ** 2 <= distance_squared:
                filtered_data[coords] = data

    return filtered_data

def get_users_data_limit(x_pos: int, y_pos: int, usersdb: Dict[str, Any], distance: int = 5) -> Dict[str, Any]:
    filtered_data = {}
    distance_squared = distance ** 2
    x_min, x_max = x_pos - distance, x_pos + distance
    y_min, y_max = y_pos - distance, y_pos + distance

    for username, data in usersdb.items():
        x_map, y_map = data['x_pos'], data['y_pos']
        if x_min <= x_map <= x_max and y_min <= y_map <= y_max:
            if (x_map - x_pos) ** 2 + (y_map - y_pos) ** 2 <= distance_squared:
                filtered_data[username] = data
    return filtered_data

def get_buildings(user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    if user_data is None:
        return []

    construction = user_data.get("construction")

    if construction is None:
        return []

    return list(construction.values())

def is_surrounded_by(x: int, y: int, entity_type: str, mapdb: Dict[str, Any], diameter: int = 1) -> bool:
    for i in range(x - diameter, x + diameter + 1):
        for j in range(y - diameter, y + diameter + 1):
            if i == x and j == y:
                continue
            if f"{i},{j}" in mapdb and mapdb[f"{i},{j}"]['type'] == entity_type:
                return True
    return False

def get_surrounding_map_and_user_data(user: str, user_data_dict: Dict[str, Any], map_data_dict: Dict[str, Any],
                                      distance: int) -> Dict[str, Any]:
    user_data = user_data_dict.get(user)
    if not user_data:
        return {"error": "User not found."}

    user_x_pos = user_data["x_pos"]
    user_y_pos = user_data["y_pos"]

    return {
        "users": get_users_data_limit(user_x_pos, user_y_pos, user_data_dict, distance=distance),
        "construction": get_map_data_limit(user_x_pos, user_y_pos, map_data_dict=map_data_dict, distance=distance),
    }

def get_coords(entry: Dict[str, Any]) -> str:
    return list(entry.keys())[0]

def save_map_data(map_data_dict: Dict[str, Any], x_pos: int, y_pos: int, data: Dict[str, Any]) -> None:
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data

def get_map_at_coords(x_pos: int, y_pos: int, map_data_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    key = f"{x_pos},{y_pos}"
    if key in map_data_dict:
        return {key: map_data_dict[key]}
    return None

def strip_usersdb(usersdb: Dict[str, Any]) -> Dict[str, Any]:
    # strip usersdb of non-displayed data
    keys_to_keep = ['x_pos', 'y_pos', 'exp', 'hp', 'armor', 'img', 'online', 'type']
    new_usersdb = {}
    for username, user_data in usersdb.items():
        new_usersdb[username] = {k: v for k, v in user_data.items() if k in keys_to_keep}
    return new_usersdb

def spawn_entities(mapdb, league):
    spawn_all_entities(mapdb[league])

def count_buildings(user_data):
    counts = {'sawmill': 0, 'forest': 0, 'barracks': 0, 'farm': 0, 'house': 0, 'mine': 0, 'mountain': 0,
              'laboratory': 0}

    for building_data in user_data.get("construction", {}).values():
        building_type = building_data['type']
        if building_type in counts:
            counts[building_type] += building_data.get('level', 1)

    return counts


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
