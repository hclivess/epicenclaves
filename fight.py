import random
import math
from typing import List, Dict, Any, Optional, Tuple
from map import get_coords, remove_from_map
from player import calculate_total_hp, has_item_equipped, drop_random_item
from backend import update_user_data
from item_generator import generate_weapon, generate_armor
from entities import entity_types, Enemy


def fight(target: str, target_name: str, on_tile_map: List[Dict], on_tile_users: List[Dict], user_data: Dict, user: str,
          usersdb: Dict, mapdb: Dict) -> Dict:
    print(f"Starting fight. Target: {target}, Target name: {target_name}")

    max_base_hp = 100
    max_total_hp = calculate_total_hp(max_base_hp, user_data["exp"])

    battle_data = {
        "player": {"name": user, "max_hp": max_total_hp, "current_hp": user_data["hp"]},
        "enemy": {"name": target, "max_hp": 0, "current_hp": 0},
        "rounds": []
    }

    print("Initial battle_data", battle_data)

    if target.lower() == "player":
        target_data = next((entry for entry in on_tile_users if get_coords(entry) == target_name), None)
        if target_data:
            target_user_data = target_data[target_name]
            print(f"Fighting player: {target_name}")
            fight_player(battle_data, target_user_data, target_name, user_data, user, usersdb)
    else:
        target_data = next(
            (entry for entry in on_tile_map if entry[get_coords(entry)]["type"].lower() == target.lower()), None)
        if target_data:
            coords = get_coords(target_data)
            npc_data = target_data[coords]
            print(f"Fighting NPC: {target}")

            fight_npc(battle_data, npc_data, coords, user_data, user, usersdb, mapdb)

    if not battle_data["rounds"]:
        battle_data["rounds"].append({"round": 0, "message": f"No valid target found: {target}"})

    print("Final battle_data", battle_data)
    return {"battle_data": battle_data}


def fight_npc(battle_data: Dict, npc_data: Dict[str, Any], coords: str, user_data: Dict, user: str, usersdb: Dict,
              mapdb: Dict) -> None:
    damage_dealt = 0

    enemy_class = entity_types.get(npc_data['type'].lower())
    if enemy_class is None:
        battle_data["rounds"].append({"round": 0, "message": f"Unknown enemy type: {npc_data['type']}"})
        return

    enemy = enemy_class(npc_data['level'])

    battle_data["enemy"].update({
        "name": enemy.type,
        "max_hp": enemy.max_hp,
        "current_hp": enemy.hp,
        "level": enemy.level
    })

    max_base_hp = 100
    max_total_hp = calculate_total_hp(max_base_hp, user_data["exp"])

    round_number = 0
    while enemy.hp > 0 and user_data["alive"]:
        round_number += 1
        round_data = {"round": round_number, "actions": []}

        if user_data["hp"] > 0:
            exp_bonus_value = exp_bonus(user_data["exp"])
            user_dmg = get_weapon_damage(user_data, exp_bonus_value)

            if user_dmg['damage'] > 0:
                if enemy.attempt_evasion():
                    round_data["actions"].append({
                        "actor": "enemy",
                        "type": "evasion",
                        "message": f"The level {enemy.level} {enemy.type} evaded your attack."
                    })
                    damage_dealt = 0
                elif enemy.attempt_block():
                    blocked_damage = int(user_dmg['damage'] * enemy.block_reduction)
                    damage_dealt = max(0, user_dmg['damage'] - blocked_damage)
                    round_data["actions"].append({
                        "actor": "enemy",
                        "type": "block",
                        "message": f"The level {enemy.level} {enemy.type} blocked part of your attack. Damage reduced from {user_dmg['damage']} to {damage_dealt}."
                    })
                else:
                    damage_dealt = user_dmg['damage']
            else:
                weapon = next((item for item in user_data.get("equipped", []) if item.get("slot") == "right_hand"), None)
                if weapon:
                    round_data["actions"].append({
                        "actor": "player",
                        "type": "miss",
                        "damage": 0,
                        "message": f"Your attack with {weapon['type']} missed the {enemy.type}."
                    })
                else:
                    round_data["actions"].append({
                        "actor": "player",
                        "type": "miss",
                        "damage": 0,
                        "message": f"Your unarmed attack missed the {enemy.type}."
                    })

            if damage_dealt > 0:
                enemy.hp = max(0, enemy.hp - damage_dealt)  # Ensure HP doesn't go below 0
                round_data["actions"].append({
                    "actor": "player",
                    "type": "attack",
                    "damage": damage_dealt,
                    "message": f"You {user_dmg['message']} the level {enemy.level} {enemy.type} for {damage_dealt} damage. Enemy HP: {enemy.hp}/{enemy.max_hp}"
                })

        if enemy.hp > 0:
            npc_dmg = enemy.roll_damage()
            final_damage, absorbed_damage = apply_armor_protection(user_data, npc_dmg["damage"], round_data,
                                                                   round_number)
            user_data["hp"] = max(0, user_data["hp"] - final_damage)  # Ensure HP doesn't go below 0
            round_data["actions"].append({
                "actor": "enemy",
                "type": "attack",
                "damage": final_damage,
                "message": f"The level {enemy.level} {enemy.type} {npc_dmg['message']} you for {final_damage} damage. Your HP: {user_data['hp']}/{max_total_hp}"
            })

        round_data["player_hp"] = user_data["hp"]
        round_data["enemy_hp"] = enemy.hp
        battle_data["rounds"].append(round_data)

        if enemy.hp <= 0:
            defeat_round = process_npc_defeat(enemy, coords, user_data, user, usersdb, mapdb, battle_data, round_number)
            battle_data["rounds"].append(defeat_round)
            break

        if user_data["hp"] <= 0:
            if death_roll(enemy.crit_chance):
                battle_data["rounds"].append({
                    "round": round_number + 1,
                    "actions": [{
                        "actor": "system",
                        "type": "defeat",
                        "message": f"You have been defeated and died. Your HP: 0/{max_total_hp}"
                    }],
                    "player_hp": 0,
                    "enemy_hp": enemy.hp
                })
                user_data["alive"] = False
                update_user_data(user=user, updated_values={"alive": False, "hp": 0}, user_data_dict=usersdb)
            else:
                battle_data["rounds"].append({
                    "round": round_number + 1,
                    "actions": [{
                        "actor": "system",
                        "type": "escape",
                        "message": f"You are critically wounded but managed to escape. Your HP: 1/{max_total_hp}"
                    }],
                    "player_hp": 1,
                    "enemy_hp": enemy.hp
                })
                update_user_data(user=user, updated_values={"action_points": user_data["action_points"] - 1, "hp": 1},
                                 user_data_dict=usersdb)
            break


