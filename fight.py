import math
import random
from typing import Dict, List, Tuple, Optional

from backend import update_user_data, get_values
from map import remove_from_map, get_coords
import entities
from weapon_generator import generate_weapon, generate_armor

def get_entity_class(target: str) -> Optional[type]:
    """
    Get the entity class based on the target string.
    Handles case sensitivity, multi-word entity names, and type-class name mismatches.
    """
    # Convert target to a normalized form (remove underscores and lowercase)
    normalized_target = target.replace('_', '').lower()

    # Try to find a matching class
    for name in dir(entities):
        if name.lower() == normalized_target:
            return getattr(entities, name)

    # If not found, try matching by removing common words and checking for partial matches
    words_to_remove = ['whelp', 'monster', 'creature', 'enemy']
    simplified_target = ''.join(word for word in normalized_target.split() if word not in words_to_remove)

    for name in dir(entities):
        if simplified_target in name.lower():
            return getattr(entities, name)

    print(f"No matching entity class found for '{target}'")
    return None

def calculate_armor_effectiveness(armor: Dict) -> float:
    base_protection = armor.get("protection", 0)
    max_durability = armor.get("max_durability", 100)
    current_durability = armor.get("durability", 0)
    efficiency = armor.get("efficiency", 100) / 100

    # Calculate durability factor (ranges from 0.5 to 1)
    durability_factor = 0.5 + (0.5 * (current_durability / max_durability))

    # Calculate efficiency factor (ranges from 0.8 to 1.2)
    efficiency_factor = 0.8 + (0.4 * efficiency)

    # Calculate effective protection
    effective_protection = base_protection * durability_factor * efficiency_factor

    return effective_protection


def apply_armor_protection(defender: Dict, initial_damage: int, rounds: List[Dict], round_number: int) -> Tuple[
    int, int]:
    print(f"Applying armor protection. Initial damage: {initial_damage}")
    armor_protection = 0
    is_player = defender.get('name', 'You') == 'You'

    all_armor_slots = [armor for armor in defender.get("equipped", []) if armor.get("role") == "armor"]

    if all_armor_slots:
        selected_armor = random.choice(all_armor_slots)
        print(f"Selected armor: {selected_armor}")

        if selected_armor.get("type") != "empty":
            effective_protection = calculate_armor_effectiveness(selected_armor)
            armor_protection = min(initial_damage, effective_protection)  # Can't absorb more than the initial damage

            # Calculate damage reduction percentage
            damage_reduction_percentage = (armor_protection / initial_damage) * 100

            armor_info = (
                f"Your {selected_armor['type']}" if is_player else f"{defender['name']}'s {selected_armor['type']}"
            )

            # Update the round information
            rounds.append({
                "round": round_number,
                "player_hp": defender["hp"],
                "enemy_hp": defender["hp"],
                "message": (
                    f"{armor_info} (Base Protection: {selected_armor['protection']}, "
                    f"Efficiency: {selected_armor['efficiency']}%, "
                    f"Durability: {selected_armor['durability']}/{selected_armor['max_durability']}) "
                    f"reduced damage by {damage_reduction_percentage:.1f}% ({armor_protection:.1f} points)."
                )
            })

            # Apply durability loss
            durability_loss = math.ceil(initial_damage / 10)  # Lose 1 durability per 10 damage points
            old_durability = selected_armor["durability"]
            selected_armor["durability"] = max(0, selected_armor["durability"] - durability_loss)

            rounds.append({
                "round": round_number,
                "player_hp": defender["hp"],
                "enemy_hp": defender["hp"],
                "message": f"{armor_info} durability reduced from {old_durability} to {selected_armor['durability']}."
            })

            if selected_armor["durability"] <= 0:
                message = (
                    f"Your {selected_armor['type']} has broken and no longer provides protection!"
                    if is_player else
                    f"{defender['name']}'s {selected_armor['type']} has broken and no longer provides protection!"
                )
                rounds.append({
                    "round": round_number,
                    "player_hp": defender["hp"],
                    "enemy_hp": defender["hp"],
                    "message": message
                })
                selected_armor["type"] = "empty"
                selected_armor["protection"] = 0
        else:
            message = (
                "The attack hit an unprotected area!" if is_player else
                f"The attack hit an unprotected area on {defender['name']}!"
            )
            rounds.append({
                "round": round_number,
                "player_hp": defender["hp"],
                "enemy_hp": defender["hp"],
                "message": message
            })

    final_damage = math.floor(max(1, initial_damage - armor_protection))
    absorbed_damage = initial_damage - final_damage
    print(f"Final damage: {final_damage}, Absorbed damage: {absorbed_damage}")

    if absorbed_damage > 0:
        message = (
            f"Your armor absorbed {absorbed_damage:.1f} damage" if is_player else
            f"{defender['name']}'s armor absorbed {absorbed_damage:.1f} damage"
        )
        rounds.append({
            "round": round_number,
            "player_hp": defender["hp"],
            "enemy_hp": defender["hp"],
            "message": message
        })

    return final_damage, absorbed_damage

