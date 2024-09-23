import random
from typing import Dict, Any
from map import remove_from_map
from backend import update_user_data
from item_generator import generate_weapon, generate_armor
from enemies import Enemy, enemy_types
from combat_utils import get_weapon_damage, apply_spell_effect, apply_armor_protection, death_roll, attempt_spell_cast
from player import calculate_total_hp
from spells import spell_types
from collections import deque


def fight_npc(battle_data: Dict, npc_data: Dict[str, Any], coords: str, user_data: Dict, user: str, usersdb: Dict,
              mapdb: Dict) -> None:
    enemy_class = enemy_types.get(npc_data['type'].lower())
    if enemy_class is None:
        battle_data["rounds"].append({"round": 0, "message": f"Unknown enemy type: {npc_data['type']}"})
        return

    enemy = enemy_class(npc_data['level'])
    if hasattr(enemy, 'spells') and enemy.spells:
        enemy.spell_queue = deque(enemy.spells)

    max_base_hp = 100
    max_total_hp = calculate_total_hp(max_base_hp, user_data["exp"])

    # Initialize battle data with correct HP values
    battle_data["player"].update({
        "name": user,
        "max_hp": max_total_hp,
        "current_hp": user_data["hp"]
    })

    battle_data["enemy"].update({
        "name": enemy.type,
        "max_hp": enemy.max_hp,
        "current_hp": enemy.hp,
        "level": enemy.level
    })

    # Add initial round data
    initial_round = {
        "round": 0,
        "message": f"Battle starts! {user} (HP: {user_data['hp']}/{max_total_hp}) vs Level {enemy.level} {enemy.type} (HP: {enemy.hp}/{enemy.max_hp})",
        "player_hp": user_data["hp"],
        "enemy_hp": enemy.hp,
        "actions": []
    }
    battle_data["rounds"].append(initial_round)

    round_number = 0
    while enemy.hp > 0 and user_data["alive"]:
        round_number += 1
        round_data = {"round": round_number, "actions": []}

        if user_data["hp"] > 0:
            # Player's turn
            handle_player_turn(user_data, user, enemy, round_data, usersdb, max_total_hp)

        if enemy.hp > 0:
            # Enemy's turn
            handle_enemy_turn(user_data, enemy, round_data, round_number, max_total_hp)

        round_data["player_hp"] = user_data["hp"]
        round_data["enemy_hp"] = enemy.hp
        battle_data["rounds"].append(round_data)

        if enemy.hp <= 0:
            defeat_round = process_npc_defeat(enemy, coords, user_data, user, usersdb, mapdb, battle_data, round_number)
            battle_data["rounds"].append(defeat_round)
            break

        if user_data["hp"] <= 0:
            handle_player_defeat(user_data, user, enemy, usersdb, battle_data, round_number, max_total_hp)
            break

    # Update final battle stats
    battle_data["player"]["current_hp"] = user_data["hp"]
    battle_data["enemy"]["current_hp"] = enemy.hp

def handle_player_turn(user_data: Dict, user: str, enemy: Any, round_data: Dict, usersdb: Dict,
                       max_total_hp: int) -> int:
    damage_dealt = 0
    initial_player_hp = user_data["hp"]
    initial_enemy_hp = enemy.hp
    spell_cast = attempt_spell_cast(user_data, spell_types)
    if spell_cast:
        damage_dealt = handle_spell_cast(user_data, user, enemy, spell_cast, round_data, usersdb, max_total_hp)
    else:
        damage_dealt = handle_weapon_attack(user_data, enemy, round_data, max_total_hp)

    enemy.hp = max(0, enemy.hp - damage_dealt)  # Update enemy HP here

    round_data["actions"][-1].update({
        "final_player_hp": user_data["hp"],
        "final_enemy_hp": enemy.hp,
        "initial_player_hp": initial_player_hp,
        "initial_enemy_hp": initial_enemy_hp
    })
    return damage_dealt


