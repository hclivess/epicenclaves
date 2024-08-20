import random
import string


def id_generator(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_weapon(level=1):
    weapon_types = ["sword", "axe", "bow", "spear", "dagger", "mace"]
    weapon_damage = {
        "sword": (7, 12),
        "axe": (9, 15),
        "bow": (5, 10),
        "spear": (6, 11),
        "dagger": (3, 7),
        "mace": (8, 13)
    }

    weapon_ranges = {
        "sword": "melee",
        "axe": "melee",
        "bow": "ranged",
        "spear": "melee",
        "dagger": "melee",
        "mace": "melee"
    }

    selected_weapon = random.choice(weapon_types)
    base_min_damage, base_max_damage = weapon_damage[selected_weapon]
    min_damage = int(base_min_damage * random.uniform(0.8, 1.2) * level)
    max_damage = int(base_max_damage * random.uniform(0.8, 1.2) * level)

    if max_damage <= min_damage:
        max_damage = min_damage + 1

    weapon_dict = {
        "type": selected_weapon,
        "range": weapon_ranges[selected_weapon],
        "min_damage": min_damage,
        "max_damage": max_damage,
        "role": "right_hand",
        "id": id_generator(),
        "level": level
    }

    if weapon_dict["range"] == "ranged":
        weapon_dict["accuracy"] = 50
        weapon_dict["crit_dmg_pct"] = 200  # percentual
        weapon_dict["crit_chance"] = 100
    else:
        weapon_dict["accuracy"] = random.randint(80, 100)
        weapon_dict["crit_dmg_pct"] = random.randint(100, 400)
        weapon_dict["crit_chance"] = random.randint(1, 10)

    return weapon_dict


def generate_armor(level=1):
    armor_types = ["helmet", "chestplate", "leggings", "boots"]
    armor_base_protection = {
        "helmet": 5,
        "chestplate": 8,
        "leggings": 7,
        "boots": 4
    }

    selected_armor = random.choice(armor_types)
    base_protection = armor_base_protection[selected_armor]
    protection = int(base_protection * random.uniform(0.8, 1.2) * level)

    armor_dict = {
        "type": selected_armor,
        "protection": protection,
        "durability": random.randint(50, 100) * level,
        "efficiency": random.randint(80, 100),
        "role": "armor",
        "id": id_generator(),
        "level": level
    }

    return armor_dict


if __name__ == "__main__":
    weapon_json = generate_weapon(level=2)
    print("Generated weapon:", weapon_json)

    armor_json = generate_armor(level=2)
    print("Generated armor:", armor_json)