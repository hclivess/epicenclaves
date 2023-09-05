from backend import has_item_equipped, update_user_data
from map import occupied_by, owned_by


def chop_forest(user, chop_amount, user_data, usersdb, mapdb):
    # Check if the user has an axe equipped
    item = "axe"
    if not has_item_equipped(user_data, item):
        return f"You have no {item} at hand"

    # Check if the forest is under the user's control
    under_control = owned_by(
        user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb
    )
    if not under_control:
        return "You do not own this forest"

    # Check if the user is on a forest tile
    proper_tile = occupied_by(
        user_data["x_pos"], user_data["y_pos"], what="forest", mapdb=mapdb
    )
    if not proper_tile:
        return "Not on a forest tile"

    # Check if the user has enough action points
    if user_data["action_points"] < chop_amount:
        return "Not enough action points to chop"

    # Perform wood chopping
    new_wood = user_data["wood"] + chop_amount
    new_ap = user_data["action_points"] - chop_amount  # Deduct action points

    # Update user's data
    updated_values = {"action_points": new_ap, "wood": new_wood}
    update_user_data(
        user=user,
        updated_values=updated_values,
        user_data_dict=usersdb,
    )

    return "Chopping successful"
