import random
from typing import Dict, List, Optional
from collections import deque


def attempt_spell_cast(caster: Dict, spell_types: Dict) -> Optional[Dict]:
    if random.random() > 0.1 or not caster.get('spells'):  # 10% chance to cast a spell
        return None

    if 'spell_queue' not in caster or not caster['spell_queue']:
        caster['spell_queue'] = list(caster.get('spells', []))

    spell_queue = deque(caster['spell_queue']) if isinstance(caster['spell_queue'], list) else caster['spell_queue']

    for _ in range(len(spell_queue)):
        spell_name = spell_queue[0]
        if spell_types.get(spell_name) and spell_types[spell_name](0).MANA_COST <= caster.get('mana', 0):
            spell_class = spell_types[spell_name]
            spell = spell_class(0)
            spell_queue.append(spell_queue.popleft())
            caster['spell_queue'] = list(spell_queue)
            return {
                'name': spell.DISPLAY_NAME,
                'spell_object': spell,
                'mana_cost': spell.MANA_COST
            }
        else:
            spell_queue.append(spell_queue.popleft())

    caster['spell_queue'] = list(spell_queue)
    return None


def apply_spell_effect(spell_cast: Dict, caster: Dict, target: Dict) -> Dict:
    spell = spell_cast['spell_object']
    effect_result = spell.effect(caster, target)
    caster['mana'] -= spell_cast['mana_cost']

    if 'damage_dealt' in effect_result:
        spell_damage = effect_result['damage_dealt']
        damage_info = get_spell_damage(spell_damage, caster)
        effect_result['damage_info'] = damage_info

    return effect_result


def get_spell_damage(spell_damage: int, caster: Dict) -> Dict:
    magic_bonus = caster.get("sorcery", 0)
    final_damage = spell_damage
    return {"damage": final_damage, "base_damage": spell_damage, "magic_bonus": magic_bonus}


def get_weapon_damage(attacker: Dict) -> Dict:
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
        return {"damage": 0, "base_damage": 0, "martial_bonus": 0, "message": "miss"}

    if random.randint(1, 100) <= crit_chance:
        damage = int(damage * (crit_dmg_pct / 100))
        message = "critical hit"
    else:
        message = "hit"

    martial_bonus = attacker.get("martial", 0)
    final_damage = damage + martial_bonus
    return {"damage": final_damage, "base_damage": damage, "martial_bonus": martial_bonus, "message": message}


def apply_armor_protection(defender: Dict, initial_damage: int, round_data: Dict) -> int:
    armor_protection = 0
    defender_name = defender.get('username', 'Unknown')

    all_armor_slots = [armor for armor in defender.get("equipped", []) if armor.get("role") == "armor"]

    if all_armor_slots:
        selected_armor = random.choice(all_armor_slots)

        if selected_armor.get("type") != "empty" and selected_armor["durability"] > 0:
            effective_protection = calculate_armor_effectiveness(selected_armor, initial_damage)
            armor_protection = min(initial_damage, effective_protection)

            damage_reduction_percentage = (armor_protection / initial_damage) * 100 if initial_damage > 0 else 0

            armor_info = f"{defender_name}'s {selected_armor['type']}"
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

            durability_loss = max(1, int(initial_damage / 10))
            selected_armor["durability"] = max(0, selected_armor["durability"] - durability_loss)

            if selected_armor["durability"] <= 0:
                round_data["actions"].append({
                    "actor": "system",
                    "type": "armor_break",
                    "message": f"{defender_name}'s {selected_armor['type']} has broken and is no longer usable!"
                })
                defender["equipped"] = [item for item in defender["equipped"] if item != selected_armor]
        else:
            round_data["actions"].append({
                "actor": "system",
                "type": "armor_miss",
                "message": f"The attack hit an unprotected area on {defender_name}!"
            })
            final_damage = initial_damage
    else:
        final_damage = initial_damage
        round_data["actions"].append({
            "actor": "system",
            "type": "no_armor",
            "message": f"{defender_name} has no armor equipped!"
        })

    return final_damage


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


