import random
from typing import Dict, List
from backend import update_user_data
from player import calculate_total_hp, has_item_equipped, drop_random_item
from combat_utils import exp_bonus, get_weapon_damage, apply_armor_protection

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
        player_attack(user_data, target_data, user, target_name, round_data, round_number, user_max_total_hp, target_max_total_hp)

        if target_data["hp"] <= 0:
            # Update round data with final HP values
            round_data["player_hp"] = user_data["hp"]
            round_data["enemy_hp"] = target_data["hp"]
            battle_data["rounds"].append(round_data)

            experience = user_data["exp"] + 10 + target_data["exp"] // 10
            update_user_data(user, {"exp": experience}, usersdb)
            process_player_defeat(target_data, target_name, user_data, user, 0.5, usersdb, battle_data["rounds"],
                                  round_number, target_max_total_hp)
            break

        # Target attacks player
        player_attack(target_data, user_data, target_name, user, round_data, round_number, target_max_total_hp, user_max_total_hp)

        if user_data["hp"] <= 0:
            # Update round data with final HP values
            round_data["player_hp"] = user_data["hp"]
            round_data["enemy_hp"] = target_data["hp"]
            battle_data["rounds"].append(round_data)

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

def player_attack(attacker: Dict, defender: Dict, attacker_name: str, defender_name: str, round_data: Dict,
                  round_number: int, attacker_max_hp: int, defender_max_hp: int) -> None:
    if attacker["hp"] <= 0:
        return

    # Attempt spell cast
    spell_cast = attempt_spell_cast(attacker, spell_types)
    if spell_cast:
        final_damage = spell_cast['damage']
        defender["hp"] = max(0, defender["hp"] - final_damage)
        message = f"{attacker_name} cast {spell_cast['name']} on {defender_name} for {final_damage} damage. " \
                  f"{attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}, Mana: {attacker['mana']}. " \
                  f"{defender_name}'s HP: {defender['hp']}/{defender_max_hp}"
        round_data["actions"].append({
            "actor": "player" if attacker_name == attacker.get('username') else "enemy",
            "type": "spell",
            "damage": final_damage,
            "message": message
        })
    else:
        exp_bonus_value = exp_bonus(attacker["exp"])
        damage_dict = get_weapon_damage(attacker, exp_bonus_value)

        final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], round_data, round_number)

        defender["hp"] = max(0, defender["hp"] - final_damage)  # Ensure HP doesn't go below 0

        message = (f"{attacker_name} {damage_dict['message']} {defender_name} for {final_damage} damage "
                   f"(Base: {damage_dict['base_damage']}, Exp bonus: {damage_dict['exp_bonus']}). "
                   f"{attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}, {defender_name}'s HP: {defender['hp']}/{defender_max_hp}")

        round_data["actions"].append({
            "actor": "player" if attacker_name == attacker.get('username') else "enemy",
            "type": "attack",
            "damage": final_damage,
            "message": message
        })

def process_player_defeat(defeated: Dict, defeated_name: str, victor: Dict, victor_name: str, death_chance: float,
                          usersdb: Dict, rounds: List[Dict], round_number: int, defeated_max_hp: int) -> None:
    print("victor", victor)
    print("defeated", defeated)

    if random.random() < death_chance:
        message = f"{defeated_name} was killed in battle. {defeated_name}'s HP: 0/{defeated_max_hp}"
        new_data = {"alive": False, "hp": 0, "action_points": 0}

        # Item drop mechanic - only happens when player dies
        if random.random() < 0.3:  # 30% chance to drop an item
            dropped_item, slot = drop_random_item(defeated)
            if dropped_item:
                # Remove the item from the defeated player's inventory
                if slot == "unequipped":
                    defeated["unequipped"] = [item for item in defeated["unequipped"] if item["id"] != dropped_item["id"]]
                else:
                    defeated["equipped"] = [item for item in defeated["equipped"] if item["id"] != dropped_item["id"]]

                # Add the item to the victor's inventory
                if slot == "unequipped" or has_item_equipped(victor, dropped_item["type"]):
                    victor["unequipped"].append(dropped_item)
                else:
                    victor["equipped"].append(dropped_item)

                loot_message = f"{victor_name} looted a {dropped_item['type']} from {defeated_name}'s mutilated body!"
                rounds.append({
                    "round": round_number,
                    "player_hp": victor["hp"] if victor_name == victor.get("username") else defeated["hp"],
                    "enemy_hp": defeated["hp"] if victor_name == victor.get("username") else victor["hp"],
                    "actions": [{
                        "actor": "system",
                        "type": "loot",
                        "message": loot_message
                    }]
                })

                # Update victor's data in the database
                update_user_data(victor_name, {
                    "unequipped": victor["unequipped"],
                    "equipped": victor["equipped"]
                }, usersdb)

                # Update the new_data dictionary for the defeated player
                new_data["unequipped"] = defeated["unequipped"]
                new_data["equipped"] = defeated["equipped"]
    else:
        message = f"{defeated_name} barely managed to escape. {defeated_name}'s HP: 1/{defeated_max_hp}"
        new_data = {"action_points": defeated["action_points"] - 1, "hp": 1}

    rounds.append({
        "round": round_number,
        "player_hp": victor["hp"] if victor_name == victor.get("username") else defeated["hp"],
        "enemy_hp": defeated["hp"] if victor_name == victor.get("username") else victor["hp"],
        "actions": [{
            "actor": "system",
            "type": "defeat",
            "message": message
        }]
    })

    # Update defeated player's data
    update_user_data(defeated_name, new_data, usersdb)