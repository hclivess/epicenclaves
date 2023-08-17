from backend import get_values, remove_from_user, update_map_data, update_user_data, get_coords


def attack_success(attacker, defender):
    total = attacker + defender

    # Ensure there's no division by zero
    if total == 0:
        return False

    # Calculate the proportional chance for the attacker
    chance = (attacker / total) * 100

    # Roll a random number between 0 and 100
    roll = random.uniform(0, 100)

    return roll <= chance


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

        your_army = user_data.get("army_free")
        enemy_army = get_values(entry).get("soldiers")

        conquered = attack_success(attacker=your_army, defender=enemy_army)

        if not conquered:
            return "Your army was defeated in battle!"

        # Subtract enemy army from user army, but not less than 0
        remaining_army = max(your_army - enemy_army, 0)
        user_data["army_free"] = remaining_army

        remove_from_user(owner,
                         {"x_pos": user_data["x_pos"],
                          "y_pos": user_data["y_pos"]},
                         usersdb)

        # Update the "control" attribute
        key = get_coords(entry)
        entry[key]["control"] = user

        # Update map and user data
        update_map_data(entry, mapdb)
        update_user_data(user=user, updated_values={
            "construction": entry,
            "action_points": user_data["action_points"] - 1,
            "army_free": remaining_army
        }, user_data_dict=usersdb)

        return "Takeover successful"

    return "Something unexpected happened"
