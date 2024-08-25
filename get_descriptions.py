import inspect
from weapons import *  # This imports all classes from the weapons.py file


def extract_weapon_description(weapon_name):
    # Get all classes from the weapons module
    weapon_classes = {name: obj for name, obj in inspect.getmembers(inspect.getmodule(Weapon))
                      if inspect.isclass(obj) and issubclass(obj, Weapon) and obj != Weapon}

    # Check if the specified weapon exists
    if weapon_name not in weapon_classes:
        return f"Error: Weapon '{weapon_name}' not found."

    weapon_class = weapon_classes[weapon_name]

    # Extract the description if it exists
    if hasattr(weapon_class, 'DESCRIPTION'):
        return weapon_class.DESCRIPTION
    else:
        return f"No description available for {weapon_name}."


# Example usage:
if __name__ == "__main__":
    weapon_name = input("Enter the name of the weapon: ")
    description = extract_weapon_description(weapon_name)
    print(f"{weapon_name}: {description}")