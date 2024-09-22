import random
import math
from typing import Dict, Tuple, Optional
from collections import deque


def attempt_spell_cast(caster: Dict, spell_types: Dict) -> Optional[Dict]:
    if random.random() > 1 or not caster.get('spells'):  # 10% chance to cast a spell
        return None

    if 'spell_queue' not in caster or not caster['spell_queue']:
        caster['spell_queue'] = list(caster.get('spells', []))

    # Convert to deque if it's a list
    spell_queue = deque(caster['spell_queue']) if isinstance(caster['spell_queue'], list) else caster['spell_queue']

    for _ in range(len(spell_queue)):
        spell_name = spell_queue[0]
        if spell_types.get(spell_name) and spell_types[spell_name](0).MANA_COST <= caster.get('mana', 0):
            spell_class = spell_types[spell_name]
            spell = spell_class(0)

            # Rotate the queue
            spell_queue.append(spell_queue.popleft())

            # Update the caster's spell_queue
            caster['spell_queue'] = list(spell_queue)

            return {
                'name': spell.DISPLAY_NAME,
                'spell_object': spell,
                'mana_cost': spell.MANA_COST
            }
        else:
            # Move unavailable spell to the end and continue checking
            spell_queue.append(spell_queue.popleft())

    # Update the caster's spell_queue even if no spell was cast
    caster['spell_queue'] = list(spell_queue)

    return None

def apply_spell_effect(spell_cast: Dict, caster: Dict, target: Dict) -> Dict:
    spell = spell_cast['spell_object']
    effect_result = spell.effect(caster, target)
    caster['mana'] -= spell_cast['mana_cost']
    return effect_result

def death_roll(hit_chance: float) -> bool:
    return random.random() < hit_chance

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

def get_spell_damage(spell_damage: int, caster: Dict) -> Dict:
    magic_bonus = caster.get("sorcery", 0)
    final_damage = spell_damage + magic_bonus
    return {"damage": final_damage, "base_damage": spell_damage, "magic_bonus": magic_bonus}

def apply_armor_protection(defender: Dict, initial_damage: int, round_data: Dict, round_number: int) -> Tuple[int, int]:
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

            durability_loss = math.ceil(initial_damage / 10)
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

