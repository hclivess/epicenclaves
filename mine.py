from backend import has_item_equipped, update_user_data
from map import occupied_by, owned_by


def mine_mountain(user, chop_amount, user_data, usersdb, mapdb):
    # Check if the user has an axe equipped
    item = "axe"
    if not has_item_equipped(user_data, item):
        return f"You have no {item} at hand"

    # Check if the forest is under the user's control
    under_control = owned_by(
        user_data["x_pos"], user_data["y_pos"], control=user, mapdb=mapdb
    )
    if not under_control:
        return "You do not own this mountain"

    # Check if the user is on a mountain tile
    proper_tile = occupied_by(
        user_data["x_pos"], user_data["y_pos"], what="mountain", mapdb=mapdb
    )
    if not proper_tile:
        return "Not on a mountain tile"

    # Check if the user has enough action points
    if user_data["action_points"] < chop_amount:
        return "Not enough action points to mine"

    # Perform wood chopping
    new_bis = user_data["bismuth"] + chop_amount
    new_ap = user_data["action_points"] - chop_amount  # Deduct action points

    # Update user's data
    updated_values = {"action_points": new_ap, "bismuth": new_bis}
    update_user_data(
        user=user,
        updated_values=updated_values,
        user_data_dict=usersdb,
    )

    return "Mining successful"