def get_weapon_damage(attacker: Dict, exp_bonus_value: int) -> Dict:
    print(f"Getting weapon damage for attacker. Exp bonus: {exp_bonus_value}")
    for weapon in attacker.get("equipped", {}):
        if weapon.get("role") == "right_hand":
            min_dmg = weapon.get("min_damage", 1)
            max_dmg = weapon.get("max_damage", 1)
            damage_dict = get_damage(min_dmg, max_dmg, weapon, exp_bonus=exp_bonus(value=exp_bonus_value))
            print(f"Weapon damage: {damage_dict}")
            return damage_dict
    print("No weapon found, returning default damage")
    return {"damage": 1, "message": "hit"}  # Default damage if no weapon found

def fight(target: str, target_name: str, on_tile_map: List[Dict], on_tile_users: List[Dict], user_data: Dict, user: str,
          usersdb: Dict, mapdb: Dict) -> Dict:
    print(f"Starting fight. Target: {target}, Target name: {target_name}")
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": target, "max_hp": 0, "current_hp": 0},
        "rounds": []
    }

    entity_class = get_entity_class(target)

    if entity_class:
        print(f"Found entity class: {entity_class.__name__}")
    else:
        print(f"No valid entity class found for: {target}")
        battle_data["rounds"].append({"round": 0, "message": f"No valid target found: {target}"})
        return {"battle_data": battle_data}

    for entry in on_tile_map:
        entry_type = get_values(entry).get("type")
        print(f"Processing map entry. Type: {entry_type}")

        if issubclass(entity_class, entities.Enemy):
            print(f"Fighting NPC: {target}")
            enemy = entity_class()
            battle_data["enemy"]["max_hp"] = enemy.hp
            battle_data["enemy"]["current_hp"] = enemy.hp
            fight_result = fight_npc(entry, user_data, user, usersdb, mapdb, enemy)
            battle_data.update(fight_result["battle_data"])
        elif target == "player" and entry_type == "player":
            print(f"Fighting player: {target_name}")
            fight_result = fight_player(entry, target_name, user_data, user, usersdb)
            battle_data.update(fight_result["battle_data"])

    for entry in on_tile_users:
        entry_type = get_values(entry).get("type")
        entry_name = get_coords(entry)
        print(f"Processing user entry. Type: {entry_type}, Name: {entry_name}")

        if target == "player" and entry_type == "player" and target_name == entry_name:
            print(f"Fighting player: {target_name}")
            fight_result = fight_player(entry, target_name, user_data, user, usersdb)
            battle_data.update(fight_result["battle_data"])

    if not battle_data["rounds"]:
        print(f"No valid target found for: {target}")
        battle_data["rounds"].append({"round": 0, "message": f"No valid target found: {target}"})

    return {"battle_data": battle_data}


