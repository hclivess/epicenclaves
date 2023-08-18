from backend import occupied_by, owned_by, has_item, update_user_data


def chop_forest(user, user_data, usersdb, mapdb):
    proper_tile = occupied_by(
        user_data["x_pos"], user_data["y_pos"], what="forest", mapdb=mapdb
    )
    item = "axe"

    under_control = owned_by(
        user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb
    )

    if not has_item(user_data, item):
        return f"You have no {item} at hand"

    if not under_control:
        return "You do not own this forrest"

    if not proper_tile:
        return "Not on a forest tile"

    if user_data["action_points"] <= 0:
        return "Out of action points to chop"

    new_wood = user_data["wood"] + 1
    new_ap = user_data["action_points"] - 1

    update_user_data(
        user=user,
        updated_values={"action_points": new_ap, "wood": new_wood},
        user_data_dict=usersdb,
    )

    return "Chopping successful"
