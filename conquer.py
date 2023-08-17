from backend import get_values, remove_from_user, update_map_data, update_user_data, get_coords


def conquer(user, target, on_tile_map, usersdb, mapdb, user_data):
    if not on_tile_map:
        return "Looks like an empty tile"

    for entry in on_tile_map:
        print("entry", entry)
        owner = get_values(entry).get("control")

        if owner == user:
            return "You already own this tile"

        if get_values(entry).get("type") != target or user_data["action_points"] <= 0:
            return "Cannot acquire this type of tile"

        remove_from_user(owner, {"x_pos": user_data["x_pos"], "y_pos": user_data["y_pos"]}, usersdb)

        # Update the "control" attribute
        key = get_coords(entry)
        entry[key]["control"] = user

        # Update map and user data
        update_map_data(entry, mapdb)
        update_user_data(user=user, updated_values={
            "construction": entry,
            "action_points": user_data["action_points"] - 1
        }, user_data_dict=usersdb)

        return "Takeover successful"

    return "Something unexpected happened"