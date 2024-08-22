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

def apply_armor_protection(defender: Dict, initial_damage: int, messages: List[str]) -> Tuple[int, int]:
    print(f"Applying armor protection. Initial damage: {initial_damage}")
    armor_protection = 0
    is_player = defender.get('name', 'You') == 'You'

    all_armor_slots = [armor for armor in defender.get("equipped", []) if armor.get("role") == "armor"]

    if all_armor_slots:
        selected_armor = random.choice(all_armor_slots)
        print(f"Selected armor: {selected_armor}")

        if selected_armor.get("type") != "empty":
            protection = selected_armor.get("protection", 0) * (selected_armor.get("efficiency", 100) / 100)
            armor_protection = protection
            print(f"Armor protection: {armor_protection}")

            old_durability = selected_armor["durability"]
            selected_armor["durability"] -= 1

            if is_player:
                messages.append(
                    f"Your {selected_armor['type']}'s durability reduced from {old_durability} to {selected_armor['durability']}")
            else:
                messages.append(
                    f"{defender['name']}'s {selected_armor['type']} durability reduced from {old_durability} to {selected_armor['durability']}")

            if selected_armor["durability"] <= 0:
                if is_player:
                    messages.append(f"Your {selected_armor['type']} has broken and no longer provides protection!")
                else:
                    messages.append(
                        f"{defender['name']}'s {selected_armor['type']} has broken and no longer provides protection!")
                selected_armor["type"] = "empty"
                selected_armor["protection"] = 0
        else:
            if is_player:
                messages.append("The attack hit an unprotected area!")
            else:
                messages.append(f"The attack hit an unprotected area on {defender['name']}!")

    final_damage = math.floor(max(1, initial_damage - armor_protection))
    absorbed_damage = initial_damage - final_damage
    print(f"Final damage: {final_damage}, Absorbed damage: {absorbed_damage}")

    if absorbed_damage > 0:
        if is_player:
            messages.append(f"Your armor absorbed {absorbed_damage} damage")
        else:
            messages.append(f"{defender['name']}'s armor absorbed {absorbed_damage} damage")

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
    messages = []
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": target, "max_hp": 0, "current_hp": 0}
    }

    entity_class = get_entity_class(target)

    if entity_class:
        print(f"Found entity class: {entity_class.__name__}")
    else:
        print(f"No valid entity class found for: {target}")
        messages.append(f"No valid target found: {target}")
        return {"messages": messages, "battle_data": battle_data}

    for entry in on_tile_map:
        entry_type = get_values(entry).get("type")
        print(f"Processing map entry. Type: {entry_type}")

        if issubclass(entity_class, entities.Enemy):
            print(f"Fighting NPC: {target}")
            enemy = entity_class()
            battle_data["enemy"]["max_hp"] = enemy.hp
            battle_data["enemy"]["current_hp"] = enemy.hp
            fight_result = fight_npc(entry, user_data, user, usersdb, mapdb, enemy)
            messages.extend(fight_result["messages"])
            battle_data.update(fight_result["battle_data"])
        elif target == "player" and entry_type == "player":
            print(f"Fighting player: {target_name}")
            fight_result = fight_player(entry, target_name, user_data, user, usersdb)
            messages.extend(fight_result["messages"])
            battle_data.update(fight_result["battle_data"])

    for entry in on_tile_users:
        entry_type = get_values(entry).get("type")
        entry_name = get_coords(entry)
        print(f"Processing user entry. Type: {entry_type}, Name: {entry_name}")

        if target == "player" and entry_type == "player" and target_name == entry_name:
            print(f"Fighting player: {target_name}")
            fight_result = fight_player(entry, target_name, user_data, user, usersdb)
            messages.extend(fight_result["messages"])
            battle_data.update(fight_result["battle_data"])

    if not messages:
        print(f"No valid target found for: {target}")
        messages.append(f"No valid target found: {target}")

    return {"messages": messages, "battle_data": battle_data}

