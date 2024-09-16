import random
from typing import Dict, Any
from map import remove_from_map
from backend import update_user_data
from item_generator import generate_weapon, generate_armor
from enemies import Enemy, enemy_types
from combat_utils import exp_bonus, get_weapon_damage, apply_armor_protection, death_roll, attempt_spell_cast
from player import calculate_total_hp
from spells import spell_types


def fight_npc(battle_data: Dict, npc_data: Dict[str, Any], coords: str, user_data: Dict, user: str, usersdb: Dict,
              mapdb: Dict) -> None:
    damage_dealt = 0

    enemy_class = enemy_types.get(npc_data['type'].lower())
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
            # Attempt spell cast
            spell_cast = attempt_spell_cast(user_data, spell_types)
            if spell_cast:
                damage_dealt = spell_cast['damage']
                user_data['mana'] -= spell_cast['mana_cost']  # Deduct mana cost
                update_user_data(user=user, updated_values={"mana": user_data["mana"]}, user_data_dict=usersdb)  # Update mana in database
                enemy.hp = max(0, enemy.hp - damage_dealt)
                round_data["actions"].append({
                    "actor": "player",
                    "type": "spell",
                    "damage": damage_dealt,
                    "message": f"You cast {spell_cast['name']} on the level {enemy.level} {enemy.type} for {damage_dealt} damage. Enemy HP: {enemy.hp}/{enemy.max_hp}. Your mana: {user_data['mana']}"
                })
            else:
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
                update_user_data(user=user, updated_values={"alive": False, "hp": 0, "mana": user_data["mana"]}, user_data_dict=usersdb)
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
                update_user_data(user=user, updated_values={"action_points": user_data["action_points"] - 1, "hp": 1, "mana": user_data["mana"]},
                                 user_data_dict=usersdb)
            break

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