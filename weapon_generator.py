import random
import string


def id_generator(length=10):
    """Generate a random alphanumeric string of given length."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_weapon():
    weapon_types = ["sword", "axe", "bow", "spear", "dagger", "mace"]
    weapon_damage = {
        "sword": (7, 12),
        "axe": (9, 15),
        "bow": (5, 10),
        "spear": (6, 11),
        "dagger": (3, 7),
        "mace": (8, 13)
    }

    selected_weapon = random.choice(weapon_types)
    base_min_damage, base_max_damage = weapon_damage[selected_weapon]

    # Adding variance: +/- up to 20% of the base damage value
    min_damage = int(base_min_damage * random.uniform(0.8, 1.2))
    max_damage = int(base_max_damage * random.uniform(0.8, 1.2))

    # Ensure that max_damage is at least one point higher than min_damage
    if max_damage <= min_damage:
        max_damage = min_damage + 1

    weapon_dict = {
        "type": selected_weapon,
        "min_damage": min_damage,
        "max_damage": max_damage,
        "cls": "right_hand",
        "id": id_generator(),
    }

    return weapon_dict


if __name__ == "__main__":
    weapon_json = generate_weapon()
    print(weapon_json)


