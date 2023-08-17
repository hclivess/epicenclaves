class Descriptions:
    def __init__(self):
        self.descriptions_dict = {
            "axe": "A tool to cut wood with in the forest.",
            "house": "Increases population limit. Cost: 🪵50",
            "inn": "Restores health",
            "farm": "Generates food and peasants if housing is available.",
            "barracks": "Turns peasants into soldiers for 2 food per turn and additional housing.",
            "sawmill": "Collects wood on its own.",
            "mine": "Generates additional resources.",
            "archery_range": "Turns peasants into archers for additional wood and housing."
        }

    def get(self, type):
        return self.descriptions_dict.get(type, "Description missing.")