def handle_spell_cast(user_data: Dict, user: str, enemy: Any, spell_cast: Dict, round_data: Dict, usersdb: Dict,
                      max_total_hp: int) -> int:
    initial_enemy_hp = enemy.hp
    spell_effect = apply_spell_effect(spell_cast, user_data, enemy.__dict__)

    initial_mana = user_data['mana']
    initial_hp = user_data['hp']

    user_data['mana'] = max(0, user_data['mana'] - spell_cast['mana_cost'])

    damage_dealt = 0
    healing_done = 0

    if 'healing_done' in spell_effect:
        healing_done = spell_effect['healing_done']
        user_data['hp'] = min(max_total_hp, user_data['hp'] + healing_done)
    elif 'damage_info' in spell_effect:
        damage_info = spell_effect['damage_info']
        base_damage = damage_info['base_damage']
        magic_bonus = damage_info['magic_bonus']
        total_calculated_damage = damage_info['damage']

        # Apply the damage
        enemy.hp = max(0, enemy.hp - total_calculated_damage)

        # Calculate the actual damage dealt
        actual_damage_dealt = initial_enemy_hp - enemy.hp

        message = f"You cast {spell_cast['name']}. "
        message += f"{spell_cast['name']} hits the target for {base_damage} damage! "
        message += f"You dealt {actual_damage_dealt} damage to the enemy. "
        message += f"(Base: {base_damage}, Magic bonus: {magic_bonus}, "
        message += f"Calculated total: {total_calculated_damage}, Actual: {actual_damage_dealt}) "
        message += f"Enemy {enemy.type} HP: {enemy.hp}/{enemy.max_hp}. "
        message += f"Your HP: {user_data['hp']}/{max_total_hp}. "
        message += f"Your mana: {user_data['mana']} (-{initial_mana - user_data['mana']})."

        damage_dealt = actual_damage_dealt
    else:
        message = f"You cast {spell_cast['name']}, but it had no effect."

    round_data["actions"].append({
        "actor": "player",
        "type": "spell",
        "spell_name": spell_cast['name'],
        "effect": spell_effect,
        "damage_dealt": damage_dealt,
        "healing_done": healing_done,
        "mana_used": initial_mana - user_data['mana'],
        "hp_change": user_data['hp'] - initial_hp,
        "enemy_hp_change": initial_enemy_hp - enemy.hp,
        "message": message
    })

    update_user_data(user=user, updated_values={"mana": user_data["mana"], "hp": user_data["hp"]},
                     user_data_dict=usersdb)

    return damage_dealt

def handle_weapon_attack(user_data: Dict, enemy: Any, round_data: Dict, max_total_hp: int) -> int:
    user_dmg = get_weapon_damage(user_data)

    if user_dmg['damage'] > 0:
        return process_hit(user_data, enemy, user_dmg, round_data, max_total_hp)
    else:
        return process_miss(user_data, enemy, round_data)

def process_hit(user_data: Dict, enemy: Any, user_dmg: Dict, round_data: Dict, max_total_hp: int) -> int:
    if enemy.attempt_evasion():
        round_data["actions"].append({
            "actor": "enemy",
            "type": "evasion",
            "message": f"The level {enemy.level} {enemy.type} evaded your attack."
        })
        return 0
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

    round_data["actions"].append({
        "actor": "player",
        "type": "attack",
        "damage": damage_dealt,
        "message": f"You {user_dmg['message']} the level {enemy.level} {enemy.type} for {damage_dealt} damage "
                   f"(Base: {user_dmg['base_damage']}, Martial bonus: {user_dmg['martial_bonus']}). "
                   f"Enemy HP: {enemy.hp}/{enemy.max_hp}. Your HP: {user_data['hp']}/{max_total_hp}"
    })
    return damage_dealt

def process_miss(user_data: Dict, enemy: Any, round_data: Dict) -> int:
    weapon = next((item for item in user_data.get("equipped", []) if item.get("slot") == "right_hand"), None)
    if weapon:
        message = f"Your attack with {weapon['type']} missed the {enemy.type}."
    else:
        message = f"Your unarmed attack missed the {enemy.type}."

    round_data["actions"].append({
        "actor": "player",
        "type": "miss",
        "damage": 0,
        "message": message
    })
    return 0

def handle_enemy_turn(user_data: Dict, enemy: Any, round_data: Dict, round_number: int, max_total_hp: int) -> None:
    npc_dmg = enemy.roll_damage()
    initial_player_hp = user_data["hp"]
    initial_enemy_hp = enemy.hp
    final_damage, absorbed_damage = apply_armor_protection(user_data, npc_dmg["damage"], round_data, round_number)
    user_data["hp"] = max(0, user_data["hp"] - final_damage)  # Ensure HP doesn't go below 0
    round_data["actions"].append({
        "actor": "enemy",
        "type": "attack",
        "damage": final_damage,
        "initial_player_hp": initial_player_hp,
        "final_player_hp": user_data["hp"],
        "initial_enemy_hp": initial_enemy_hp,
        "final_enemy_hp": enemy.hp,
        "message": f"The level {enemy.level} {enemy.type} {npc_dmg['message']} you for {final_damage} damage. Your HP: {user_data['hp']}/{max_total_hp}"
    })


def handle_player_defeat(user_data: Dict, user: str, enemy: Any, usersdb: Dict, battle_data: Dict, round_number: int,
                         max_total_hp: int) -> None:
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
        user_data["deaths"] = user_data.get("deaths", 0) + 1
        update_user_data(user=user, updated_values={"alive": False, "hp": 0, "mana": user_data["mana"], "deaths": user_data["deaths"]},
                         user_data_dict=usersdb)
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
        update_user_data(user=user, updated_values={"action_points": user_data["action_points"] - 1, "hp": 1,
                                                    "mana": user_data["mana"]},
                         user_data_dict=usersdb)

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