def player_turn(player: Dict, enemy: Dict, spell_types: Dict) -> Dict:
    spell_cast = attempt_spell_cast(player, spell_types)

    if spell_cast:
        effect = apply_spell_effect(spell_cast, player, enemy)
        return {
            "actor": "player",
            "type": "spell",
            "spell_name": spell_cast["name"],
            "effect": effect,
            "damage_dealt": effect.get("damage_dealt", 0),
            "healing_done": effect.get("healing_done", 0),
            "mana_used": spell_cast["mana_cost"]
        }
    else:
        weapon_damage = get_weapon_damage(player)
        return {
            "actor": "player",
            "type": "attack",
            "damage_dealt": weapon_damage["damage"],
            "message": f"{weapon_damage['message'].capitalize()}! Dealt {weapon_damage['damage']} damage."
        }


def enemy_turn(enemy: Dict, player: Dict) -> Dict:
    weapon_damage = get_weapon_damage(enemy)
    return {
        "actor": "enemy",
        "type": "attack",
        "damage_dealt": weapon_damage["damage"],
        "message": f"Enemy {weapon_damage['message']}! Dealt {weapon_damage['damage']} damage."
    }


def process_combat_round(player: Dict, enemy: Dict, round_number: int, spell_types: Dict) -> Dict:
    round_data = {
        "round": round_number,
        "actions": [],
        "player_hp": player["hp"],
        "enemy_hp": enemy["hp"]
    }

    # Player's turn
    player_action = player_turn(player, enemy, spell_types)
    round_data["actions"].append(player_action)

    # Apply damage to enemy and check for defeat
    initial_damage = player_action.get("damage_dealt", 0)
    final_damage = apply_armor_protection(enemy, initial_damage, round_data)
    enemy["hp"] = max(0, enemy["hp"] - final_damage)
    round_data["enemy_hp"] = enemy["hp"]

    if enemy["hp"] <= 0:
        round_data["actions"].append({
            "actor": "system",
            "type": "defeat",
            "message": f"The level {enemy['level']} {enemy['name']} is defeated"
        })
        return round_data

    # Enemy's turn
    enemy_action = enemy_turn(enemy, player)
    round_data["actions"].append(enemy_action)

    # Apply damage to player
    initial_damage = enemy_action.get("damage_dealt", 0)
    final_damage = apply_armor_protection(player, initial_damage, round_data)
    player["hp"] = max(0, player["hp"] - final_damage)
    round_data["player_hp"] = player["hp"]

    return round_data


def combat_loop(player: Dict, enemy: Dict, spell_types: Dict) -> List[Dict]:
    rounds = []
    round_number = 0

    # Initial round to show starting HP
    rounds.append({
        "round": round_number,
        "message": f"Battle starts! {player['name']} (HP: {player['hp']}/{player['max_hp']}) vs Level {enemy['level']} {enemy['name']} (HP: {enemy['hp']}/{enemy['max_hp']})",
        "player_hp": player["hp"],
        "enemy_hp": enemy["hp"],
        "actions": []
    })

    while player["hp"] > 0 and enemy["hp"] > 0:
        round_number += 1
        round_data = process_combat_round(player, enemy, round_number, spell_types)
        rounds.append(round_data)

        if enemy["hp"] <= 0 or player["hp"] <= 0:
            break

    return rounds


def start_combat(player: Dict, enemy: Dict, spell_types: Dict) -> Dict:
    combat_rounds = combat_loop(player, enemy, spell_types)
    return {
        "battle_data": {
            "player": {"name": player["name"], "max_hp": player["max_hp"], "current_hp": player["hp"]},
            "enemy": {"name": enemy["name"], "max_hp": enemy["max_hp"], "current_hp": enemy["hp"],
                      "level": enemy["level"]},
            "rounds": combat_rounds
        }
    }