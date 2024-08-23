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

# Add this function to the weapons.py file
def calculate_damage(base_damage, level):
    return math.floor(base_damage * (1 + math.log(level, 2) * 0.1))

class Weapon:
    def __init__(self, level, weapon_id):
        self.level = level
        self.id = weapon_id
        self.base_damage = random.randint(self.MIN_DAMAGE, self.MAX_DAMAGE)
        self.damage = calculate_damage(self.base_damage, self.level)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "level": self.level,
            "damage": self.damage
        }

# Update your weapon classes in weapons.py to use the new Weapon base class

if __name__ == "__main__":
    print("Weapon damage progression:")
    for level in range(1, 11):
        weapon = generate_weapon(level=level)
        print(f"Level {level}: {weapon['damage']} damage")

    print("\nArmor progression:")
    for level in range(1, 11):
        armor = generate_armor(level=level)
        print(f"Level {level}: {armor['defense']} defense")