class Descriptions:
    def __init__(self):
        self.descriptions_dict = {
            "axe": "A tool to cut wood with in the forest and mine in a mountain.",
            "house": "Increases population limit by 10. Cost: 🪵50",
            "inn": "Allows user to rest and restore health. Cost: 🪵50",
            "farm": "Generates food and peasants if housing is available. Cost: 🪵50",
            "barracks": "Turns peasants into soldiers for 2 food per turn and additional housing. Soldiers are the only deployable unit. Cost: 🪵50",
            "sawmill": "Passively produces 🪵1 per turn per every level and forest. Cost: 🪵50",
            "mine": "Passively produces 🪨1 per turn per every level and forest. Cost: 🪵50",
            "archery_range": "Allows you to train soldiers into archers. Cost: 🪵50",
            "laboratory": "Turns peasants into researchers to generate research points. Cost: 🪵50",
        }

    def get(self, type):
        return self.descriptions_dict.get(type, "Description missing.")