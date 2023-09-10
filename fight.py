import math
from backend import update_user_data, get_values
from map import remove_from_map, get_coords
from entities import Boar
from weapon_generator import generate_weapon
import random


def player_attack(attacker, defender, attacker_name, messages):
    if attacker["hp"] > 0:
        damage = 1  # Default damage
        for weapon in attacker.get("equipped", {}):
            if weapon.get("role") == "right_hand":
                min_dmg = weapon.get("min_damage", 1)
                max_dmg = weapon.get("max_damage", 1)
                damage = get_damage(min_dmg, max_dmg, weapon, exp_bonus=exp_bonus(value=attacker["exp"]))
                break

        defender["hp"] -= damage
        if attacker_name == "You":
            messages.append(f"You hit for {damage} damage, they have {defender['hp']} left")
        else:
            messages.append(f"{attacker_name} hits you for {damage} damage, you have {defender['hp']} left")


def defeat_outcome(entity, entity_name, chance, usersdb):
    messages = []
    if death_roll(chance):
        messages.append(f"{entity_name} is defeated.")
        new_data = {
            "alive": False,
            "hp": 0,
            "action_points": 0
        }
    else:
        messages.append(f"{entity_name} barely managed to escape.")
        new_data = {
            "action_points": entity["action_points"] - 1,
            "hp": 1
        }
    update_user_data(user=entity_name, updated_values=new_data, user_data_dict=usersdb)
    return messages


def fight_player(entry, target_name, user_data, user, usersdb):
    messages = []
    entry_name = get_coords(entry)
    target_data = entry[entry_name]

    if target_name == entry_name:
        if target_data["hp"] == 0:
            messages.append(f"{entry_name} is already dead!")
            return messages

        if target_data["exp"] < 10:
            messages.append(f"{entry_name} is too inexperienced to challenge!")
            return messages

        messages.append(f"You challenged {entry_name}")

        while target_data["alive"] and user_data["alive"]:
            player_attack(target_data, user_data, entry_name, messages)
            player_attack(user_data, target_data, "You", messages)

            if 10 > target_data["hp"] > 0:
                messages.append(f"{entry_name} has run seeing they stand no chance against you!")
                break

            defeated_entity = None
            defeated_name = None

            if target_data["hp"] <= 0:
                defeated_entity = target_data
                defeated_name = entry_name
                exp_gain = user_data["exp"] + 10 + target_data["exp"] / 10
                update_user_data(user=user, updated_values={"exp": exp_gain}, user_data_dict=usersdb)

            elif user_data["hp"] <= 0:
                defeated_entity = user_data
                defeated_name = user
                update_user_data(user=target_name, updated_values={"exp": target_data["exp"] + 10},
                                 user_data_dict=usersdb)

            if defeated_entity:
                messages.extend(defeat_outcome(defeated_entity, defeated_name, 0.5, usersdb))
                break

    return messages

def fight_boar(entry, user_data, user, usersdb, mapdb):
    messages = []
    boar = Boar()
    escaped = False

    while boar.alive and user_data["alive"] and not escaped:
        # Check if the boar should be dead
        if boar.hp < 1:
            messages.append("The boar is dead")
            boar.alive = False

            if random.random() < 0.1:  # 10% chance of dropping a weapon
                new_weapon = generate_weapon()
                messages.append(f"You found a {new_weapon['type']}!")
                user_data["unequipped"].append(new_weapon)

            remove_from_map(
                entity_type="boar", coords=get_coords(entry), map_data_dict=mapdb
            )
            update_user_data(
                user=user,
                updated_values={
                    "action_points": user_data["action_points"] - 1,
                    "exp": user_data["exp"] + 1,
                    "food": user_data["food"] + 1,
                    "hp": user_data["hp"],
                    "unequipped": user_data["unequipped"]
                },
                user_data_dict=usersdb,
            )

        # Check if the user should be dead or escape
        elif user_data["hp"] < 1:
            if death_roll(boar.kill_chance):
                messages.append("You died")
                user_data["alive"] = False
                update_user_data(
                    user=user,
                    updated_values={"alive": user_data["alive"], "hp": 0},
                    user_data_dict=usersdb,
                )
            else:
                messages.append("You are almost dead but managed to escape")
                update_user_data(
                    user=user,
                    updated_values={
                        "action_points": user_data["action_points"] - 1,
                        "hp": 1,
                    },
                    user_data_dict=usersdb,
                )
                escaped = True

        # Attack logic, ensuring entities with 0 hp don't attack
        else:
            # User attacks the boar if they have more than 0 hp
            if user_data["hp"] > 0:
                damage = 1
                for weapon in user_data.get("equipped", {}):
                    if weapon.get("role") == "right_hand":
                        min_dmg = weapon.get("min_damage", 1)
                        max_dmg = weapon.get("max_damage", 1)

                        damage = get_damage(min_dmg, max_dmg, weapon, exp_bonus=exp_bonus(value=user_data["exp"]))
                        break

                boar.hp -= damage
                messages.append(
                    f"The boar takes {damage} damage and is left with {boar.hp} hp"
                )

            # Boar attacks the user if it has more than 0 hp
            if boar.hp > 0:
                boar_dmg_roll = boar.roll_damage()
                user_data["hp"] -= boar_dmg_roll
                messages.append(
                    f"You take {boar_dmg_roll} damage and are left with {user_data['hp']} hp"
                )

    return messages


def fight(target, target_name, on_tile_map, on_tile_users, user_data, user, usersdb, mapdb):
    messages = []

    for entry in on_tile_map:
        entry_type = get_values(entry).get("type")

        if target == "boar" and entry_type == "boar":
            messages.extend(fight_boar(entry, user_data, user, usersdb, mapdb))
        elif target == "player" and entry_type == "player":
            messages.extend(fight_player(entry, target_name, user_data, user, usersdb))

    for entry in on_tile_users:
        entry_type = get_values(entry).get("type")
        entry_name = get_coords(entry)

        if target == "player" and entry_type == "player" and target_name == entry_name:
            messages.extend(fight_player(entry, target_name, user_data, user, usersdb))

    return messages


def get_fight_preconditions(user_data):
    if user_data["action_points"] < 1:
        return "Not enough action points to slay"
    if not user_data["alive"]:
        return "You are dead"
    return None


def exp_bonus(value, base=10):
    if value <= 0:
        return 0

    lower = 1
    upper = 10
    log_lower = math.log(lower, base)
    log_upper = math.log(upper, base)
    log_value = math.log(value, base)

    scaled_value = int(log_lower + (log_upper - log_lower) * ((log_value - log_lower) / (log_upper - log_lower)))
    return scaled_value


import random

def get_damage(min_dmg, max_dmg, weapon, exp_bonus):
    damage_dict = {}
    damage = int(min_dmg + (max_dmg - min_dmg) * random.betavariate(2, 5))
    damage_type = "normal"

    hit_chance = 100 - weapon["miss_chance"]
    if random.randint(1, 100) > hit_chance:
        damage_dict["damage"] = 0
        damage_dict["damage_type"] = "missed"
    else:
        if random.randint(1, 100) <= weapon["crit_chance"]:
            damage = int(damage * (weapon["crit_dmg_pct"] / 100))
            damage_type = "critical"
        damage_dict["damage"] = damage
        damage_dict["damage_type"] = damage_type

    damage_dict["damage"] = damage
    damage_dict["damage_type"] = damage_type
    return damage_dict + exp_bonus


def death_roll(hit_chance):
    if hit_chance < 0 or hit_chance > 1:
        raise ValueError("Hit chance should be between 0 and 1 inclusive.")
    return random.random() < hit_chance
