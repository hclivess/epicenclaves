import random
import string
import weapons
import armor
import tools
import math


def id_generator(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def logarithmic_level(max_level):
    # Generate a random number between 0 and 1
    r = random.random()
    # Use logarithmic distribution to skew towards lower levels
    level = int(math.exp(r * math.log(max_level))) + 1
    return min(level, max_level)  # Ensure we don't exceed max_level


def generate_weapon(max_level=20, weapon_type=None):
    level = logarithmic_level(max_level)
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


def generate_armor(max_level=20, slot=None):
    level = logarithmic_level(max_level)
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


def generate_tool(max_level=20, tool_type=None):
    level = logarithmic_level(max_level)
    tool_classes = [cls for cls in tools.__dict__.values() if
                    isinstance(cls, type) and issubclass(cls, tools.Tool) and cls != tools.Tool]

    if tool_type:
        selected_class = next((cls for cls in tool_classes if cls.__name__.lower() == tool_type.lower()), None)
        if not selected_class:
            raise ValueError(f"Unknown tool type: {tool_type}")
    else:
        selected_class = random.choice(tool_classes)

    tool = selected_class()
    tool_dict = tool.to_dict()
    tool_dict['id'] = id_generator()
    tool_dict['level'] = level
    return tool_dict


def calculate_stat(base_stat, level, scaling_factor=0.1):
    return math.floor(base_stat * (1 + math.log(level, 2) * scaling_factor))


if __name__ == "__main__":
    print("Level distribution test:")
    level_counts = {i: 0 for i in range(1, 21)}
    for _ in range(10000):
        level = logarithmic_level(20)
        level_counts[level] += 1

    for level, count in level_counts.items():
        print(f"Level {level}: {count}")

    print("\nWeapon generation test:")
    for _ in range(10):
        weapon = generate_weapon()
        print(f"Generated {weapon['type']} - Level: {weapon['level']}")

    print("\nArmor generation test:")
    for _ in range(10):
        armor = generate_armor()
        print(f"Generated {armor['type']} - Level: {armor['level']}")

    print("\nTool generation test:")
    for _ in range(10):
        tool = generate_tool()
        print(f"Generated {tool['type']} - Level: {tool['level']}")