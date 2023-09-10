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
                exp_gain = target_data["exp"] + 10 + user_data["exp"] / 10
                update_user_data(user=target_name, updated_values={"exp": exp_gain},
                                 user_data_dict=usersdb)

            if defeated_entity:
                messages.extend(defeat_outcome(defeated_entity, defeated_name, 0.5, usersdb))
                break


    return messages

def fight_npc(entry, user_data, user, usersdb, mapdb, npc):
    messages = []
    escaped = False

    while npc.alive and user_data["alive"] and not escaped:
        if npc.hp < 1:
            messages.append(f"The {npc.type} is dead")
            npc.alive = False

            if random.random() < 0.1:
                new_weapon = generate_weapon()
                messages.append(f"You found a {new_weapon['type']}!")
                user_data["unequipped"].append(new_weapon)

            remove_from_map(
                entity_type=npc.type.lower(),
                coords=get_coords(entry),
                map_data_dict=mapdb)

            updated_values = {
                "action_points": user_data["action_points"] - 1,
                "exp": user_data["exp"] + npc.exp_gain,
                "hp": user_data["hp"],
                "unequipped": user_data["unequipped"],
            }

            for key, value in npc.regular_drop.items():
                if key in user_data:
                    updated_values[key] = user_data[key] + value
                else:
                    updated_values[key] = value

            update_user_data(
                user=user,
                updated_values=updated_values,
                user_data_dict=usersdb,
            )

        elif user_data["hp"] < 1:
            if death_roll(npc.kill_chance):
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

        else:
            if user_data["hp"] > 0:
                damage = 1
                for weapon in user_data.get("equipped", {}):
                    if weapon.get("role") == "right_hand":
                        min_dmg = weapon.get("min_damage", 1)
                        max_dmg = weapon.get("max_damage", 1)

                        damage = get_damage(min_dmg, max_dmg, weapon, exp_bonus=exp_bonus(value=user_data["exp"]))
                        break

                npc.hp -= damage
                messages.append(
                    f"The {npc.type} takes {damage} damage and is left with {npc.hp} hp"
                )

            if npc.hp > 0:
                npc_dmg_roll = npc.roll_damage()
                user_data["hp"] -= npc_dmg_roll
                messages.append(
                    f"You take {npc_dmg_roll} damage and are left with {user_data['hp']} hp"
                )

    return messages




def fight(target, target_name, on_tile_map, on_tile_users, user_data, user, usersdb, mapdb):
    messages = []

    for entry in on_tile_map:
        entry_type = get_values(entry).get("type")

        if target == "boar" and entry_type == "boar":
            messages.extend(fight_npc(entry, user_data, user, usersdb, mapdb, Boar()))
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

import random


def get_damage(min_dmg, max_dmg, weapon, exp_bonus):
    damage = int(min_dmg + (max_dmg - min_dmg) * random.betavariate(2, 5))

    if random.randint(1, 100) > weapon["accuracy"]:
        return 0
    else:
        if random.randint(1, 100) <= weapon["crit_chance"]:
            damage = int(damage * (weapon["crit_dmg_pct"] / 100))

        return damage + exp_bonus


def death_roll(hit_chance):
    if hit_chance < 0 or hit_chance > 1:
        raise ValueError("Hit chance should be between 0 and 1 inclusive.")
    return random.random() < hit_chance
