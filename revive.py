import math
from backend import update_user_data

def calculate_revive_cost(exp):
    base_cost = 500
    exp_cost = math.ceil(exp * 0.1)
    return base_cost + exp_cost

def revive(user, user_data, league, usersdb):
    exp = user_data.get("exp", 0)
    revive_cost = calculate_revive_cost(exp)
    exp_deduction = math.ceil(exp * 0.1)

    if user_data.get("action_points", 0) >= revive_cost:
        new_ap = user_data["action_points"] - revive_cost
        new_exp = exp - exp_deduction
        update_user_data(user=user, updated_values={
            "alive": True,
            "hp": 100,
            "action_points": new_ap,
            "exp": new_exp
        }, user_data_dict=usersdb[league])
        message = f"You awaken from the dead. {revive_cost} action points and {exp_deduction} exp points were deducted."
    else:
        message = f"You do not have enough action points to revive. You need {revive_cost} action points."
    return message