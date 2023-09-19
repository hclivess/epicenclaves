class Descriptions:
    def __init__(self):
        self.descriptions_dict = {
            "axe": "A tool to cut wood with in the forest.",
            "house": "Increases population limit by 10. Cost: 🪵50",
            "inn": "Restores health",
            "farm": "Generates food and peasants if housing is available.",
            "barracks": "Turns peasants into soldiers for 2 food per turn and additional housing.",
            "sawmill": "Passively produces 🪵1 per turn per every level and forest.",
            "mine": "Passively produces 🪨1 per turn per every level and forest.",
            "archery_range": "Turns peasants into archers for additional wood and housing.",
            "laboratory": "Turns peasants into researchers to generate research points.",
        }

    def get(self, type):
        return self.descriptions_dict.get(type, "Description missing.")