def fight_player(battle_data: Dict, target_data: Dict, target_name: str, user_data: Dict, user: str, usersdb: Dict) -> None:
    print(f"Starting fight_player. Target: {target_name}, User: {user}")
    print(f"Target data: {target_data}")
    print(f"User data: {user_data}")

    max_base_hp = 100
    user_max_total_hp = calculate_total_hp(max_base_hp, user_data["exp"])
    target_max_total_hp = calculate_total_hp(max_base_hp, target_data["exp"])

    battle_data["player"].update({
        "name": user,
        "max_hp": user_max_total_hp,
        "current_hp": user_data["hp"]
    })

    battle_data["enemy"].update({
        "name": target_name,
        "max_hp": target_max_total_hp,
        "current_hp": target_data["hp"]
    })

    battle_data["rounds"].append({
        "round": 0,
        "player_hp": user_data["hp"],
        "enemy_hp": target_data["hp"],
        "message": f"You challenged {target_name}. Your HP: {user_data['hp']}/{user_max_total_hp}, {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}",
        "actions": []
    })

    round_number = 0
    while target_data["hp"] > 0 and user_data["hp"] > 0:
        round_number += 1
        round_data = {"round": round_number, "actions": []}

        # Player attacks target
        exp_bonus_value = exp_bonus(user_data["exp"])
        user_dmg = get_weapon_damage(user_data, exp_bonus_value)
        final_damage, absorbed_damage = apply_armor_protection(target_data, user_dmg['damage'], round_data,
                                                               round_number)
        target_data["hp"] = max(0, target_data["hp"] - final_damage)

        round_data["actions"].append({
            "actor": "player",
            "type": "attack",
            "damage": final_damage,
            "message": f"You {user_dmg['message']} {target_name} for {final_damage} damage. {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}"
        })

        if target_data["hp"] <= 0:
            battle_data["rounds"].append(round_data)  # Append the round data before processing defeat
            experience = user_data["exp"] + 10 + target_data["exp"] // 10
            update_user_data(user, {"exp": experience}, usersdb)
            process_player_defeat(target_data, target_name, user_data, user, 0.5, usersdb, battle_data["rounds"],
                                  round_number, target_max_total_hp)
            break

        # Target attacks player
        exp_bonus_value = exp_bonus(target_data["exp"])
        target_dmg = get_weapon_damage(target_data, exp_bonus_value)
        final_damage, absorbed_damage = apply_armor_protection(user_data, target_dmg['damage'], round_data,
                                                               round_number)
        user_data["hp"] = max(0, user_data["hp"] - final_damage)

        round_data["actions"].append({
            "actor": "enemy",
            "type": "attack",
            "damage": final_damage,
            "message": f"{target_name} {target_dmg['message']} you for {final_damage} damage. Your HP: {user_data['hp']}/{user_max_total_hp}"
        })

        if user_data["hp"] <= 0:
            battle_data["rounds"].append(round_data)  # Append the round data before processing defeat
            experience = target_data["exp"] + 10 + user_data["exp"] // 10
            update_user_data(target_name, {"exp": experience}, usersdb)
            process_player_defeat(user_data, user, target_data, target_name, 0.5, usersdb, battle_data["rounds"],
                                  round_number, user_max_total_hp)
            break

        round_data["player_hp"] = user_data["hp"]
        round_data["enemy_hp"] = target_data["hp"]
        round_data["actions"].append({
            "actor": "system",
            "type": "round_end",
            "message": f"Round {round_number} complete. Your HP: {user_data['hp']}/{user_max_total_hp}, {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}"
        })
        battle_data["rounds"].append(round_data)

        if 0 < target_data["hp"] < 10:
            battle_data["rounds"].append({
                "round": round_number + 1,
                "player_hp": user_data["hp"],
                "enemy_hp": target_data["hp"],
                "message": f"{target_name} has fled seeing they stand no chance against you! Your HP: {user_data['hp']}/{user_max_total_hp}, {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}",
                "actions": []
            })
            break

    # Update final battle stats
    battle_data["player"]["current_hp"] = user_data["hp"]
    battle_data["enemy"]["current_hp"] = target_data["hp"]

    print(f"Fight ended. Rounds: {len(battle_data['rounds'])}, Player HP: {user_data['hp']}, Enemy HP: {target_data['hp']}")

