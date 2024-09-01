from backend import update_user_data, get_values, get_user, has_item_equipped
from map import remove_from_map, get_coords
import entities
from item_generator import generate_weapon, generate_armor, logarithmic_level
import math
import random
from typing import Dict, List, Tuple, Optional


def get_entity_class(target: str) -> Optional[type]:
    """
    Get the entity class based on the target string.
    Handles case sensitivity, multi-word entity names, and type-class name mismatches.
    """
    normalized_target = target.replace('_', '').lower()

    for name in dir(entities):
        if name.lower() == normalized_target:
            return getattr(entities, name)

    words_to_remove = ['whelp', 'monster', 'creature', 'enemy']
    simplified_target = ''.join(word for word in normalized_target.split() if word not in words_to_remove)

    for name in dir(entities):
        if simplified_target in name.lower():
            return getattr(entities, name)

    print(f"No matching entity class found for '{target}'")
    return None


def fight_npc(entry: Dict, user_data: Dict, user: str, usersdb: Dict, mapdb: Dict, npc: entities.Enemy) -> Dict:
    entity_data = get_values(entry)

    npc.level = entity_data.get('level', 1)
    npc.hp = entity_data.get('hp', npc.calculate_hp())
    npc.max_hp = entity_data.get('max_hp', npc.hp)
    npc.min_damage, npc.max_damage = npc.calculate_damage()

    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": npc.type, "max_hp": npc.max_hp, "current_hp": npc.hp, "level": npc.level},
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

        exp_bonus_value = exp_bonus(user_data["exp"])
        user_dmg = get_weapon_damage(user_data, exp_bonus_value)
        npc.hp -= user_dmg['damage']
        battle_data["enemy"]["current_hp"] = npc.hp
        battle_data["rounds"].append({
            "round": round_number,
            "player_hp": user_data["hp"],
            "enemy_hp": npc.hp,
            "message": f"You {user_dmg['message']} the level {npc.level} {npc.type} for {user_dmg['damage']} damage "
                       f"(Base: {user_dmg['base_damage']}, Exp bonus: {user_dmg['exp_bonus']}). "
                       f"It has {npc.hp}/{npc.max_hp} HP left"
        })

        if npc.hp > 0:
            npc_dmg = npc.roll_damage()
            final_damage, absorbed_damage = apply_armor_protection(user_data, npc_dmg["damage"], battle_data["rounds"],
                                                                   round_number)
            user_data["hp"] -= final_damage
            battle_data["player"]["current_hp"] = user_data["hp"]
            battle_data["rounds"].append({
                "round": round_number,
                "player_hp": user_data["hp"],
                "enemy_hp": npc.hp,
                "message": f"The level {npc.level} {npc.type} {npc_dmg['message']} you for {final_damage} damage "
                           f"(Damage range: {npc.min_damage}-{npc.max_damage}). You have {user_data['hp']} HP left"
            })

    return {"battle_data": battle_data}


def determine_item_level(max_level: int) -> int:
    """
    Determine item level using a logarithmic distribution.
    Higher levels are progressively harder to obtain.
    """
    if max_level <= 1:
        return 1
    r = random.random()
    level = int(math.exp(r * math.log(max_level))) + 1
    return min(level, max_level)


def process_npc_defeat(npc: entities.Enemy, user_data: Dict, user: str, usersdb: Dict, mapdb: Dict, entry: Dict,
                       battle_data: Dict, round_number: int) -> None:
    battle_data["rounds"].append({
        "round": round_number,
        "player_hp": user_data["hp"],
        "enemy_hp": 0,
        "message": f"The level {npc.level} {npc.type} is defeated"
    })
    npc.alive = False

    if random.random() < npc.drop_chance:
        min_item_level = max(1, npc.level - 9)  # Ensure minimum level is at least 1
        max_item_level = npc.level

        # Use logarithmic_level to generate the item level
        item_level = logarithmic_level(min_item_level, max_item_level)

        new_item = generate_weapon(min_level=item_level,
                                   max_level=item_level) if random.random() < 0.5 else generate_armor(
            min_level=item_level, max_level=item_level)

        battle_data["rounds"].append({
            "round": round_number,
            "player_hp": user_data["hp"],
            "enemy_hp": 0,
            "message": f"You found a level {new_item['level']} {new_item['type']}!"
        })
        user_data["unequipped"].append(new_item)
    else:
        battle_data["rounds"].append({
            "round": round_number,
            "player_hp": user_data["hp"],
            "enemy_hp": 0,
            "message": f"The defeated {npc.type} didn't drop any items."
        })

    remove_from_map(entity_type=npc.type.lower(), coords=get_coords(entry), map_data_dict=mapdb)

    scaled_experience = calculate_scaled_stat(npc.experience, npc.level, scaling_factor=0.1)

    updated_values = {
        "action_points": user_data["action_points"] - 1,
        "exp": user_data["exp"] + scaled_experience,
        "hp": user_data["hp"],
        "unequipped": user_data["unequipped"],
        **{key: user_data.get(key, 0) + value for key, value in npc.regular_drop.items()}
    }

    update_user_data(user=user, updated_values=updated_values, user_data_dict=usersdb)


