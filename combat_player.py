import random
from typing import Dict, List
from backend import update_user_data
from player import calculate_total_hp, calculate_total_mana, has_item_equipped, drop_random_item
from combat_utils import get_weapon_damage, apply_spell_effect, apply_armor_protection, attempt_spell_cast, death_roll
from spells import spell_types
from collections import deque

def fight_player(battle_data: Dict, target_data: Dict, target_name: str, user_data: Dict, user: str, usersdb: Dict) -> None:
    max_base_hp = 100
    max_base_mana = 100
    user_max_total_hp = calculate_total_hp(max_base_hp, user_data["exp"])
    user_max_total_mana = calculate_total_mana(max_base_mana, user_data["exp"])
    target_max_total_hp = calculate_total_hp(max_base_hp, target_data["exp"])
    target_max_total_mana = calculate_total_mana(max_base_mana, target_data["exp"])

    for player_data in [user_data, target_data]:
        if 'spells' in player_data and player_data['spells']:
            player_data['spell_queue'] = deque(player_data['spells'])

    battle_data["player"].update({
        "name": user,
        "max_hp": user_max_total_hp,
        "current_hp": user_data["hp"],
        "max_mana": user_max_total_mana,
        "current_mana": user_data["mana"]
    })

    battle_data["enemy"].update({
        "name": target_name,
        "max_hp": target_max_total_hp,
        "current_hp": target_data["hp"],
        "max_mana": target_max_total_mana,
        "current_mana": target_data["mana"]
    })

    battle_data["rounds"].append({
        "round": 0,
        "player_hp": user_data["hp"],
        "player_mana": user_data["mana"],
        "enemy_hp": target_data["hp"],
        "enemy_mana": target_data["mana"],
        "message": f"You challenged {target_name}. Your HP: {user_data['hp']}/{user_max_total_hp}, Mana: {user_data['mana']}/{user_max_total_mana}. {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}, Mana: {target_data['mana']}/{target_max_total_mana}",
        "actions": []
    })

    round_number = 0
    while target_data["hp"] > 0 and user_data["hp"] > 0:
        round_number += 1
        round_data = {"round": round_number, "actions": []}

        # Player attacks target
        attacker_action(user_data, target_data, user, target_name, round_data, round_number, user_max_total_hp, target_max_total_hp, user_max_total_mana, target_max_total_mana)

        if target_data["hp"] <= 0:
            round_data["player_hp"] = user_data["hp"]
            round_data["player_mana"] = user_data["mana"]
            round_data["enemy_hp"] = target_data["hp"]
            round_data["enemy_mana"] = target_data["mana"]
            battle_data["rounds"].append(round_data)

            experience = user_data["exp"] + 10 + target_data["exp"] // 10
            update_user_data(user, {"exp": experience}, usersdb)
            process_player_defeat(target_data, target_name, user_data, user, 0.5, usersdb, battle_data["rounds"],
                                  round_number, target_max_total_hp)
            break

        # Target attacks player
        defender_action(target_data, user_data, target_name, user, round_data, round_number, target_max_total_hp, user_max_total_hp, target_max_total_mana, user_max_total_mana)

        if user_data["hp"] <= 0:
            round_data["player_hp"] = user_data["hp"]
            round_data["player_mana"] = user_data["mana"]
            round_data["enemy_hp"] = target_data["hp"]
            round_data["enemy_mana"] = target_data["mana"]
            battle_data["rounds"].append(round_data)

            experience = target_data["exp"] + 10 + user_data["exp"] // 10
            update_user_data(target_name, {"exp": experience}, usersdb)
            process_player_defeat(user_data, user, target_data, target_name, 0.5, usersdb, battle_data["rounds"],
                                  round_number, user_max_total_hp)
            break

        round_data["player_hp"] = user_data["hp"]
        round_data["player_mana"] = user_data["mana"]
        round_data["enemy_hp"] = target_data["hp"]
        round_data["enemy_mana"] = target_data["mana"]
        round_data["actions"].append({
            "actor": "system",
            "type": "round_end",
            "message": f"Round {round_number} complete. Your HP: {user_data['hp']}/{user_max_total_hp}, Mana: {user_data['mana']}/{user_max_total_mana}. {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}, Mana: {target_data['mana']}/{target_max_total_mana}"
        })
        battle_data["rounds"].append(round_data)

        if 0 < target_data["hp"] < 10:
            battle_data["rounds"].append({
                "round": round_number + 1,
                "player_hp": user_data["hp"],
                "player_mana": user_data["mana"],
                "enemy_hp": target_data["hp"],
                "enemy_mana": target_data["mana"],
                "message": f"{target_name} has fled seeing they stand no chance against you! Your HP: {user_data['hp']}/{user_max_total_hp}, Mana: {user_data['mana']}/{user_max_total_mana}. {target_name}'s HP: {target_data['hp']}/{target_max_total_hp}, Mana: {target_data['mana']}/{target_max_total_mana}",
                "actions": []
            })
            break

    # Update final battle stats
    battle_data["player"]["current_hp"] = user_data["hp"]
    battle_data["player"]["current_mana"] = user_data["mana"]
    battle_data["enemy"]["current_hp"] = target_data["hp"]
    battle_data["enemy"]["current_mana"] = target_data["mana"]

    print(f"Fight ended. Rounds: {len(battle_data['rounds'])}, Player HP: {user_data['hp']}, Player Mana: {user_data['mana']}, Enemy HP: {target_data['hp']}, Enemy Mana: {target_data['mana']}")