def process_npc_defeat(enemy: Enemy, coords: str, user_data: Dict, user: str, usersdb: Dict, mapdb: Dict,
                       battle_data: Dict, round_number: int) -> Dict:
    defeat_round = {
        "round": round_number + 1,
        "actions": [{
            "actor": "system",
            "type": "defeat",
            "message": f"The level {enemy.level} {enemy.type} is defeated"
        }],
        "player_hp": user_data["hp"],
        "enemy_hp": 0
    }

    if random.random() < enemy.drop_chance:
        min_item_level = max(1, int(enemy.level / 2))
        max_item_level = enemy.level
        new_item = generate_weapon(min_level=min_item_level,
                                   max_level=max_item_level) if random.random() < 0.5 else generate_armor(
            min_level=min_item_level, max_level=max_item_level)

        defeat_round["actions"].append({
            "actor": "system",
            "type": "loot",
            "message": f"You found a level {new_item['level']} {new_item['type']}!",
            "item": new_item
        })
        user_data["unequipped"].append(new_item)
    else:
        defeat_round["actions"].append({
            "actor": "system",
            "type": "no_loot",
            "message": f"The defeated {enemy.type} didn't drop any items."
        })

    remove_from_map(entity_type=enemy.type.lower(), coords=coords, map_data_dict=mapdb)

    experience_gained = enemy.experience
    defeat_round["actions"].append({
        "actor": "system",
        "type": "exp_gain",
        "message": f"You gained {experience_gained} experience points.",
        "exp_gained": experience_gained
    })

    ingredients = user_data.get("ingredients", {})
    for item, amount in enemy.regular_drop.items():
        ingredients[item] = ingredients.get(item, 0) + amount

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "exp": user_data["exp"] + experience_gained,
        "hp": user_data["hp"],
        "unequipped": user_data["unequipped"],
        "ingredients": ingredients
    }

    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

    return defeat_round


