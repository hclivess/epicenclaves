import random


def train_sorcery(user, user_data, usersdb, mapdb):
    exp_cost = 5000
    magic_gain = 50
    failure_chance = 0.5

    if user_data['exp'] < exp_cost:
        return False, f"You need {exp_cost} exp to train sorcery. You only have {user_data['exp']} exp."

    if random.random() < failure_chance:
        user_data['exp'] -= exp_cost
        return False, f"Your sorcery training failed. You lost {exp_cost} exp."

    user_data['exp'] -= exp_cost
    user_data['sorcery'] = user_data.get('sorcery', 0) + magic_gain

    usersdb[user].update(user_data)
    return True, f"Your sorcery training was successful! You gained {magic_gain} magic power."
