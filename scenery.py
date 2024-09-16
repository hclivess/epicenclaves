from typing import List, Dict

class Scenery:
    probability = 0
    role = "scenery"
    type = "scenery"
    biome = "any"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

    def to_dict(self) -> Dict[str, any]:
        return {
            "role": self.role,
            "type": self.type,
            "biome": self.biome
        }

class Forest(Scenery):
    biome = "forest"
    type = "forest"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "chop", "action": "/chop?amount=1"},
            {"name": "chop 10", "action": "/chop?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Pond(Scenery):
    biome = "pond"
    type = "pond"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "fish", "action": "/fish"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Cavern(Scenery):
    biome = "cavern"
    type = "cavern"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Graveyard(Scenery):
    biome = "graveyard"
    type = "graveyard"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Desert(Scenery):
    biome = "desert"
    type = "desert"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Gnomes(Scenery):
    biome = "gnomes"
    type = "gnomes"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return []

class Mountain(Scenery):
    biome = "mountain"
    type = "mountain"

    def get_actions(self, user: str) -> List[Dict[str, str]]:
        return [
            {"name": "mine", "action": "/mine?amount=1"},
            {"name": "mine 10", "action": "/mine?amount=10"},
            {"name": "conquer", "action": f"/conquer?target={self.type}"},
        ]

class Rock(Scenery):
    biome = "rock"
    type = "rock"


def get_all_scenery_subclasses():
    all_subclasses = set()
    classes_to_check = list(Scenery.__subclasses__())

    while classes_to_check:
        subclass = classes_to_check.pop()
        if subclass not in all_subclasses:
            all_subclasses.add(subclass)
            classes_to_check.extend(subclass.__subclasses__())

    return all_subclasses


# The rest of the code remains the same
scenery_types = {}
for cls in get_all_scenery_subclasses():
    if hasattr(cls, 'type'):
        scenery_types[cls.type] = cls
    else:
        print(f"Warning: {cls.__name__} does not have a 'type' attribute.")

# Optionally, you can print out the collected scenery types for verification
print("Collected scenery types:")
for scenery_type, scenery_class in scenery_types.items():
    print(f"{scenery_type}: {scenery_class.__name__}")