def calculate_scaled_stat(base_stat, level, scaling_factor=0.1):
    return math.floor(base_stat * (1 + math.log(level, 2) * scaling_factor))


def exp_bonus(value: int, base: int = 10) -> int:
    if value <= 0:
        return 0
    return int(math.log(value, base))


def death_roll(hit_chance: float) -> bool:
    return random.random() < hit_chance


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


def apply_armor_protection(defender: Dict, initial_damage: int, rounds: List[Dict], round_number: int) -> Tuple[
    int, int]:
    print(f"Applying armor protection. Initial damage: {initial_damage}")
    armor_protection = 0
    is_player = defender.get('name', 'You') == 'You'

    all_armor_slots = [armor for armor in defender.get("equipped", []) if armor.get("role") == "armor"]

    if all_armor_slots:
        selected_armor = random.choice(all_armor_slots)
        print(f"Selected armor: {selected_armor}")

        if selected_armor.get("type") != "empty" and selected_armor["durability"] > 0:
            effective_protection = calculate_armor_effectiveness(selected_armor, initial_damage)
            armor_protection = min(initial_damage, effective_protection)

            # Handle the case where initial_damage is zero
            if initial_damage > 0:
                damage_reduction_percentage = (armor_protection / initial_damage) * 100
            else:
                damage_reduction_percentage = 100 if armor_protection > 0 else 0

            armor_info = f"Your {selected_armor['type']}" if is_player else f"{defender['name']}'s {selected_armor['type']}"
            final_damage = max(0, initial_damage - armor_protection)

            rounds.append({
                "round": round_number,
                "player_hp": defender["hp"],
                "enemy_hp": defender["hp"],
                "message": (
                    f"{armor_info} (Base Protection: {selected_armor['protection']}, "
                    f"Efficiency: {selected_armor['efficiency']}%, "
                    f"Durability: {selected_armor['durability']}/{selected_armor['max_durability']}) "
                    f"reduced damage by {damage_reduction_percentage:.1f}% ({armor_protection} points). "
                )
            })

            durability_loss = math.ceil(initial_damage / 10)
            old_durability = selected_armor["durability"]
            selected_armor["durability"] = max(0, selected_armor["durability"] - durability_loss)

            if selected_armor["durability"] <= 0:
                message = f"Your {selected_armor['type']} has broken and is no longer usable!" if is_player else f"{defender['name']}'s {selected_armor['type']} has broken and is no longer usable!"
                rounds.append({
                    "round": round_number,
                    "player_hp": defender["hp"],
                    "enemy_hp": defender["hp"],
                    "message": message
                })
                defender["equipped"] = [item for item in defender["equipped"] if item != selected_armor]
        else:
            message = "The attack hit an unprotected area!" if is_player else f"The attack hit an unprotected area on {defender['name']}!"
            rounds.append({
                "round": round_number,
                "player_hp": defender["hp"],
                "enemy_hp": defender["hp"],
                "message": message
            })
            final_damage = initial_damage
    else:
        final_damage = initial_damage
        message = "You have no armor equipped!" if is_player else f"{defender['name']} has no armor equipped!"
        rounds.append({
            "round": round_number,
            "player_hp": defender["hp"],
            "enemy_hp": defender["hp"],
            "message": message
        })

    absorbed_damage = initial_damage - final_damage
    print(f"Final damage: {final_damage}, Absorbed damage: {absorbed_damage}")

    return final_damage, absorbed_damage


def get_weapon_damage(attacker: Dict, exp_bonus_value: int) -> Dict:
    print(f"Getting weapon damage for attacker. Exp bonus: {exp_bonus_value}")
    default_weapon = {
        "min_damage": 1,
        "max_damage": 2,
        "accuracy": 100,
        "crit_chance": 5,
        "crit_dmg_pct": 150
    }

    weapon = None
    for item in attacker.get("equipped", []):
        if item.get("slot") == "right_hand":
            weapon = item
            break

    if not weapon:
        print("No weapon found, using default values")
        weapon = default_weapon

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
    print(f"Weapon damage: {final_damage}, Base damage: {damage}, Exp bonus: {exp_bonus_value}, Message: {message}")
    return {"damage": final_damage, "base_damage": damage, "exp_bonus": exp_bonus_value, "message": message}