def fight_npc(entry: Dict, user_data: Dict, user: str, usersdb: Dict, mapdb: Dict, npc: entities.Enemy) -> Dict:
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": npc.type, "max_hp": npc.hp, "current_hp": npc.hp},
        "rounds": []
    }

    round_number = 0
    while npc.alive and user_data["alive"]:
        round_number += 1

        if npc.hp < 1:
            process_npc_defeat(npc, user_data, user, usersdb, mapdb, entry, battle_data, round_number)
            break

        if user_data["hp"] < 1:
            if death_roll(npc.kill_chance):
                battle_data["rounds"].append({
                    "round": round_number,
                    "player_hp": 0,
                    "enemy_hp": npc.hp,
                    "message": "You died"
                })
                user_data["alive"] = False
                update_user_data(user=user, updated_values={"alive": False, "hp": 0}, user_data_dict=usersdb)
            else:
                battle_data["rounds"].append({
                    "round": round_number,
                    "player_hp": 1,
                    "enemy_hp": npc.hp,
                    "message": "You are almost dead but managed to escape"
                })
                update_user_data(user=user, updated_values={"action_points": user_data["action_points"] - 1, "hp": 1},
                                 user_data_dict=usersdb)
            break

        # Player attacks NPC
        user_dmg = get_weapon_damage(user_data, user_data["exp"])
        npc.hp -= user_dmg['damage']
        battle_data["enemy"]["current_hp"] = npc.hp
        battle_data["rounds"].append({
            "round": round_number,
            "player_hp": user_data["hp"],
            "enemy_hp": npc.hp,
            "message": f"You {user_dmg['message']} the {npc.type} for {user_dmg['damage']} damage. It has {npc.hp} HP left"
        })

        # NPC attacks player
        if npc.hp > 0:
            npc_dmg = npc.roll_damage()
            final_damage, absorbed_damage = apply_armor_protection(user_data, npc_dmg["damage"], battle_data["rounds"], round_number)
            user_data["hp"] -= final_damage
            battle_data["player"]["current_hp"] = user_data["hp"]
            battle_data["rounds"].append({
                "round": round_number,
                "player_hp": user_data["hp"],
                "enemy_hp": npc.hp,
                "message": f"The {npc.type} {npc_dmg['message']} you for {final_damage} damage. You have {user_data['hp']} HP left"
            })

    return {"battle_data": battle_data}

def fight_player(entry: Dict, target_name: str, user_data: Dict, user: str, usersdb: Dict) -> Dict:
    target_data = entry[target_name]
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": target_name, "max_hp": target_data["hp"], "current_hp": target_data["hp"]},
        "rounds": [{
            "round": 0,
            "player_hp": user_data["hp"],
            "enemy_hp": target_data["hp"],
            "message": f"You challenged {target_name}"
        }]
    }

    round_number = 0
    while target_data["alive"] and user_data["alive"]:
        round_number += 1

        # Player attacks target
        player_attack(target_data, user_data, target_name, battle_data["rounds"], round_number)
        battle_data["enemy"]["current_hp"] = target_data["hp"]

        # Target attacks player
        player_attack(user_data, target_data, "You", battle_data["rounds"], round_number)
        battle_data["player"]["current_hp"] = user_data["hp"]

        if 0 < target_data["hp"] < 10:
            battle_data["rounds"].append({
                "round": round_number,
                "player_hp": user_data["hp"],
                "enemy_hp": target_data["hp"],
                "message": f"{target_name} has fled seeing they stand no chance against you!"
            })
            break

        if target_data["hp"] <= 0:
            experience = user_data["exp"] + 10 + target_data["exp"] / 10
            update_user_data(user=user, updated_values={"exp": experience}, user_data_dict=usersdb)
            process_defeat(target_data, target_name, 0.5, usersdb, battle_data["rounds"], round_number)
            break
        elif user_data["hp"] <= 0:
            experience = target_data["exp"] + 10 + user_data["exp"] / 10
            update_user_data(user=target_name, updated_values={"exp": experience}, user_data_dict=usersdb)
            process_defeat(user_data, user, 0.5, usersdb, battle_data["rounds"], round_number)
            break

    return {"battle_data": battle_data}


def player_attack(attacker: Dict, defender: Dict, attacker_name: str, rounds: List[Dict], round_number: int) -> None:
    print(f"{attacker_name} attacking {defender.get('name', 'opponent')}")
    if attacker["hp"] <= 0:
        print(f"{attacker_name} has 0 HP, cannot attack")
        return

    damage_dict = get_weapon_damage(attacker, attacker["exp"])
    final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], rounds, round_number)

    defender["hp"] -= final_damage
    print(f"Defender's HP reduced to {defender['hp']}")

    if attacker_name == "You":
        message = f"You {damage_dict['message']} for {final_damage} damage, they have {defender['hp']} HP left"
    else:
        message = f"{attacker_name} hits you for {final_damage} {damage_dict['message']} damage, you have {defender['hp']} HP left"

    rounds.append({
        "round": round_number,
        "player_hp": attacker["hp"] if attacker_name == "You" else defender["hp"],
        "enemy_hp": defender["hp"] if attacker_name == "You" else attacker["hp"],
        "message": message
    })

