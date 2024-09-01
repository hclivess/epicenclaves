from backend import update_user_data
from map import occupied_by, owned_by


def calculate_total_hp(base_hp: int, exp: int) -> int:
    # This function should be the same as the one we defined earlier
    hp_bonus = int(exp / 10)  # 1 extra HP for every 10 exp
    return base_hp + hp_bonus

def calculate_total_hp(base_hp: int, exp: int) -> int:
    hp_bonus = int(exp / 10)  # 1 extra HP for every 10 exp
    return base_hp + hp_bonus

def attempt_rest(user, user_data, hours_arg, usersdb, mapdb):
    hours = int(hours_arg)
    x_pos, y_pos = user_data["x_pos"], user_data["y_pos"]

    proper_tile = occupied_by(x_pos, y_pos, what="inn", mapdb=mapdb)
    under_control = owned_by(x_pos, y_pos, control=user, mapdb=mapdb)

    current_hp = user_data["hp"]
    max_base_hp = 100  # The maximum base HP is always 100
    max_total_hp = calculate_total_hp(max_base_hp, user_data["exp"])

    if current_hp >= max_total_hp:
        return "You are already fully rested"
    elif not proper_tile:
        return "You cannot rest here, inn required"
    elif not under_control:
        return "This location is not under your control"
    elif user_data["action_points"] < hours:
        return "Out of action points to rest"

    # If the control checks pass and the user is able to rest
    hp_recovered = hours  # Assuming 1 HP recovered per hour
    new_hp = min(current_hp + hp_recovered, max_total_hp)
    new_ap = user_data["action_points"] - hours

    update_user_data(
        user=user,
        updated_values={"hp": new_hp, "action_points": new_ap},
        user_data_dict=usersdb,
    )

    hp_gain = new_hp - current_hp
    return f"You feel more rested. You recovered {hp_gain} HP. Your total HP is now {new_hp}/{max_total_hp}."