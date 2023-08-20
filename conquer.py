from backend import (
    get_values,
    remove_from_user,
    update_map_data,
    update_user_data,
    get_coords,
)
import random


# Calculate attack success based on attacker and defender strengths.
def attack_success(attacker, defender):
    total = attacker + defender
    if total == 0:
        return {"success": True, "chance": 100}
    chance = (attacker / total) * 100
    roll = random.uniform(0, 100)
    success = roll <= chance
    return {"success": success, "chance": chance}


# Check if the tile belongs to the user.
def is_user_tile_owner(entry, user):
    return get_values(entry).get("control") == user


# Check if tile can be acquired by the user.
def can_acquire_tile(entry, target):
    return get_values(entry).get("type") == target


# Check if the user has enough action points.
def has_sufficient_action_points(user_data):
    return user_data["action_points"] >= 10


# Handle the case when attack fails.
def process_attack_failure(user, user_data, usersdb, chance):
    update_user_data(
        user=user,
        updated_values={
            "action_points": user_data["action_points"] - 10,
            "hp": 1,
            "army_free": 0,
        },
        user_data_dict=usersdb,
    )
    return f"Your army was crushed in battle, the chance of success was {chance}! You were seriously hurt."


# Handle the case when attack is successful.
def process_attack_success(
    entry, user, usersdb, mapdb, user_data, enemy_army, your_army, chance
):
    remaining_army = max(your_army - enemy_army, 0)
    user_data["army_free"] = remaining_army

    owner = get_values(entry).get("control")
    remove_from_user(
        owner, {"x_pos": user_data["x_pos"], "y_pos": user_data["y_pos"]}, usersdb
    )

    key = get_coords(entry)
    entry[key]["control"] = user

    update_map_data(entry, mapdb)
    update_user_data(
        user=user,
        updated_values={
            "construction": entry,
            "action_points": user_data["action_points"] - 1,
            "army_free": remaining_army,
        },
        user_data_dict=usersdb,
    )
    return f"Takeover successful. The chance was {chance}"


# Main function to handle tile conquest.
def attempt_conquer(user, target, on_tile_map, usersdb, mapdb, user_data):
    if not on_tile_map:
        return "Looks like an empty tile"

    for entry in on_tile_map:
        if is_user_tile_owner(entry, user):
            return "You already own this tile"
        if not can_acquire_tile(entry, target):
            return "Cannot acquire this type of tile"
        if not has_sufficient_action_points(user_data):
            return "You need at least 10 action points to attack"

        your_army = user_data.get("army_free", 0)
        enemy_army = get_values(entry).get("soldiers", 0)

        conquered = attack_success(attacker=your_army, defender=enemy_army)

        if not conquered["success"]:
            return process_attack_failure(user, user_data, usersdb, conquered["chance"])

        return process_attack_success(
            entry,
            user,
            usersdb,
            mapdb,
            user_data,
            enemy_army,
            your_army,
            conquered["chance"],
        )

    return "Something unexpected happened"