def process_defeat(entity: Dict, entity_name: str, chance: float, usersdb: Dict, rounds: List[Dict], round_number: int) -> None:
    if death_roll(chance):
        message = f"{entity_name} is defeated."
        new_data = {"alive": False, "hp": 0, "action_points": 0}
    else:
        message = f"{entity_name} barely managed to escape."
        new_data = {"action_points": entity["action_points"] - 1, "hp": 1}

    rounds.append({
        "round": round_number,
        "player_hp": entity["hp"],
        "enemy_hp": entity["hp"],
        "message": message
    })

    update_user_data(user=entity_name, updated_values=new_data, user_data_dict=usersdb)

def process_defeat(entity: Dict, entity_name: str, chance: float, usersdb: Dict) -> List[str]:
    messages = []
    if death_roll(chance):
        messages.append(f"{entity_name} is defeated.")
        new_data = {"alive": False, "hp": 0, "action_points": 0}
    else:
        messages.append(f"{entity_name} barely managed to escape.")
        new_data = {"action_points": entity["action_points"] - 1, "hp": 1}

    update_user_data(user=entity_name, updated_values=new_data, user_data_dict=usersdb)
    return messages

def process_npc_defeat(npc: entities.Enemy, user_data: Dict, user: str, usersdb: Dict, mapdb: Dict, entry: Dict,
                       battle_data: Dict, round_number: int) -> None:
    battle_data["rounds"].append({
        "round": round_number,
        "player_hp": user_data["hp"],
        "enemy_hp": 0,
        "message": f"The {npc.type} is defeated"
    })
    npc.alive = False

    if random.random() < npc.drop_chance:
        max_level = get_values(entry).get("level", 1)
        level = random.randint(1, max_level)
        new_item = generate_weapon(level=level) if random.random() < 0.5 else generate_armor(level=level)
        battle_data["rounds"].append({
            "round": round_number,
            "player_hp": user_data["hp"],
            "enemy_hp": 0,
            "message": f"You found a level {level} {new_item['type']}!"
        })
        user_data["unequipped"].append(new_item)

    remove_from_map(entity_type=npc.type.lower(), coords=get_coords(entry), map_data_dict=mapdb)

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "exp": user_data["exp"] + npc.experience,
        "hp": user_data["hp"],
        "unequipped": user_data["unequipped"],
        **{key: user_data.get(key, 0) + value for key, value in npc.regular_drop.items()}
    }

    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)

def exp_bonus(value: int, base: int = 10) -> int:
    if value <= 0:
        return 0

    lower, upper = 1, 10
    log_lower = math.log(lower, base)
    log_upper = math.log(upper, base)
    log_value = math.log(value, base)

    return int(log_lower + (log_upper - log_lower) * ((log_value - log_lower) / (log_upper - log_lower)))

def get_damage(min_dmg: int, max_dmg: int, weapon: Dict, exp_bonus: int) -> Dict:
    damage = int(min_dmg + (max_dmg - min_dmg) * random.betavariate(2, 5))

    if random.randint(1, 100) > weapon["accuracy"]:
        return {"damage": 0, "message": "miss"}

    if random.randint(1, 100) <= weapon["crit_chance"]:
        damage = int(damage * (weapon["crit_dmg_pct"] / 100))
        message = "critical hit"
    else:
        message = "hit"

    return {"damage": damage + exp_bonus, "message": message}

def death_roll(hit_chance: float) -> bool:
    if not 0 <= hit_chance <= 1:
        raise ValueError("Hit chance should be between 0 and 1 inclusive.")
    return random.random() < hit_chance

def get_fight_preconditions(user_data: Dict) -> Optional[str]:
    if user_data["action_points"] < 1:
        return "Not enough action points to fight"
    if not user_data["alive"]:
        return "You are dead"
    return None