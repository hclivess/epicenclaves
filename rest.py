from backend import update_user_data
from map import occupied_by, owned_by


def attempt_rest(user, user_data, hours_arg, usersdb, mapdb):
    hours = int(hours_arg)
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    proper_tile = occupied_by(x_pos, y_pos, what="inn", mapdb=mapdb)
    under_control = owned_by(x_pos, y_pos, control=user, mapdb=mapdb)

    if user_data["hp"] >= 100:
        return "You are already fully rested"
    elif not proper_tile:
        return "You cannot rest here, inn required"
    elif not under_control:
        return "This location is not under your control"
    elif user_data["action_points"] < hours:
        return "Out of action points to rest"

    # If the control checks pass and the user is able to rest
    new_hp = min(user_data["hp"] + hours, 100)  # Ensures HP doesn't exceed 100
    new_ap = user_data["action_points"] - hours
    update_user_data(
        user=user,
        updated_values={"hp": new_hp, "action_points": new_ap},
        user_data_dict=usersdb,
    )
    return "You feel more rested"