def fight(target: str, target_name: str, on_tile_map: List[Dict], on_tile_users: List[Dict], user_data: Dict, user: str,
          usersdb: Dict, mapdb: Dict) -> Dict:
    print(f"Starting fight. Target: {target}, Target name: {target_name}")
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": target, "max_hp": 0, "current_hp": 0},
        "rounds": []
    }

    if target.lower() == "player":
        # Handle PvP combat
        for entry in on_tile_users:
            entry_name = get_coords(entry)
            if entry_name == target_name:
                print(f"Fighting player: {target_name}")
                fight_result = fight_player(entry, target_name, user_data, user, usersdb)
                battle_data.update(fight_result["battle_data"])
                return {"battle_data": battle_data}
    else:
        # Handle NPC combat
        entity_class = get_entity_class(target)

        if entity_class:
            print(f"Found entity class: {entity_class.__name__}")
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
                    return {"battle_data": battle_data}
        else:
            print(f"No valid entity class found for: {target}")

    # If we reach here, no valid target was found
    battle_data["rounds"].append({"round": 0, "message": f"No valid target found: {target}"})
    return {"battle_data": battle_data}

def fight_player(entry: Dict, target_name: str, user_data: Dict, user: str, usersdb: Dict) -> Dict:
    target_data = get_user(target_name, usersdb)
    if not target_data:
        return {"battle_data": {"rounds": [{"message": f"Target player {target_name} not found"}]}}

    target_data = target_data[target_name]
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

        player_attack(target_data, user_data, target_name, battle_data["rounds"], round_number)
        battle_data["enemy"]["current_hp"] = target_data["hp"]

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
            experience = user_data["exp"] + 10 + target_data["exp"] // 10
            update_user_data(user, {"exp": experience}, usersdb)
            process_player_defeat(target_data, target_name, user_data, user, 0.5, usersdb, battle_data["rounds"], round_number)
            break
        elif user_data["hp"] <= 0:
            experience = target_data["exp"] + 10 + user_data["exp"] // 10
            update_user_data(target_name, {"exp": experience}, usersdb)
            process_player_defeat(user_data, user, target_data, target_name, 0.5, usersdb, battle_data["rounds"], round_number)
            break

    return {"battle_data": battle_data}

def process_player_defeat(defeated: Dict, defeated_name: str, victor: Dict, victor_name: str, death_chance: float, usersdb: Dict, rounds: List[Dict], round_number: int) -> None:
    if random.random() < death_chance:
        message = f"{defeated_name} is defeated."
        new_data = {"alive": False, "hp": 0, "action_points": 0}
    else:
        message = f"{defeated_name} barely managed to escape."
        new_data = {"action_points": defeated["action_points"] - 1, "hp": 1}

    rounds.append({
        "round": round_number,
        "player_hp": defeated["hp"],
        "enemy_hp": defeated["hp"],
        "message": message
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

            rounds.append({
                "round": round_number,
                "player_hp": defeated["hp"],
                "enemy_hp": defeated["hp"],
                "message": f"{victor_name} looted a {dropped_item['type']} from {defeated_name}'s territory!"
            })
            update_user_data(victor_name, {"unequipped": victor["unequipped"], "equipped": victor["equipped"]}, usersdb)

    update_user_data(defeated_name, new_data, usersdb)


def drop_random_item(player: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    inventory = player.get("unequipped", [])
    equipped_items = [item for item in player.get("equipped", []) if item["type"] != "empty"]

    all_items = inventory + equipped_items
    if not all_items:
        return None, None

    dropped_item = random.choice(all_items)
    if dropped_item in inventory:
        player["unequipped"].remove(dropped_item)
        return dropped_item, "unequipped"
    else:
        player["equipped"] = [item for item in player["equipped"] if item != dropped_item]
        return dropped_item, dropped_item["slot"]

def player_attack(attacker: Dict, defender: Dict, attacker_name: str, rounds: List[Dict], round_number: int) -> None:
    if attacker["hp"] <= 0:
        return

    exp_bonus_value = exp_bonus(attacker["exp"])
    damage_dict = get_weapon_damage(attacker, exp_bonus_value)
    final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], rounds, round_number)

    defender["hp"] -= final_damage

    if attacker_name == "You":
        message = (f"You {damage_dict['message']} for {final_damage} damage "
                   f"(Base: {damage_dict['base_damage']}, Exp bonus: {damage_dict['exp_bonus']}), "
                   f"they have {defender['hp']} HP left")
    else:
        message = (f"{attacker_name} hits you for {final_damage} {damage_dict['message']} damage "
                   f"(Base: {damage_dict['base_damage']}, Exp bonus: {damage_dict['exp_bonus']}), "
                   f"you have {defender['hp']} HP left")

    rounds.append({
        "round": round_number,
        "player_hp": attacker["hp"] if attacker_name == "You" else defender["hp"],
        "enemy_hp": defender["hp"] if attacker_name == "You" else attacker["hp"],
        "message": message
    })


def process_defeat(entity: Dict, entity_name: str, chance: float, usersdb: Dict, rounds: List[Dict],
                   round_number: int) -> None:
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

def get_fight_preconditions(user_data: Dict) -> Optional[str]:
    if user_data["action_points"] < 1:
        return "Not enough action points to fight"
    if not user_data["alive"]:
        return "You are dead"
    return None