def process_player_defeat(defeated: Dict, defeated_name: str, victor: Dict, victor_name: str, death_chance: float,
                          usersdb: Dict, rounds: List[Dict], round_number: int, defeated_max_hp: int) -> None:
    if death_roll(death_chance):
        message = f"{defeated_name} was killed in battle. {defeated_name}'s HP: 0/{defeated_max_hp}"
        new_data = {"alive": False, "hp": 0, "action_points": 0, "deaths": defeated.get("deaths", 0) + 1}

        # Update victor's homicides
        victor["homicides"] = victor.get("homicides", 0) + 1
        update_user_data(victor_name, {"homicides": victor["homicides"]}, usersdb)

        # Item drop mechanic - only happens when player dies
        if random.random() < 0.3:  # 30% chance to drop an item
            dropped_item, slot = drop_random_item(defeated)
            if dropped_item:
                # Remove the item from the defeated player's inventory
                if slot == "unequipped":
                    defeated["unequipped"] = [item for item in defeated["unequipped"] if
                                              item["id"] != dropped_item["id"]]
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

def attacker_action(attacker: Dict, defender: Dict, attacker_name: str, defender_name: str, round_data: Dict,
                    round_number: int, attacker_max_hp: int, defender_max_hp: int, attacker_max_mana: int, defender_max_mana: int) -> None:
    if attacker["hp"] <= 0:
        return

    initial_attacker_hp = attacker["hp"]
    initial_attacker_mana = attacker["mana"]
    initial_defender_hp = defender["hp"]
    initial_defender_mana = defender["mana"]

    # Attempt spell cast
    spell_cast = attempt_spell_cast(attacker, spell_types)
    if spell_cast:
        spell_effect = apply_spell_effect(spell_cast, attacker, defender)

        damage_dealt = spell_effect.get('damage_dealt', 0)
        healing_done = spell_effect.get('healing_done', 0)

        defender["hp"] = max(0, defender["hp"] - damage_dealt)
        attacker["hp"] = min(attacker_max_hp, attacker["hp"] + healing_done)

        message = f"{attacker_name} cast {spell_cast['name']}. {spell_effect['message']} "
        message += f"{attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}, Mana: {attacker['mana']}/{attacker_max_mana}. "
        message += f"{defender_name}'s HP: {defender['hp']}/{defender_max_hp}, Mana: {defender['mana']}/{defender_max_mana}"

        round_data["actions"].append({
            "actor": "player",
            "type": "spell",
            "spell_name": spell_cast['name'],
            "effect": spell_effect,
            "damage_dealt": damage_dealt,
            "healing_done": healing_done,
            "mana_used": spell_cast['mana_cost'],
            "hp_change": attacker["hp"] - initial_attacker_hp,
            "mana_change": attacker["mana"] - initial_attacker_mana,
            "enemy_hp_change": initial_defender_hp - defender["hp"],
            "enemy_mana_change": initial_defender_mana - defender["mana"],
            "message": message,
            "final_player_hp": attacker["hp"],
            "final_player_mana": attacker["mana"],
            "final_enemy_hp": defender["hp"],
            "final_enemy_mana": defender["mana"],
            "initial_player_hp": initial_attacker_hp,
            "initial_player_mana": initial_attacker_mana,
            "initial_enemy_hp": initial_defender_hp,
            "initial_enemy_mana": initial_defender_mana
        })
    else:
        damage_dict = get_weapon_damage(attacker)

        final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], round_data, round_number)

        defender["hp"] = max(0, defender["hp"] - final_damage)  # Ensure HP doesn't go below 0

        message = (f"{attacker_name} {damage_dict['message']} {defender_name} for {final_damage} damage "
                   f"(Base: {damage_dict['base_damage']}, Martial bonus: {damage_dict['martial_bonus']}). "
                   f"{attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}, Mana: {attacker['mana']}/{attacker_max_mana}. "
                   f"{defender_name}'s HP: {defender['hp']}/{defender_max_hp}, Mana: {defender['mana']}/{defender_max_mana}")

        round_data["actions"].append({
            "actor": "player",
            "type": "attack",
            "damage": final_damage,
            "message": message,
            "final_player_hp": attacker["hp"],
            "final_player_mana": attacker["mana"],
            "final_enemy_hp": defender["hp"],
            "final_enemy_mana": defender["mana"],
            "initial_player_hp": initial_attacker_hp,
            "initial_player_mana": initial_attacker_mana,
            "initial_enemy_hp": initial_defender_hp,
            "initial_enemy_mana": initial_defender_mana
        })

