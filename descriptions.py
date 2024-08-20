class Descriptions:
    def __init__(self):
        self.descriptions_dict = {
            "axe": "A tool to cut wood with in the forest and mine in a mountain.",
            "house": "Increases population limit by 10. Cost: 🪵50",
            "inn": "Allows user to rest and restore health. Cost: 🪵50",
            "farm": "Generates food and peasants if housing is available. Cost: 🪵50",
            "barracks": "Turns peasants into army for 2 food per turn and additional housing. Army is the only deployable unit. Cost: 🪵50",
            "sawmill": "Passively produces 🪵1 per turn per every sawmill level and forest. Cost: 🪵50",
            "mine": "Passively produces 🪨1 per turn per every mine level and forest. Cost: 🪵50",
            "archery_range": "Allows you to train army into archers. Cost: 🪵50",
            "laboratory": "Turns peasants into researchers to generate research points. Cost: 🪵50",
            "dagger": "Dagger is a weapon used in combat.",
            "sword": "A versatile melee weapon with balanced damage.",
            "bow": "A ranged weapon that allows attacking from a distance.",
            "spear": "A long melee weapon with good reach.",
            "mace": "A heavy melee weapon that deals high damage.",
            "helmet": "Protects your head from damage.",
            "chestplate": "Provides protection for your torso.",
            "leggings": "Armor for your legs, offering additional protection.",
            "boots": "Protects your feet and provides better mobility.",
        }

    def get(self, type):
        return self.descriptions_dict.get(type, "Description missing.")