def player_attack(attacker: Dict, defender: Dict, attacker_name: str, rounds: List[Dict],
                  round_number: int, attacker_max_hp: int, defender_max_hp: int) -> None:
    if attacker["hp"] <= 0:
        return

    exp_bonus_value = exp_bonus(attacker["exp"])
    damage_dict = get_weapon_damage(attacker, exp_bonus_value)

    # Create a new round data dictionary
    round_data = {
        "round": round_number,
        "player_hp": attacker["hp"] if attacker_name == "You" else defender["hp"],
        "enemy_hp": defender["hp"] if attacker_name == "You" else attacker["hp"],
        "actions": []
    }

    final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], round_data, round_number)

    defender["hp"] = max(0, defender["hp"] - final_damage)  # Ensure HP doesn't go below 0

    if attacker_name == "You":
        message = (f"You {damage_dict['message']} for {final_damage} damage "
                   f"(Base: {damage_dict['base_damage']}, Exp bonus: {damage_dict['exp_bonus']}). "
                   f"Your HP: {attacker['hp']}/{attacker_max_hp}, Enemy HP: {defender['hp']}/{defender_max_hp}")
    else:
        message = (f"{attacker_name} hits you for {final_damage} {damage_dict['message']} damage "
                   f"(Base: {damage_dict['base_damage']}, Exp bonus: {damage_dict['exp_bonus']}). "
                   f"Your HP: {defender['hp']}/{defender_max_hp}, {attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}")

    round_data["actions"].append({
        "actor": "player" if attacker_name == "You" else "enemy",
        "type": "attack",
        "damage": final_damage,
        "message": message
    })
    rounds.append(round_data)

def exp_bonus(value: int, base: int = 10) -> int:
    if value <= 0:
        return 0
    return int(math.log(value, base))

def death_roll(hit_chance: float) -> bool:
    return random.random() < hit_chance

def apply_armor_protection(defender: Dict, initial_damage: int, round_data: Dict, round_number: int) -> Tuple[int, int]:
    armor_protection = 0
    is_player = defender.get('name', 'You') == 'You'

    all_armor_slots = [armor for armor in defender.get("equipped", []) if armor.get("role") == "armor"]

    if all_armor_slots:
        selected_armor = random.choice(all_armor_slots)

        if selected_armor.get("type") != "empty" and selected_armor["durability"] > 0:
            effective_protection = calculate_armor_effectiveness(selected_armor, initial_damage)
            armor_protection = min(initial_damage, effective_protection)

            damage_reduction_percentage = (armor_protection / initial_damage) * 100 if initial_damage > 0 else 0

            armor_info = f"Your {selected_armor['type']}" if is_player else f"{defender['name']}'s {selected_armor['type']}"
            final_damage = max(0, initial_damage - armor_protection)

            round_data["actions"].append({
                "actor": "system",
                "type": "armor",
                "message": (
                    f"{armor_info} (Base Protection: {selected_armor['protection']}, "
                    f"Efficiency: {selected_armor['efficiency']}%, "
                    f"Durability: {selected_armor['durability']}/{selected_armor['max_durability']}) "
                    f"reduced damage by {damage_reduction_percentage:.1f}% ({armor_protection} points). "
                )
            })

            durability_loss = math.ceil(initial_damage / 10)
            selected_armor["durability"] = max(0, selected_armor["durability"] - durability_loss)

            if selected_armor["durability"] <= 0:
                message = f"Your {selected_armor['type']} has broken and is no longer usable!" if is_player else f"{defender['name']}'s {selected_armor['type']} has broken and is no longer usable!"
                round_data["actions"].append({
                    "actor": "system",
                    "type": "armor_break",
                    "message": message
                })
                defender["equipped"] = [item for item in defender["equipped"] if item != selected_armor]
        else:
            message = "The attack hit an unprotected area!" if is_player else f"The attack hit an unprotected area on {defender['name']}!"
            round_data["actions"].append({
                "actor": "system",
                "type": "armor_miss",
                "message": message
            })
            final_damage = initial_damage
    else:
        final_damage = initial_damage
        message = "You have no armor equipped!" if is_player else f"{defender['name']} has no armor equipped!"
        round_data["actions"].append({
            "actor": "system",
            "type": "no_armor",
            "message": message
        })

    absorbed_damage = initial_damage - final_damage
    return final_damage, absorbed_damage


