import random
import string
import weapons
import armor
import math

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

# Add these functions to both weapons.py and armor.py files
def calculate_stat(base_stat, level, scaling_factor=0.1):
    return math.floor(base_stat * (1 + math.log(level, 2) * scaling_factor))

# Update Weapon class in weapons.py
class Weapon:
    def __init__(self, level, weapon_id):
        self.level = level
        self.id = weapon_id
        self.base_damage = random.randint(self.MIN_DAMAGE, self.MAX_DAMAGE)
        self.damage = calculate_stat(self.base_damage, self.level)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "level": self.level,
            "damage": self.damage
        }

# Update Armor class in armor.py
class Armor:
    def __init__(self, level, armor_id):
        self.level = level
        self.id = armor_id
        self.base_defense = random.randint(self.MIN_DEFENSE, self.MAX_DEFENSE)
        self.defense = calculate_stat(self.base_defense, self.level)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "slot": self.SLOT,
            "level": self.level,
            "defense": self.defense
        }

# Update your weapon and armor subclasses in weapons.py and armor.py to use these new base classes

if __name__ == "__main__":
    print("Weapon damage progression:")
    for level in range(1, 21, 2):  # Testing levels 1, 3, 5, ..., 19
        weapon = generate_weapon(level=level)
        print(f"Level {level}: {weapon['damage']} damage")

    print("\nArmor defense progression:")
    for level in range(1, 21, 2):  # Testing levels 1, 3, 5, ..., 19
        armor = generate_armor(level=level)
        print(f"Level {level}: {armor['defense']} defense")