def fight_npc(entry: Dict, user_data: Dict, user: str, usersdb: Dict, mapdb: Dict, npc: entities.Enemy) -> Dict:
    messages = []
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": npc.type, "max_hp": npc.hp, "current_hp": npc.hp}
    }

    while npc.alive and user_data["alive"]:
        if npc.hp < 1:
            process_npc_defeat(npc, user_data, user, usersdb, mapdb, entry, messages)
            battle_data["enemy"]["current_hp"] = 0
            break

        if user_data["hp"] < 1:
            if death_roll(npc.kill_chance):
                messages.append("You died")
                user_data["alive"] = False
                update_user_data(user=user, updated_values={"alive": False, "hp": 0}, user_data_dict=usersdb)
            else:
                messages.append("You are almost dead but managed to escape")
                update_user_data(user=user, updated_values={"action_points": user_data["action_points"] - 1, "hp": 1},
                                 user_data_dict=usersdb)
            battle_data["player"]["current_hp"] = user_data["hp"]
            break

        # Player attacks NPC
        user_dmg = get_weapon_damage(user_data, user_data["exp"])
        npc.hp -= user_dmg['damage']
        battle_data["enemy"]["current_hp"] = npc.hp
        messages.append(
            f"You {user_dmg['message']} the {npc.type} for {user_dmg['damage']} damage. It has {npc.hp} HP left")

        # NPC attacks player
        if npc.hp > 0:
            npc_dmg = npc.roll_damage()
            user_with_name = {"name": "You", **user_data}  # Add 'name' key to user_data
            final_damage, _ = apply_armor_protection(user_with_name, npc_dmg["damage"], messages)
            user_data["hp"] -= final_damage
            battle_data["player"]["current_hp"] = user_data["hp"]
            messages.append(
                f"The {npc.type} {npc_dmg['message']} you for {final_damage} damage. You have {user_data['hp']} HP left")

    return {"messages": messages, "battle_data": battle_data}

def fight_player(entry: Dict, target_name: str, user_data: Dict, user: str, usersdb: Dict) -> Dict:
    messages = []
    target_data = entry[target_name]
    battle_data = {
        "player": {"name": user, "max_hp": user_data["hp"], "current_hp": user_data["hp"]},
        "enemy": {"name": target_name, "max_hp": target_data["hp"], "current_hp": target_data["hp"]}
    }

    messages.append(f"You challenged {target_name}")

    while target_data["alive"] and user_data["alive"]:
        # Player attacks target
        player_attack(target_data, user_data, target_name, messages)
        battle_data["enemy"]["current_hp"] = target_data["hp"]

        # Target attacks player
        player_attack(user_data, target_data, "You", messages)
        battle_data["player"]["current_hp"] = user_data["hp"]

        if 0 < target_data["hp"] < 10:
            messages.append(f"{target_name} has fled seeing they stand no chance against you!")
            break

        if target_data["hp"] <= 0:
            experience = user_data["exp"] + 10 + target_data["exp"] / 10
            update_user_data(user=user, updated_values={"exp": experience}, user_data_dict=usersdb)
            messages.extend(process_defeat(target_data, target_name, 0.5, usersdb))
            break
        elif user_data["hp"] <= 0:
            experience = target_data["exp"] + 10 + user_data["exp"] / 10
            update_user_data(user=target_name, updated_values={"exp": experience}, user_data_dict=usersdb)
            messages.extend(process_defeat(user_data, user, 0.5, usersdb))
            break

    return {"messages": messages, "battle_data": battle_data}

def player_attack(attacker: Dict, defender: Dict, attacker_name: str, messages: List[str]) -> None:
    print(f"{attacker_name} attacking {defender.get('name', 'opponent')}")
    if attacker["hp"] <= 0:
        print(f"{attacker_name} has 0 HP, cannot attack")
        return

    damage_dict = get_weapon_damage(attacker, attacker["exp"])
    final_damage, absorbed_damage = apply_armor_protection(defender, damage_dict['damage'], messages)

    defender["hp"] -= final_damage
    print(f"Defender's HP reduced to {defender['hp']}")

    if attacker_name == "You":
        messages.append(f"You {damage_dict['message']} for {final_damage} damage, they have {defender['hp']} HP left")
    else:
        messages.append(
            f"{attacker_name} hits you for {final_damage} {damage_dict['message']} damage, you have {defender['hp']} HP left")

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
                       messages: List[str]) -> None:
    messages.append(f"The {npc.type} is defeated")
    npc.alive = False

    if random.random() < npc.drop_chance:
        max_level = get_values(entry).get("level", 1)
        level = random.randint(1, max_level)
        new_item = generate_weapon(level=level) if random.random() < 0.5 else generate_armor(level=level)
        messages.append(f"You found a level {level} {new_item['type']}!")
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