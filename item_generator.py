import random
import string
import weapons
import armor
import tools
import math

from backend import calculate_level


def id_generator(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))



def generate_weapon(min_level=1, max_level=20, weapon_type=None):
    print(f"Generating weapon: min_level={min_level}, max_level={max_level}")
    level = calculate_level(min_level, max_level, bias=1)
    weapon_classes = [cls for cls in weapons.__dict__.values() if
                      isinstance(cls, type) and issubclass(cls, weapons.Weapon) and cls != weapons.Weapon]

    if weapon_type:
        selected_class = next((cls for cls in weapon_classes if cls.__name__.lower() == weapon_type.lower()), None)
        if not selected_class:
            raise ValueError(f"Unknown weapon type: {weapon_type}")
    else:
        selected_class = random.choice(weapon_classes)

    weapon = selected_class(min_level=min_level, weapon_id=id_generator(), max_level=level)
    print(f"Generated weapon: {weapon.to_dict()}")
    return weapon.to_dict()  # Return the dictionary representation

def generate_armor(min_level=1, max_level=20, slot=None):
    print(f"Generating armor: min_level={min_level}, max_level={max_level}")
    level = calculate_level(min_level, max_level)
    armor_classes = [cls for cls in armor.__dict__.values() if
                     isinstance(cls, type) and issubclass(cls, armor.Armor) and cls != armor.Armor]

    if slot:
        selected_class = next((cls for cls in armor_classes if cls.SLOT.lower() == slot.lower()), None)
        if not selected_class:
            raise ValueError(f"Unknown armor slot: {slot}")
    else:
        selected_class = random.choice(armor_classes)

    armor_piece = selected_class(min_level=min_level, armor_id=id_generator(), max_level=level)
    print(f"Generated armor: {armor_piece.to_dict()}")
    return armor_piece.to_dict()  # Return the dictionary representation


def generate_tool(min_level=1, max_level=20, tool_type=None):
    print(f"Generating tool: min_level={min_level}, max_level={max_level}")
    level = calculate_level(min_level, max_level)
    tool_classes = [cls for cls in tools.__dict__.values() if
                    isinstance(cls, type) and issubclass(cls, tools.Tool) and cls != tools.Tool]

    if tool_type:
        selected_class = next((cls for cls in tool_classes if cls.__name__.lower() == tool_type.lower()), None)
        if not selected_class:
            raise ValueError(f"Unknown tool type: {tool_type}")
    else:
        selected_class = random.choice(tool_classes)

    tool_id = id_generator()  # Generate a unique ID for the tool
    tool = selected_class(min_level=min_level, max_level=level, tool_id=tool_id)
    tool_dict = tool.to_dict()
    tool_dict['id'] = tool_id
    tool_dict['level'] = level
    print(f"Generated tool: {tool_dict}")
    return tool_dict

def calculate_stat(base_stat, level, scaling_factor=0.1):
    return math.floor(base_stat * (1 + math.log(level, 2) * scaling_factor))


if __name__ == "__main__":
    print("Level distribution test:")
    level_counts = {i: 0 for i in range(1, 21)}
    for _ in range(10000):
        level = calculate_level(1, 20)
        level_counts[level] += 1

    for level, count in level_counts.items():
        print(f"Level {level}: {count}")

    print("\nWeapon generation test:")
    for _ in range(10):
        weapon = generate_weapon(min_level=5, max_level=15)
        print(f"Generated {weapon['type']} - Level: {weapon['level']}")

    print("\nArmor generation test:")
    for _ in range(10):
        armor = generate_armor(min_level=3, max_level=18)
        print(f"Generated {armor['type']} - Level: {armor['level']}")

    print("\nTool generation test:")
    for _ in range(10):
        tool = generate_tool(max_level=20)
        print(f"Generated {tool['type']} - Level: {tool['level']}")