def defender_action(attacker: Dict, defender: Dict, attacker_name: str, defender_name: str, round_data: Dict,
                    round_number: int, attacker_max_hp: int, defender_max_hp: int, attacker_max_mana: int, defender_max_mana: int) -> None:
    if attacker["hp"] <= 0:
        return

    initial_attacker_hp = attacker["hp"]
    initial_attacker_mana = attacker["mana"]
    initial_defender_hp = defender["hp"]
    initial_defender_mana = defender["mana"]

    # Attempt spell cast
    spell_cast = attempt_spell_cast(attacker, spell_types)
    if spell_cast:
        spell_effect = apply_spell_effect(spell_cast, attacker, defender)

        damage_dealt = spell_effect.get('damage_dealt', 0)
        healing_done = spell_effect.get('healing_done', 0)

        defender["hp"] = max(0, defender["hp"] - damage_dealt)
        attacker["hp"] = min(attacker_max_hp, attacker["hp"] + healing_done)

        message = f"{attacker_name} cast {spell_cast['name']}. {spell_effect['message']} "
        message += f"{attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}, Mana: {attacker['mana']}/{attacker_max_mana}. "
        message += f"{defender_name}'s HP: {defender['hp']}/{defender_max_hp}, Mana: {defender['mana']}/{defender_max_mana}"

        round_data["actions"].append({
            "actor": "enemy",
            "type": "spell",
            "spell_name": spell_cast['name'],
            "effect": spell_effect,
            "damage_dealt": damage_dealt,
            "healing_done": healing_done,
            "mana_used": spell_cast['mana_cost'],
            "hp_change": attacker["hp"] - initial_attacker_hp,
            "mana_change": attacker["mana"] - initial_attacker_mana,
            "enemy_hp_change": initial_defender_hp - defender["hp"],
            "enemy_mana_change": initial_defender_mana - defender["mana"],
            "message": message,
            "final_player_hp": defender["hp"],
            "final_player_mana": defender["mana"],
            "final_enemy_hp": attacker["hp"],
            "final_enemy_mana": attacker["mana"],
            "initial_player_hp": initial_defender_hp,
            "initial_player_mana": initial_defender_mana,
            "initial_enemy_hp": initial_attacker_hp,
            "initial_enemy_mana": initial_attacker_mana
        })
    else:
        damage_dict = get_weapon_damage(attacker)

        final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], round_data, round_number)

        defender["hp"] = max(0, defender["hp"] - final_damage)  # Ensure HP doesn't go below 0

        message = (f"{attacker_name} {damage_dict['message']} {defender_name} for {final_damage} damage "
                   f"(Base: {damage_dict['base_damage']}, Martial bonus: {damage_dict['martial_bonus']}). "
                   f"{attacker_name}'s HP: {attacker['hp']}/{attacker_max_hp}, Mana: {attacker['mana']}/{attacker_max_mana}. "
                   f"{defender_name}'s HP: {defender['hp']}/{defender_max_hp}, Mana: {defender['mana']}/{defender_max_mana}")

        round_data["actions"].append({
            "actor": "enemy",
            "type": "attack",
            "damage": final_damage,
            "message": message,
            "final_player_hp": defender["hp"],
            "final_player_mana": defender["mana"],
            "final_enemy_hp": attacker["hp"],
            "final_enemy_mana": attacker["mana"],
            "initial_player_hp": initial_defender_hp,
            "initial_player_mana": initial_defender_mana,
            "initial_enemy_hp": initial_attacker_hp,
            "initial_enemy_mana": initial_attacker_mana
        })