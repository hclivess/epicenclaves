import random
from player import User, calculate_total_hp, calculate_total_mana


def train_sorcery(user, user_data, usersdb, mapdb):
    EXP_COST = 5000
    MAGIC_GAIN = 50
    FAILURE_CHANCE = 0.5

    if user_data['exp'] < EXP_COST:
        return False, f"You need {EXP_COST} exp to train sorcery. You only have {user_data['exp']} exp."

    user_data['exp'] -= EXP_COST

    player = User(user_data['username'], user_data['x_pos'], user_data['y_pos'])

    # Recalculate HP and mana after spending EXP
    user_data['hp'] = calculate_total_hp(player.base_hp, user_data['exp'])
    user_data['mana'] = calculate_total_mana(player.base_hp, user_data['exp'])

    if random.random() < FAILURE_CHANCE:
        usersdb[user].update(user_data)
        return False, f"Your sorcery training failed. You lost {EXP_COST} exp."

    user_data['sorcery'] = user_data.get('sorcery', 0) + MAGIC_GAIN

    usersdb[user].update(user_data)
    return True, f"Your sorcery training was successful! You gained {MAGIC_GAIN} magic power."