def calculate_armor_effectiveness(armor: Dict, damage: int) -> int:
    base_protection = armor.get("protection", 0)
    max_durability = armor.get("max_durability", 100)
    current_durability = armor.get("durability", 0)
    efficiency = armor.get("efficiency", 100) / 100

    durability_factor = 0.5 + (0.5 * (current_durability / max_durability))
    damage_reduction = min(damage, base_protection)
    damage_reduction = int(round(damage_reduction * efficiency))
    effective_protection = int(round(damage_reduction * durability_factor))

    return effective_protection


def get_weapon_damage(attacker: Dict, exp_bonus_value: int) -> Dict:
    default_weapon = {
        "min_damage": 1,
        "max_damage": 2,
        "accuracy": 100,
        "crit_chance": 5,
        "crit_dmg_pct": 150
    }

    weapon = next((item for item in attacker.get("equipped", []) if item.get("slot") == "right_hand"),
                  default_weapon)

    min_damage = weapon.get("min_damage", default_weapon["min_damage"])
    max_damage = weapon.get("max_damage", default_weapon["max_damage"])
    accuracy = weapon.get("accuracy", default_weapon["accuracy"])
    crit_chance = weapon.get("crit_chance", default_weapon["crit_chance"])
    crit_dmg_pct = weapon.get("crit_dmg_pct", default_weapon["crit_dmg_pct"])

    damage = random.randint(min_damage, max_damage)

    if random.randint(1, 100) > accuracy:
        return {"damage": 0, "base_damage": 0, "exp_bonus": 0, "message": "miss"}

    if random.randint(1, 100) <= crit_chance:
        damage = int(damage * (crit_dmg_pct / 100))
        message = "critical hit"
    else:
        message = "hit"

    final_damage = damage + exp_bonus_value
    return {"damage": final_damage, "base_damage": damage, "exp_bonus": exp_bonus_value, "message": message}


def get_fight_preconditions(user_data: Dict) -> Optional[str]:
    if user_data["action_points"] < 1:
        return "Not enough action points to fight"
    if not user_data["alive"]:
        return "You are dead"
    return None


def process_player_defeat(defeated: Dict, defeated_name: str, victor: Dict, victor_name: str, death_chance: float,
                          usersdb: Dict, rounds: List[Dict], round_number: int, defeated_max_hp: int) -> None:
    print("victor", victor)
    print("defeated", defeated)
    is_player_defeated = defeated_name == victor["username"]

    if random.random() < death_chance:
        message = f"{'You were' if is_player_defeated else defeated_name + ' was'} killed in battle. {'Your' if is_player_defeated else defeated_name + 's'} HP: 0/{defeated_max_hp}"
        new_data = {"alive": False, "hp": 0, "action_points": 0}
    else:
        message = f"{'You' if is_player_defeated else defeated_name} barely managed to escape. {'Your' if is_player_defeated else defeated_name + 's'} HP: 1/{defeated_max_hp}"
        new_data = {"action_points": defeated["action_points"] - 1, "hp": 1}

    rounds.append({
        "round": round_number,
        "player_hp": victor["hp"] if victor_name == victor["username"] else defeated["hp"],
        "enemy_hp": defeated["hp"] if victor_name == victor["username"] else victor["hp"],
        "actions": [{
            "actor": "system",
            "type": "defeat",
            "message": message
        }]
    })

    # Add item drop mechanic
    if random.random() < 0.3:  # 30% chance to drop an item
        dropped_item, slot = drop_random_item(defeated)
        if dropped_item:
            if slot == "unequipped":
                victor["unequipped"].append(dropped_item)
            else:
                # If it's an equipped item, we need to handle it differently
                if not has_item_equipped(victor, dropped_item["type"]):
                    victor["equipped"].append(dropped_item)
                else:
                    victor["unequipped"].append(dropped_item)

            loot_message = f"{'You looted' if victor_name == victor['username'] else victor_name + ' looted'} a {dropped_item['type']} from {'your' if is_player_defeated else defeated_name + 's'} mutilated body!"
            rounds.append({
                "round": round_number,
                "player_hp": victor["hp"] if victor_name == victor["username"] else defeated["hp"],
                "enemy_hp": defeated["hp"] if victor_name == victor["username"] else victor["hp"],
                "actions": [{
                    "actor": "system",
                    "type": "loot",
                    "message": loot_message
                }]
            })
            update_user_data(victor_name, {"unequipped": victor["unequipped"], "equipped": victor["equipped"]},
                             usersdb)

    update_user_data(defeated_name, new_data, usersdb)