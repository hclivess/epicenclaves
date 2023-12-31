from backend import get_values, update_user_data
from map import owned_by, update_map_data, get_coords


def deploy_army(user, on_tile_map, usersdb, mapdb, user_data):
    if not owned_by(user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb):
        return "You do not own this tile"
    if user_data["action_points"] < 1:
        return "Not enough action points to build"
    if not user_data.get("army_free") > 0:
        return "Not enough free army available"

    for entry in on_tile_map:
        if get_values(entry).get("role") == "building":
            updated_user_values = {
                "army_free": user_data["army_free"] - 1,
                "army_deployed": user_data["army_deployed"] + 1,
                "action_points": user_data["action_points"] - 1,
            }

            player_pos = f"{user_data['x_pos']},{user_data['y_pos']}"
            user_data["construction"][player_pos]["army"] += 1
            updated_user_values["construction"] = {player_pos: user_data["construction"][player_pos]}

            update_user_data(user, updated_user_values, usersdb)

            key = get_coords(entry)
            entry[key]["army"] = user_data["construction"][player_pos]["army"]
            update_map_data(entry, mapdb)

            return "Soldiers deployed"

    return "Army must be stationed on a building"

def remove_army(user, on_tile_map, usersdb, mapdb, user_data):
    if not owned_by(user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb):
        return "You do not own this tile"
    if user_data["action_points"] < 1:
        return "Not enough action points to remove"

    player_pos = f"{user_data['x_pos']},{user_data['y_pos']}"
    if user_data["construction"][player_pos]["army"] <= 0:
        return "No army to remove"

    for entry in on_tile_map:
        if get_values(entry).get("role") == "building":
            updated_user_values = {
                "army_free": user_data["army_free"] + 1,
                "army_deployed": user_data["army_deployed"] - 1,
                "action_points": user_data["action_points"] - 1,
            }

            user_data["construction"][player_pos]["army"] -= 1
            updated_user_values["construction"] = {player_pos: user_data["construction"][player_pos]}

            update_user_data(user, updated_user_values, usersdb)

            key = get_coords(entry)
            entry[key]["army"] = user_data["construction"][player_pos]["army"]
            update_map_data(entry, mapdb)

            return "Soldiers removed"

    return "Army must be stationed on a building"
