class Descriptions:
    def get(self, type):
        if type == "axe":
            description = "A tool to cut wood with in the forest."
        elif type == "house":
            description = "Increases population limit. Cost: 🪵50"
        elif type == "inn":
            description = "Restores health"
        elif type == "farm":
            description = "Generates food and peasants if housing is available."
        elif type == "barracks":
            description = "Two turn peasants into soldiers for food and additional housing."
        elif type == "sawmill":
            description = "Collects wood on its own."
        elif type == "mine":
            description = "Generates additional resources."
        elif type == "archery_range":
            description = "Turns peasants into archers for additional wood and housing."
        else:
            description = "Description missing."

        return description
