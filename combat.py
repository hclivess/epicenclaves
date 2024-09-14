import random
import math
from typing import List, Dict, Any, Optional, Tuple
from map import get_coords, remove_from_map
from player import calculate_total_hp, has_item_equipped, drop_random_item
from backend import update_user_data
from item_generator import generate_weapon, generate_armor
from entities import entity_types, Enemy
from combat_utils import exp_bonus, death_roll, apply_armor_protection, calculate_armor_effectiveness, get_weapon_damage
from combat_npc import fight_npc, process_npc_defeat
from combat_player import fight_player, player_attack, process_player_defeat

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

def get_fight_preconditions(user_data: Dict) -> Optional[str]:
    if user_data["action_points"] < 1:
        return "Not enough action points to fight"
    if not user_data["alive"]:
        return "You are dead"
    return None