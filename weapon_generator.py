import random
import string
import weapons
import armor


def id_generator(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def generate_weapon(level=1, weapon_type=None):
    weapon_classes = [cls for cls in weapons.__dict__.values() if
                      isinstance(cls, type) and issubclass(cls, weapons.Weapon) and cls != weapons.Weapon]

    if weapon_type:
        selected_class = next((cls for cls in weapon_classes if cls.__name__.lower() == weapon_type.lower()), None)
        if not selected_class:
            raise ValueError(f"Unknown weapon type: {weapon_type}")
    else:
        selected_class = random.choice(weapon_classes)

    weapon = selected_class(level, id_generator())
    return weapon.to_dict()  # Return the dictionary representation


def generate_armor(level=1, slot=None):
    armor_classes = [cls for cls in armor.__dict__.values() if
                     isinstance(cls, type) and issubclass(cls, armor.Armor) and cls != armor.Armor]

    if slot:
        selected_class = next((cls for cls in armor_classes if cls.SLOT.lower() == slot.lower()), None)
        if not selected_class:
            raise ValueError(f"Unknown armor slot: {slot}")
    else:
        selected_class = random.choice(armor_classes)

    armor_piece = selected_class(level, id_generator())
    return armor_piece.to_dict()  # Return the dictionary representation


if __name__ == "__main__":
    weapon = generate_weapon(level=2)
    print("Generated weapon:", weapon)

    armor = generate_armor(level=2)
    print("Generated armor:", armor)