import threading
import inspect

from backend import get_user, map_lock
from player import get_users_at_coords

from typing import List, Dict, Any, Optional
from player import User
from entities import Enemy, Scenery
from buildings import Building


# Get all subclasses of Enemy and Scenery
entity_types = {cls.__name__.lower(): cls for cls in Enemy.__subclasses__() + Scenery.__subclasses__()}

# Get all subclasses of Building
building_types = {cls.__name__.lower(): cls for cls in Building.__subclasses__()}

def get_tile_map(x: int, y: int, mapdb: Dict[str, Any]) -> List[Dict[str, Any]]:
    map_entities = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)
    if not isinstance(map_entities, list):
        map_entities = [map_entities] if map_entities else []
    return map_entities

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

def occupied_by(x: int, y: int, what: str, mapdb: Dict[str, Any]) -> bool:
    entity_map = get_map_at_coords(x_pos=x, y_pos=y, map_data_dict=mapdb)

    if entity_map:
        entity = entity_map.get(f"{x},{y}")

        if entity and entity.get("type") == what:
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
    with map_lock:
        coords = list(update_data.keys())[0]
        tile_data = update_data[coords]
        if coords in map_data_dict:
            for key, value in tile_data.items():
                map_data_dict[coords][key] = value
        else:
            raise KeyError(f"No data found at the given coordinates {coords}.")

def remove_from_map(coords: str, entity_type: str, map_data_dict: Dict[str, Any]) -> None:
    with map_lock:
        print("remove_from_map", coords, entity_type)

        # Check if the key exists in the map_data_dict
        if coords in map_data_dict:
            # Check if the type matches
            if map_data_dict[coords].get("type") == entity_type:
                # Remove the key from the map_data_dict
                del map_data_dict[coords]
                print(f"Entity of type {entity_type} at coordinates {coords} has been removed.")
            else:
                print(f"Entity of type {entity_type} not found at the given coordinates {coords}.")
        else:
            print(f"No data found at the given coordinates {coords}.")

def insert_map_data(existing_data: Dict[str, Any], new_data: Dict[str, Any]) -> None:
    with map_lock:
        print("insert_map_data", new_data)

        for coord, construction_info in new_data.items():
            if coord in existing_data:
                # If the coordinate already exists, update its values
                existing_data[coord].update(construction_info)
            else:
                # If the coordinate doesn't exist, create a new entry
                existing_data[coord] = construction_info

def is_visible(x1: int, y1: int, x2: int, y2: int, distance: int) -> bool:
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 <= distance ** 2

def get_map_data_limit(x_pos: int, y_pos: int, map_data_dict: Dict[str, Any], distance: int = 5) -> Dict[str, Any]:
    filtered_data = {}
    for coords, data in map_data_dict.items():
        x_map, y_map = map(int, coords.split(","))
        if is_visible(x_pos, y_pos, x_map, y_map, distance):
            filtered_data[coords] = data
    return filtered_data

def get_users_data_limit(x_pos: int, y_pos: int, usersdb: Dict[str, Any], distance: int = 5) -> Dict[str, Any]:
    filtered_data = {}
    for username, data in usersdb.items():
        x_map = data['x_pos']
        y_map = data['y_pos']
        if is_visible(x_pos, y_pos, x_map, y_map, distance):
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

def get_surrounding_map_and_user_data(user: str, user_data_dict: Dict[str, Any], map_data_dict: Dict[str, Any], distance: int) -> Dict[str, Any]:
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

def get_coords(entry: Dict[str, Any]) -> str:
    return list(entry.keys())[0]

def save_map_data(map_data_dict: Dict[str, Any], x_pos: int, y_pos: int, data: Dict[str, Any]) -> None:
    # Use a string coordinate key like 'x,y'
    coord_key = f"{x_pos},{y_pos}"
    map_data_dict[coord_key] = data


def get_map_at_coords(x_pos: int, y_pos: int, map_data_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """returns map data at a specific coordinate"""
    key = f"{x_pos},{y_pos}"

    # Check if the key exists in the map_data_dict
    if key in map_data_dict:
        return {key: map_data_dict[key]}

    # Return None if no data was found for the given coordinates
    return None

sql_lock = threading.Lock()


def strip_usersdb(usersdb: Dict[str, Any]) -> Dict[str, Any]:
    # strip usersdb of non-displayed data
    keys_to_keep = ['x_pos', 'y_pos', 'exp', 'hp', 'armor', 'img', 'online', 'type']
    new_usersdb = {}
    for username, user_data in usersdb.items():
        new_usersdb[username] = {k: v for k, v in user_data.items() if k in keys_to_keep}
    return new_usersdb